"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest


from tests.dynamodb.models.user_model import User


class DynamoDBModelSerializationUnitTest(unittest.TestCase):
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
