"""
Unit tests for DynamoDBModelBase.save_partial() method

Uses moto for in-memory DynamoDB testing instead of magic mocks.
This provides real DynamoDB-like behavior for comprehensive testing.
"""

import unittest

import boto3
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class UserModel(DynamoDBModelBase):
    """User model for save_partial tests"""

    def __init__(self):
        super().__init__(self)
        self.pk = None
        self.sk = None
        self.id = None
        self.name = None
        self.email = None
        self.status = None
        self.age = None
        self.active = None
        self.temp_field = None


def create_test_table(dynamodb_resource, table_name):
    """Create a test DynamoDB table"""
    return dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@mock_aws
class TestSavePartialBasic(unittest.TestCase):
    """Tests for basic save_partial() functionality"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_calls_update_item_partial(self):
        """Test that save_partial() calls update_item_partial()"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.email = "john@example.com"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with save_partial
        user.name = "Jane"
        response = user.save_partial(table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

        # Verify the update in DynamoDB
        retrieved = self.db.get(key={"pk": user.pk, "sk": user.sk}, table_name=self.table_name)
        self.assertEqual(retrieved["Item"]["name"], "Jane")

    def test_save_partial_parameters_are_passed_through(self):
        """Test that parameters are passed through correctly"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.temp_field = "temp_value"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with save_partial and clear temp_field
        user.name = "Jane"
        user.temp_field = None  # Clear the field value before calling save_partial
        response = user.save_partial(
            table_name=self.table_name,
            fields_to_clear={"temp_field"},
            return_values="ALL_NEW",
        )

        # Verify response contains attributes
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")

        # Verify temp_field was cleared
        retrieved = self.db.get(key={"pk": user.pk, "sk": user.sk}, table_name=self.table_name)
        self.assertNotIn("temp_field", retrieved["Item"])

    def test_save_partial_response_is_returned(self):
        """Test that response is returned correctly"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with save_partial
        user.name = "Jane"
        response = user.save_partial(table_name=self.table_name, return_values="ALL_NEW")

        # Verify response structure
        self.assertIsNotNone(response)
        self.assertIn("Attributes", response)


@mock_aws
class TestSavePartialWithMerge(unittest.TestCase):
    """Tests for save_partial() integration with merge() pattern"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_works_after_merge(self):
        """Test that save_partial() works after merge()"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "Jane"
        user.email = "jane@example.com"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Merge updates
        updates = {"name": "John", "status": "active"}
        user.merge(updates)

        # Save partial
        response = user.save_partial(table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

        # Verify the updates in DynamoDB
        retrieved = self.db.get(key={"pk": user.pk, "sk": user.sk}, table_name=self.table_name)
        self.assertEqual(retrieved["Item"]["name"], "John")
        self.assertEqual(retrieved["Item"]["status"], "active")

    def test_model_instance_is_not_modified(self):
        """Test that model instance is not modified by save_partial()"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "Jane"
        user.email = "jane@example.com"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        original_name = user.name
        original_email = user.email

        # Save partial
        user.save_partial(table_name=self.table_name)

        # Verify model instance is unchanged
        self.assertEqual(user.name, original_name)
        self.assertEqual(user.email, original_email)


@mock_aws
class TestSavePartialWithMap(unittest.TestCase):
    """Tests for save_partial() integration with map() pattern"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_works_after_map(self):
        """Test that save_partial() works after map()"""
        user = UserModel()
        db_response = {
            "pk": "user#user-123",
            "sk": "user#user-123",
            "id": "user-123",
            "name": "Jane",
            "email": "jane@example.com",
        }
        user.map(db_response)

        user.name = "John"

        response = user.save_partial(table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

    def test_loaded_item_can_be_partially_updated(self):
        """Test that loaded item can be partially updated"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "Jane"
        user.email = "jane@example.com"
        user.age = 30

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update only name
        user.name = "John"
        response = user.save_partial(table_name=self.table_name, return_values="ALL_NEW")

        # Verify only name was updated
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "John")
        self.assertEqual(response["Attributes"]["age"], 30)  # Age should remain unchanged


@mock_aws
class TestSavePartialWithFieldsToClean(unittest.TestCase):
    """Tests for save_partial() with fields_to_clear parameter"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_with_fields_to_clear(self):
        """Test save_partial() with fields_to_clear parameter"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.temp_field = "temp_value"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Clear temp_field
        user.temp_field = None  # Clear the field value before calling save_partial
        response = user.save_partial(
            table_name=self.table_name,
            fields_to_clear={"temp_field"},
            return_values="ALL_NEW",
        )

        # Verify temp_field was cleared
        self.assertNotIn("temp_field", response["Attributes"])


@mock_aws
class TestSavePartialWithConditionalWrite(unittest.TestCase):
    """Tests for save_partial() with conditional writes"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_with_condition_expression(self):
        """Test save_partial() with condition_expression"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with condition that should succeed
        user.name = "Jane"
        response = user.save_partial(
            table_name=self.table_name,
            condition_expression="attribute_exists(pk)",
        )

        # Verify update was successful
        self.assertIsNotNone(response)


@mock_aws
class TestSavePartialWithReturnValues(unittest.TestCase):
    """Tests for save_partial() with return_values parameter"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_with_return_values_all_new(self):
        """Test save_partial() with return_values='ALL_NEW'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with return_values
        user.name = "Jane"
        result = user.save_partial(
            table_name=self.table_name,
            return_values="ALL_NEW",
        )

        # Verify response contains all attributes
        self.assertIn("Attributes", result)
        self.assertEqual(result["Attributes"]["name"], "Jane")

    def test_save_partial_with_return_values_updated_new(self):
        """Test save_partial() with return_values='UPDATED_NEW'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with return_values
        user.name = "Jane"
        result = user.save_partial(
            table_name=self.table_name,
            return_values="UPDATED_NEW",
        )

        # Verify response contains updated attributes
        self.assertIn("Attributes", result)

    def test_save_partial_with_return_values_all_old(self):
        """Test save_partial() with return_values='ALL_OLD'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with return_values
        user.name = "Jane"
        result = user.save_partial(
            table_name=self.table_name,
            return_values="ALL_OLD",
        )

        # Verify response contains old attributes
        self.assertIn("Attributes", result)
        self.assertEqual(result["Attributes"]["name"], "John")

    def test_save_partial_with_return_values_updated_old(self):
        """Test save_partial() with return_values='UPDATED_OLD'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with return_values
        user.name = "Jane"
        result = user.save_partial(
            table_name=self.table_name,
            return_values="UPDATED_OLD",
        )

        # Verify response contains updated old attributes
        self.assertIn("Attributes", result)


@mock_aws
class TestSavePartialEdgeCases(unittest.TestCase):
    """Tests for edge cases in save_partial()"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_save_partial_with_empty_string_value(self):
        """Test save_partial() with empty string value"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = ""

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with empty string
        response = user.save_partial(table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

    def test_save_partial_with_zero_value(self):
        """Test save_partial() with zero value"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.age = 0

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with zero value
        response = user.save_partial(table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

    def test_save_partial_with_false_value(self):
        """Test save_partial() with False value"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.active = False

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with False value
        response = user.save_partial(table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

    def test_save_partial_with_multiple_fields(self):
        """Test save_partial() with multiple fields"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.email = "john@example.com"
        user.age = 30
        user.status = "active"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update multiple fields
        user.name = "Jane"
        user.email = "jane@example.com"
        user.age = 31
        response = user.save_partial(table_name=self.table_name, return_values="ALL_NEW")

        # Verify all updates were successful
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["email"], "jane@example.com")
        self.assertEqual(response["Attributes"]["age"], 31)


if __name__ == "__main__":
    unittest.main()
