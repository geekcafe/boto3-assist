"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
import json
from datetime import datetime, UTC
from datetime import timedelta
from typing import cast
from typing import Optional, List
from boto3_assist.utilities.serialization_utility import Serialization, JsonConversions
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


class JsonConversionsUnitTest(unittest.TestCase):
    """Unit tests for JsonConversions.string_to_json_obj function"""

    def setUp(self):
        """Set up common test data"""
        self.sample_dict = {"name": "John", "age": 30}
        self.sample_json = '{"name": "John", "age": 30}'

    def test_valid_json_conversions(self):
        """Test converting valid JSON strings and data types"""
        test_cases = [
            (
                '{"name": "John", "age": 30, "active": true}',
                {"name": "John", "age": 30, "active": True},
            ),
            (
                '[{"name": "John"}, {"name": "Jane"}]',
                [{"name": "John"}, {"name": "Jane"}],
            ),
            (
                '{"message": "Hello 🌍", "symbol": "©"}',
                {"message": "Hello 🌍", "symbol": "©"},
            ),
            (
                '{"name": "John", "middle_name": null}',
                {"name": "John", "middle_name": None},
            ),
        ]

        for json_input, expected in test_cases:
            with self.subTest(json_input=json_input):
                result = JsonConversions.string_to_json_obj(json_input)
                self.assertEqual(result, expected)

    def test_empty_and_none_inputs(self):
        """Test edge cases with empty/None inputs"""
        test_cases = [
            ("", {}),
            (None, {}),
        ]

        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = JsonConversions.string_to_json_obj(input_val)
                self.assertEqual(result, expected)

    def test_passthrough_types(self):
        """Test that certain types pass through unchanged"""
        input_dict = {"name": "John", "age": 30}
        result = JsonConversions.string_to_json_obj(input_dict)
        self.assertEqual(result, input_dict)
        self.assertIs(result, input_dict)

    def test_string_preprocessing(self):
        """Test string preprocessing (whitespace, quotes)"""
        test_cases = [
            ('\n  {"name": "John", "age": 30}  \n', self.sample_dict),
            ('\'{"name": "John", "age": 30}\'', self.sample_dict),
            ('"{\\"name\\": \\"John\\", \\"age\\": 30}"', self.sample_dict),
        ]

        for json_input, expected in test_cases:
            with self.subTest(json_input=json_input[:20] + "..."):
                result = JsonConversions.string_to_json_obj(json_input)
                self.assertEqual(result, expected)

    def test_malformed_json_auto_fix(self):
        """Test auto-fixing of malformed JSON"""
        bad_json = "{'name': 'John', 'age': 30}"
        result = JsonConversions.string_to_json_obj(bad_json)
        self.assertEqual(result, self.sample_dict)

    def test_error_handling_with_raise_on_error_true(self):
        """Test error handling when raise_on_error=True"""
        test_cases = [
            ("{'name': 'John', 'age': 30, 'invalid'}", json.JSONDecodeError),
            ('{"valid": "json"}', RuntimeError),  # retry=10 triggers RuntimeError
        ]

        for invalid_input, expected_exception in test_cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(expected_exception):
                    if expected_exception == RuntimeError:
                        JsonConversions.string_to_json_obj(invalid_input, retry=10)
                    else:
                        JsonConversions.string_to_json_obj(
                            invalid_input, raise_on_error=True
                        )

    def test_error_handling_with_raise_on_error_false(self):
        """Test graceful error handling when raise_on_error=False"""
        test_cases = [
            ("{'name': 'John', 'age': 30, 'invalid'}", {}),
            (12345, 12345),  # Non-string input
        ]

        for invalid_input, expected in test_cases:
            with self.subTest(invalid_input=invalid_input):
                result = JsonConversions.string_to_json_obj(
                    invalid_input, raise_on_error=False
                )
                self.assertEqual(result, expected)

    def test_retry_limit(self):
        """Test retry limit enforcement"""
        with self.assertRaises(RuntimeError) as context:
            JsonConversions.string_to_json_obj(self.sample_json, retry=6)
        self.assertIn("Too many attempts", str(context.exception))

    def test_complex_nested_structure(self):
        """Test complex nested JSON structure"""
        complex_json = """{
            "user": {"name": "John Doe", "details": {"age": 30, "preferences": ["reading", "coding"]}},
            "metadata": {"version": 1.2}
        }"""

        result = JsonConversions.string_to_json_obj(complex_json)

        # Verify key nested values
        self.assertEqual(result["user"]["name"], "John Doe")
        self.assertEqual(result["user"]["details"]["age"], 30)
        self.assertEqual(
            result["user"]["details"]["preferences"], ["reading", "coding"]
        )
        self.assertEqual(result["metadata"]["version"], 1.2)

    def test_data_type_preservation(self):
        """Test that JSON data types are properly preserved"""
        json_with_types = """{
            "string_val": "text", "int_val": 42, "float_val": 3.14,
            "bool_true": true, "bool_false": false, "null_val": null
        }"""

        result = JsonConversions.string_to_json_obj(json_with_types)

        # Verify all data types
        self.assertEqual(result["string_val"], "text")
        self.assertEqual(result["int_val"], 42)
        self.assertEqual(result["float_val"], 3.14)
        self.assertTrue(result["bool_true"])
        self.assertFalse(result["bool_false"])
        self.assertIsNone(result["null_val"])
