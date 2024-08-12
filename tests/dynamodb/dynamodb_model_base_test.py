"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Optional, List, Dict

from src.boto3_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDbIndex
from src.boto3_assist.dynamodb.dynamodb_key import DynamoDbKey


class User(DynamoDbModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        DynamoDbModelBase.__init__(self)
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.age: Optional[int] = None
        self.email: Optional[str] = None

        self.__setup_indexes()

    def __setup_indexes(self):
        primary_key: DynamoDbIndex = DynamoDbIndex(
            index_name="primary_key",
            partition_key=DynamoDbKey(
                attribute_name="pk", value=lambda: f"user#{self.id if self.id else ''}"
            ),
            sort_key=DynamoDbKey(
                attribute_name="sk", value=lambda: f"user#{self.id if self.id else ''}"
            ),
        )
        self.indexes.add_primary(primary_key)

        gsi0: DynamoDbIndex = DynamoDbIndex(
            index_name="gsi0",
            partition_key=DynamoDbKey(attribute_name="gsi0_pk", value="users#"),
            sort_key=DynamoDbKey(
                attribute_name="gsi0_sk",
                value=lambda: f"email#{self.email if self.email else ''}",
            ),
        )
        self.indexes.add_secondary(gsi0)

        gsi1: DynamoDbIndex = DynamoDbIndex(
            index_name="gsi1",
            partition_key=DynamoDbKey(attribute_name="gsi1_pk", value="users#"),
            sort_key=DynamoDbKey(
                attribute_name="gsi1_sk",
                value=lambda: (
                    f"lastname#{self.last_name if self.last_name else ''}"
                    + (f"#firstname#{self.first_name}" if self.first_name else "")
                ),
            ),
        )
        self.indexes.add_secondary(gsi1)

        gsi2: DynamoDbIndex = DynamoDbIndex(
            index_name="gsi2",
            partition_key=DynamoDbKey(attribute_name="gsi2_pk", value="users#"),
            sort_key=DynamoDbKey(
                attribute_name="gsi2_sk",
                value=self.__get_gsi2,
            ),
        )

        self.indexes.add_secondary(gsi2)

        # key_configs = [
        #     {
        #         "primary_key": {
        #             "pk": {
        #                 "attribute": "pk",
        #                 "value": lambda: f"user#{self.id if self.id else ''}",
        #             },
        #             "sk": {
        #                 "attribute": "sk",
        #                 "value": lambda: f"user#{self.id if self.id else ''}",
        #             },
        #         }
        #     },
        #     {
        #         "gsi0": {
        #             "pk": {
        #                 "attribute": "gsi0_pk",
        #                 "value": "users#",
        #             },
        #             "sk": {
        #                 "attribute": "gsi0_sk",
        #                 "value": lambda: f"email#{self.email if self.email else ''}",
        #             },
        #         }
        #     },
        #     {
        #         "gsi1": {
        #             "pk": {"attribute": "gsi1_pk", "value": "users#"},
        #             "sk": {
        #                 "attribute": "gsi1_sk",
        #                 "value": lambda: (
        #                     f"lastname#{self.last_name if self.last_name else ''}"
        #                     + (
        #                         f"#firstname#{self.first_name}"
        #                         if self.first_name
        #                         else ""
        #                     )
        #                 ),
        #             },
        #         }
        #     },
        #     {
        #         "gsi2": {
        #             "pk": {
        #                 "attribute": "gsi2_pk",
        #                 "value": "users#",
        #             },
        #             "sk": {
        #                 "attribute": "gsi2_sk",
        #                 "value": self.__get_gsi2,
        #                 "results": {
        #                     "firstname#{self.first_name}": "with no last name",
        #                     "firstname#{self.first_name}#lastname#{self.lastname}": "with a last name",
        #                 },
        #             },
        #         }
        #     },
        # ]

        # self.key_configs = key_configs
        self.projection_expression = (
            "id,first_name,last_name,email,tenant_id,#type,#status,"
            "company_name,authorization,modified_datetime_utc"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type",
        }

    def __get_gsi2(self) -> str:
        index = f"firstname#{self.first_name if self.first_name else ''}"
        if self.last_name:
            index = f"{index}#lastname#{self.last_name}"

        return index


class DynamoDbModelUnitTest(unittest.TestCase):
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
        self.assertEqual(key_1.get("key"), "lastname##firstname#John")

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
        self.assertEqual(key_1.get("key"), "firstname#John")

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
        keys: List[DynamoDbIndex] = user.list_keys()
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
        self.assertEqual(keys[2].sort_key.value, "lastname##firstname#John")

        self.assertEqual(keys[3].partition_key.attribute_name, "gsi2_pk")
        self.assertEqual(keys[3].partition_key.value, "users#")
        self.assertEqual(keys[3].sort_key.attribute_name, "gsi2_sk")
        self.assertEqual(keys[3].sort_key.value, "firstname#John")

        print("stop")

    def test_key_dictionary(self):
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
        keys: List[DynamoDbKey] = user.list_keys()

        self.assertEqual(len(keys), 4)

        dictionary = user.helpers.keys_to_dictionary(keys=keys)

        self.assertEqual(dictionary.get("pk"), "user#123456")
        self.assertEqual(dictionary.get("sk"), "user#123456")

        self.assertEqual(dictionary.get("gsi0_pk"), "users#")
        self.assertEqual(dictionary.get("gsi0_sk"), "email#john@example.com")

        self.assertEqual(dictionary.get("gsi1_pk"), "users#")
        self.assertEqual(dictionary.get("gsi1_sk"), "lastname##firstname#John")

        self.assertEqual(dictionary.get("gsi2_pk"), "users#")
        self.assertEqual(dictionary.get("gsi2_sk"), "firstname#John")

        print("stop")
