"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Optional, List, Dict

from src.boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from src.boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class User(DynamoDBModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        DynamoDBModelBase.__init__(self)
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.age: Optional[int] = None
        self.email: Optional[str] = None

        self.__setup_indexes()

    def __setup_indexes(self):
        primary_key: DynamoDBIndex = DynamoDBIndex(
            index_name="primary_key",
            partition_key=DynamoDBKey(
                attribute_name="pk",
                value=lambda: DynamoDBKey.build_key((("user", self.id))),
            ),
            sort_key=DynamoDBKey(
                attribute_name="sk",
                value=lambda: DynamoDBKey.build_key(("user", self.id)),
            ),
        )
        self.indexes.add_primary(primary_key)

        gsi0: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi0",
            partition_key=DynamoDBKey(attribute_name="gsi0_pk", value="users#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi0_sk",
                value=lambda: DynamoDBKey.build_key(("email", self.email)),
            ),
        )
        self.indexes.add_secondary(gsi0)

        gsi1: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi1",
            partition_key=DynamoDBKey(attribute_name="gsi1_pk", value="users#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi1_sk",
                value=lambda: DynamoDBKey.build_key(
                    ("lastname", self.last_name), ("firstname", self.first_name)
                ),
            ),
        )
        self.indexes.add_secondary(gsi1)

        gsi2: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi2",
            partition_key=DynamoDBKey(attribute_name="gsi2_pk", value="users#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi2_sk",
                value=lambda: DynamoDBKey.build_key(
                    ("firstname", self.first_name), ("lastname", self.last_name)
                ),
            ),
        )

        self.indexes.add_secondary(gsi2)

        # self.key_configs = key_configs
        self.projection_expression = (
            "id,first_name,last_name,email,tenant_id,#type,#status,"
            "company_name,authorization,modified_datetime_utc"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type",
        }


class DynamoDBModelUnitTest(unittest.TestCase):
    "Serialization Tests"

    def test_basic_serialization(self):
        """Test Basic Serlization"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        serialized_data: User = User().map(data)

        # Assert

        self.assertEqual(serialized_data.first_name, "John")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")
        self.assertIsInstance(serialized_data, User)

        key = serialized_data.indexes.primary.key()
        self.assertIsInstance(key, dict)

    def test_object_serialization_map(self):
        """Test Basic Serlization"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        serialized_data: User = User().map(data)

        # Assert

        self.assertEqual(serialized_data.first_name, "John")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")

        self.assertIsInstance(serialized_data, User)

    def test_new_key_design_serialization_map(self):
        """Test Basic Serlization"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        user: User = User().map(data)

        # Assert

        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.age, 30)
        self.assertEqual(user.email, "john@example.com")

        self.assertIsInstance(user, User)

        pk = user.indexes.primary.partition_key.value
        self.assertEqual(pk, "user#123456")
        index_name = "gsi1"
        gsi_key = user.get_key(index_name).key()

        expression = user.helpers.get_filter_expressions(gsi_key)
        print(f"expression: {expression}")
        keys: List[Dict] = expression.get("keys")
        key_0: Dict = keys[0].get("key")
        self.assertEqual(key_0.get("name"), "gsi1_pk")
        self.assertEqual(key_0.get("key"), "users#")

        key_1: Dict = keys[1].get("key")
        self.assertEqual(key_1.get("name"), "gsi1_sk")
        # we didn't populate a last name so this is correct (based on the current logic)
        # we stop here and don't go any further
        self.assertEqual(key_1.get("key"), "lastname#")

        ### gsi3 mapped to a name of gsi2
        index_name = "gsi2"
        gsi_key = user.get_key(index_name).key()
        # this should be mapped to gsi0
        self.assertEqual(index_name, "gsi2")

        expression = user.helpers.get_filter_expressions(gsi_key)
        print(f"expression: {expression}")
        keys: List[Dict] = expression.get("keys")
        key_0: Dict = keys[0].get("key")
        self.assertEqual(key_0.get("name"), "gsi2_pk")
        self.assertEqual(key_0.get("key"), "users#")

        key_1: Dict = keys[1].get("key")
        self.assertEqual(key_1.get("name"), "gsi2_sk")
        self.assertEqual(key_1.get("key"), "firstname#John#lastname#")

        resource = user.to_resource_dictionary()
        self.assertIsNotNone(resource)

    def test_keylist(self):
        """Test Listing Keys"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        user: User = User().map(data)
        keys: List[DynamoDBIndex] = user.list_keys()
        print("")
        for key in keys:
            print(
                f"key: {key.partition_key.attribute_name} value: {key.partition_key.value}"
            )
            print(f"key: {key.sort_key.attribute_name} value: {key.sort_key.value}")

        self.assertEqual(len(keys), 4)

        self.assertEqual(keys[0].partition_key.attribute_name, "pk")
        self.assertEqual(keys[0].partition_key.value, "user#123456")
        self.assertEqual(keys[0].sort_key.attribute_name, "sk")
        self.assertEqual(keys[0].sort_key.value, "user#123456")

        self.assertEqual(keys[1].partition_key.attribute_name, "gsi0_pk")
        self.assertEqual(keys[1].partition_key.value, "users#")
        self.assertEqual(keys[1].sort_key.attribute_name, "gsi0_sk")
        self.assertEqual(keys[1].sort_key.value, "email#john@example.com")

        self.assertEqual(keys[2].partition_key.attribute_name, "gsi1_pk")
        self.assertEqual(keys[2].partition_key.value, "users#")
        self.assertEqual(keys[2].sort_key.attribute_name, "gsi1_sk")
        self.assertEqual(keys[2].sort_key.value, "lastname#")

        self.assertEqual(keys[3].partition_key.attribute_name, "gsi2_pk")
        self.assertEqual(keys[3].partition_key.value, "users#")
        self.assertEqual(keys[3].sort_key.attribute_name, "gsi2_sk")
        self.assertEqual(keys[3].sort_key.value, "firstname#John#lastname#")

        print("stop")

    def test_key_dictionary(self):
        """Test Listing Keys"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "last_name": "Smith",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        user: User = User().map(data)
        keys: List[DynamoDBKey] = user.list_keys()

        self.assertEqual(len(keys), 4)

        dictionary = user.helpers.keys_to_dictionary(keys=keys)

        self.assertEqual(dictionary.get("pk"), "user#123456")
        self.assertEqual(dictionary.get("sk"), "user#123456")

        self.assertEqual(dictionary.get("gsi0_pk"), "users#")
        self.assertEqual(dictionary.get("gsi0_sk"), "email#john@example.com")

        self.assertEqual(dictionary.get("gsi1_pk"), "users#")
        self.assertEqual(dictionary.get("gsi1_sk"), "lastname#Smith#firstname#John")

        self.assertEqual(dictionary.get("gsi2_pk"), "users#")
        self.assertEqual(dictionary.get("gsi2_sk"), "firstname#John#lastname#Smith")

        print("stop")
