"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Dict, List

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from tests.unit.dynamodb_tests.db_models.user_model import User


class DynamoDBModelUnitTest(unittest.TestCase):
    "Serialization Tests"

    def test_basic_serialization(self):
        """Test Basic Serialization"""
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
        """Test Basic Serialization"""
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
        """Test Basic Serialization"""
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
        index_name = "gsi2"
        gsi_key = user.get_key(index_name).key()

        expression = user.helpers.get_filter_expressions(gsi_key)
        print(f"expression: {expression}")
        keys: List[Dict] = expression.get("keys")
        key_0: Dict = keys[0].get("key")
        self.assertEqual(key_0.get("name"), "gsi2_pk")
        self.assertEqual(key_0.get("key"), "users#")

        key_1: Dict = keys[1].get("key")
        self.assertEqual(key_1.get("name"), "gsi2_sk")
        # we didn't populate a last name so this is correct (based on the current logic)
        # we stop here and don't go any further
        self.assertEqual(key_1.get("key"), "lastname#")

        index_name = "gsi3"
        gsi_key = user.get_key(index_name).key()
        # this should be mapped to gsi0
        self.assertEqual(index_name, "gsi3")

        expression = user.helpers.get_filter_expressions(gsi_key)
        print(f"expression: {expression}")
        keys: List[Dict] = expression.get("keys")
        key_0: Dict = keys[0].get("key")
        self.assertEqual(key_0.get("name"), "gsi3_pk")
        self.assertEqual(key_0.get("key"), "users#")

        key_1: Dict = keys[1].get("key")
        self.assertEqual(key_1.get("name"), "gsi3_sk")
        self.assertEqual(key_1.get("key"), "firstname#John#lastname#")

        resource = user.to_resource_dictionary()
        self.assertIsNotNone(resource)

    def test_key_list(self):
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

        self.assertEqual(keys[1].partition_key.attribute_name, "gsi1_pk")
        self.assertEqual(keys[1].partition_key.value, "users#")
        self.assertEqual(keys[1].sort_key.attribute_name, "gsi1_sk")
        self.assertEqual(keys[1].sort_key.value, "email#john@example.com")

        self.assertEqual(keys[2].partition_key.attribute_name, "gsi2_pk")
        self.assertEqual(keys[2].partition_key.value, "users#")
        self.assertEqual(keys[2].sort_key.attribute_name, "gsi2_sk")
        self.assertEqual(keys[2].sort_key.value, "lastname#")
        expression = user.helpers.get_filter_expressions(keys[2].key())
        print(f"expression: {expression}")

        self.assertEqual(keys[3].partition_key.attribute_name, "gsi3_pk")
        self.assertEqual(keys[3].partition_key.value, "users#")
        self.assertEqual(keys[3].sort_key.attribute_name, "gsi3_sk")
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

        self.assertEqual(dictionary.get("gsi1_pk"), "users#")
        self.assertEqual(dictionary.get("gsi1_sk"), "email#john@example.com")

        self.assertEqual(dictionary.get("gsi2_pk"), "users#")
        self.assertEqual(dictionary.get("gsi2_sk"), "lastname#Smith#firstname#John")

        self.assertEqual(dictionary.get("gsi3_pk"), "users#")
        self.assertEqual(dictionary.get("gsi3_sk"), "firstname#John#lastname#Smith")

        print("stop")

    def test_key_dictionary_key_gen(self):
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
        keys: List[DynamoDBKey] = user.list_keys()

        self.assertEqual(len(keys), 4)

        dictionary = user.helpers.keys_to_dictionary(keys=keys)

        self.assertEqual(dictionary.get("pk"), "user#123456")
        self.assertEqual(dictionary.get("sk"), "user#123456")

        self.assertEqual(dictionary.get("gsi1_pk"), "users#")
        self.assertEqual(dictionary.get("gsi1_sk"), "email#john@example.com")

        self.assertEqual(dictionary.get("gsi2_pk"), "users#")
        self.assertEqual(dictionary.get("gsi2_sk"), "lastname#")

        self.assertEqual(dictionary.get("gsi3_pk"), "users#")
        self.assertEqual(dictionary.get("gsi3_sk"), "firstname#John#lastname#")

        print("stop")
