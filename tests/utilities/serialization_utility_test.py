"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import cast
from typing import Optional, List
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase


class UserAuthorizationModel:
    """Defines the Use Authorization Model"""

    def __init__(self):
        super().__init__()
        self.__groups: List[str] = []
        self.__policies: List[str] = []

    @property
    def groups(self) -> List[str]:
        """List of groups the user belongs to"""
        return self.__groups

    @groups.setter
    def groups(self, value: List[str] | str) -> None:
        if isinstance(value, str):
            value = value.split(",")
        self.__groups = value

    @property
    def policies(self) -> List[str]:
        """List of policies the user has"""
        return self.__policies

    @policies.setter
    def policies(self, value: List[str] | str) -> None:
        if isinstance(value, str):
            value = value.split(", ")
        self.__policies = value


class User:
    """User Model"""

    def __init__(
        self,
        name: Optional[str] = None,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ):
        self.name: Optional[str] = name
        self.age: Optional[int] = age
        self.email: Optional[str] = email
        self.authorization: UserAuthorizationModel = UserAuthorizationModel()

        # self.authorization.groups = "Admin, Manager"


class UserDbModel(User, DynamoDbModelBase):
    """User Model"""

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
        data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "authorization": {"groups": "Admin, Manager"},
        }

        # Act
        serialized_data: User = Serialization.map(data, User)

        # Assert

        self.assertEqual(serialized_data.name, "John Doe")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")
        self.assertIsInstance(serialized_data, User)
        t = type(serialized_data)
        print(t)
        user: User = cast(User, serialized_data)
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.age, 30)
        self.assertEqual(user.email, "john@example.com")

        self.assertEqual(user.authorization.groups[0], "Admin")

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
