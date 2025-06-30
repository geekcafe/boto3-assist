"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest


from tests.unit.dynamodb_tests.db_models.user_model import User
from tests.unit.dynamodb_tests.db_models.user_required_fields_model import User as User2


class Dynamodb_Model_SerializationUnitTest(unittest.TestCase):
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

        dictionary = serialized_data.to_resource_dictionary()
        self.assertIsInstance(dictionary, dict)
        keys = dictionary.keys()
        self.assertIn("first_name", keys)
        self.assertIn("age", keys)
        self.assertIn("email", keys)
        self.assertIn("id", keys)
        self.assertNotIn("T", keys)

        user: User = User()
        dictionary = user.to_resource_dictionary()
        self.assertIsInstance(dictionary, dict)

    def test_required_fields(self):
        """Test Required Fields"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        serialized_data: User2 = User2().map(data)

        # Assert
        self.assertEqual(serialized_data.first_name, "John")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")
        self.assertIsInstance(serialized_data, User2)

        key = serialized_data.indexes.primary.key()
        self.assertIsInstance(key, dict)

        dictionary = serialized_data.to_resource_dictionary()
        self.assertIsInstance(dictionary, dict)
        keys = dictionary.keys()
        self.assertIn("first_name", keys)
        self.assertIn("age", keys)
        self.assertIn("email", keys)
        self.assertIn("id", keys)
        self.assertNotIn("T", keys)

        user: User = User()
        dictionary = user.to_resource_dictionary()
        self.assertIsInstance(dictionary, dict)
