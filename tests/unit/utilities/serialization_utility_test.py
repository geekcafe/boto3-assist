"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from datetime import datetime, UTC
from datetime import timedelta
from typing import cast
from typing import Optional, List
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_model_base import (
    DynamoDBModelBase,
    exclude_indexes_from_serialization,
)
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class UserAuthorizationModel(DynamoDBModelBase):
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


class User(DynamoDBModelBase):
    """User Model"""

    def __init__(
        self,
        name: Optional[str] = None,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ):
        DynamoDBModelBase.__init__(self)
        self.id: Optional[str] = None
        self.name: Optional[str] = name
        self.age: Optional[int] = age
        self.email: Optional[str] = email
        self.authorization: UserAuthorizationModel = UserAuthorizationModel()

        self.__setup_indexes()

    def __setup_indexes(self):
        self.indexes.add_primary(
            DynamoDBIndex(
                index_name="primary",
                partition_key=DynamoDBKey(
                    attribute_name="pk",
                    value=lambda: f"user#{self.id if self.id else ''}",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="sk",
                    value=lambda: f"user#{self.id if self.id else ''}",
                ),
            )
        )

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value="users#",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: f"email#{self.email if self.email else ''}",
                ),
            )
        )


class Subscription(DynamoDBModelBase):
    """Subscription Model"""

    def __init__(self):
        super().__init__()
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.start_utc: Optional[datetime] = None
        self.end_utc: Optional[datetime] = None
        self.__setup_indexes()

    def __setup_indexes(self):
        self.indexes.add_primary(
            DynamoDBIndex(
                index_name="primary",
                partition_key=DynamoDBKey(
                    attribute_name="pk",
                    value=lambda: f"subscription#{self.id}",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="sk",
                    value=lambda: f"subscription#{self.id}",
                ),
            )
        )

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value="subscriptions#",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: f"subscription#{self.id}",
                ),
            )
        )


class Tenant(DynamoDBModelBase):
    """Tenant Model"""

    def __init__(self):
        super().__init__()
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.__active_subscription: Optional[Subscription] = Subscription()
        self.__setup_indexes()

    @property
    @exclude_indexes_from_serialization
    def active_subscription(self) -> Subscription:
        """Active Subscription"""
        return self.__active_subscription

    @active_subscription.setter
    def active_subscription(self, value: Subscription) -> None:
        self.__active_subscription = value

    def __setup_indexes(self):
        self.indexes.add_primary(
            DynamoDBIndex(
                index_name="primary",
                partition_key=DynamoDBKey(
                    attribute_name="pk",
                    value=lambda: f"tenant#{self.id}",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="sk",
                    value=lambda: f"tenant#{self.id}",
                ),
            )
        )

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value="tenants#",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: f"tenant#{self.id}",
                ),
            )
        )


class SerializationUnitTest(unittest.TestCase):
    "Serialization Tests"

    def test_basic_serialization(self):
        """Test Basic Serialization"""
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
        """Test Basic Serialization"""
        # Arrange
        data = {"name": "John Doe", "age": 30, "email": "john@example.com"}

        # Act
        serialized_data: User = User().map(data)

        # Assert

        self.assertEqual(serialized_data.name, "John Doe")
        self.assertEqual(serialized_data.age, 30)
        self.assertEqual(serialized_data.email, "john@example.com")

    def test_object_serialization_map_resource(self):
        """Ensure the db properties aren't carried over to sub objects during Serialization"""
        # Arrange
        subscription: Subscription = Subscription()

        subscription.id = "123"
        subscription.name = "Monthly"
        subscription.start_utc = datetime.now(tz=UTC)
        subscription.end_utc = subscription.start_utc + timedelta(days=30)

        tenant: Tenant = Tenant()
        tenant.id = "456"
        tenant.name = "Acme Corp"
        tenant.active_subscription = subscription
        # Act

        # Assert

        resource: dict = tenant.to_resource_dictionary()

        self.assertEqual(resource.get("pk"), "tenant#456")
        self.assertEqual(resource.get("sk"), "tenant#456")

        self.assertEqual(resource.get("gsi0_pk"), "tenants#")
        self.assertEqual(resource.get("gsi0_sk"), "tenant#456")

        active_subscription: dict = resource.get("active_subscription")

        self.assertIsNone(active_subscription.get("pk"))
        self.assertIsNone(active_subscription.get("sk"))
        self.assertIsNone(active_subscription.get("gsi0_pk"))
        self.assertIsNone(active_subscription.get("gsi0_sk"))
