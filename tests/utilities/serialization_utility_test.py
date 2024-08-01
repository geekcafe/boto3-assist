# create unittest

import unittest
from typing import Optional
from boto_assist.utilities.serialization_utility import Serialization
from boto_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase


class User:
    def __init__(
        self,
        name: Optional[str] = None,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ):
        self.name: Optional[str] = name
        self.age: Optional[int] = age
        self.email: Optional[str] = email


class UserDbModel(User, DynamoDbModelBase):
    def __init__(
        self,
        name: Optional[str] = None,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ):
        User.__init__(self, name, age, email)
        DynamoDbModelBase.__init__(self)


class SerializationUnitTest(unittest.TestCase):
    "Serialization Tests"

    def test_basic_serialization(self):
        """Test Basic Serlization"""
        # Arrange
        data = {"name": "John Doe", "age": 30, "email": "john@example.com"}

        # Act
        serialized_data: User = Serialization.map(data, User)

        # Assert

        self.assertEqual(serialized_data.name, "John Doe")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")

    def test_object_serialization_map(self):
        """Test Basic Serlization"""
        # Arrange
        data = {"name": "John Doe", "age": 30, "email": "john@example.com"}

        # Act
        serialized_data: UserDbModel = UserDbModel().map(data)

        # Assert

        self.assertEqual(serialized_data.name, "John Doe")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")
