"""
Unit tests for DynamoDB.update_item_partial() method

Uses moto for in-memory DynamoDB testing instead of magic mocks.
This provides real DynamoDB-like behavior for comprehensive testing.
"""

import unittest

import boto3
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class UserModel(DynamoDBModelBase):
    """User model for update_item_partial tests"""

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
class TestUpdateItemPartialBasic(unittest.TestCase):
    """Tests for basic update_item_partial() functionality"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_update_item_partial_with_model(self):
        """Test that update_item_partial() works with a model instance"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.email = "john@example.com"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update via update_item_partial
        user.name = "Jane"
        response = self.db.update_item_partial(item=user, table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

        # Verify the update in DynamoDB
        retrieved = self.db.get(key={"pk": user.pk, "sk": user.sk}, table_name=self.table_name)
        self.assertEqual(retrieved["Item"]["name"], "Jane")

    def test_update_item_partial_parameters_are_passed_through(self):
        """Test that parameters are passed through correctly"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.temp_field = "temp_value"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update and clear temp_field
        user.name = "Jane"
        user.temp_field = None
        response = self.db.update_item_partial(
            item=user,
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

    def test_update_item_partial_response_is_returned(self):
        """Test that response is returned correctly"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update via update_item_partial
        user.name = "Jane"
        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify response structure
        self.assertIsNotNone(response)
        self.assertIn("Attributes", response)


@mock_aws
class TestUpdateItemPartialWithMerge(unittest.TestCase):
    """Tests for update_item_partial() integration with merge() pattern"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_update_item_partial_works_after_merge(self):
        """Test that update_item_partial() works after merge()"""
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

        # Update via db service
        response = self.db.update_item_partial(item=user, table_name=self.table_name)

        # Verify update was successful
        self.assertIsNotNone(response)

        # Verify the updates in DynamoDB
        retrieved = self.db.get(key={"pk": user.pk, "sk": user.sk}, table_name=self.table_name)
        self.assertEqual(retrieved["Item"]["name"], "John")
        self.assertEqual(retrieved["Item"]["status"], "active")

    def test_model_instance_is_not_modified(self):
        """Test that model instance is not modified by update_item_partial()"""
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

        # Update via db service
        self.db.update_item_partial(item=user, table_name=self.table_name)

        # Verify model instance is unchanged
        self.assertEqual(user.name, original_name)
        self.assertEqual(user.email, original_email)


@mock_aws
class TestUpdateItemPartialWithMap(unittest.TestCase):
    """Tests for update_item_partial() integration with map() pattern"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_update_item_partial_works_after_map(self):
        """Test that update_item_partial() works after map()"""
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

        response = self.db.update_item_partial(item=user, table_name=self.table_name)

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
        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify only name was updated
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "John")
        self.assertEqual(response["Attributes"]["age"], 30)  # Age should remain unchanged


@mock_aws
class TestUpdateItemPartialWithFieldsToClear(unittest.TestCase):
    """Tests for update_item_partial() with fields_to_clear parameter"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_update_item_partial_with_fields_to_clear(self):
        """Test update_item_partial() with fields_to_clear parameter"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.temp_field = "temp_value"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Clear temp_field
        user.temp_field = None
        response = self.db.update_item_partial(
            item=user,
            table_name=self.table_name,
            fields_to_clear={"temp_field"},
            return_values="ALL_NEW",
        )

        # Verify temp_field was cleared
        self.assertNotIn("temp_field", response["Attributes"])


@mock_aws
class TestUpdateItemPartialWithConditionalWrite(unittest.TestCase):
    """Tests for update_item_partial() with conditional writes"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_update_item_partial_with_condition_expression(self):
        """Test update_item_partial() with condition_expression"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        # Save initial item
        self.db.save(item=user, table_name=self.table_name)

        # Update with condition that should succeed
        user.name = "Jane"
        response = self.db.update_item_partial(
            item=user,
            table_name=self.table_name,
            condition_expression="attribute_exists(pk)",
        )

        # Verify update was successful
        self.assertIsNotNone(response)


@mock_aws
class TestUpdateItemPartialWithReturnValues(unittest.TestCase):
    """Tests for update_item_partial() with return_values parameter"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_return_values_all_new(self):
        """Test update_item_partial() with return_values='ALL_NEW'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        self.db.save(item=user, table_name=self.table_name)

        user.name = "Jane"
        result = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertIn("Attributes", result)
        self.assertEqual(result["Attributes"]["name"], "Jane")

    def test_return_values_updated_new(self):
        """Test update_item_partial() with return_values='UPDATED_NEW'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        self.db.save(item=user, table_name=self.table_name)

        user.name = "Jane"
        result = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="UPDATED_NEW"
        )

        self.assertIn("Attributes", result)

    def test_return_values_all_old(self):
        """Test update_item_partial() with return_values='ALL_OLD'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        self.db.save(item=user, table_name=self.table_name)

        user.name = "Jane"
        result = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_OLD"
        )

        self.assertIn("Attributes", result)
        self.assertEqual(result["Attributes"]["name"], "John")

    def test_return_values_updated_old(self):
        """Test update_item_partial() with return_values='UPDATED_OLD'"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"

        self.db.save(item=user, table_name=self.table_name)

        user.name = "Jane"
        result = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="UPDATED_OLD"
        )

        self.assertIn("Attributes", result)


@mock_aws
class TestUpdateItemPartialEdgeCases(unittest.TestCase):
    """Tests for edge cases in update_item_partial()"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_empty_string_value(self):
        """Test update_item_partial() with empty string value"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = ""

        self.db.save(item=user, table_name=self.table_name)
        response = self.db.update_item_partial(item=user, table_name=self.table_name)
        self.assertIsNotNone(response)

    def test_zero_value(self):
        """Test update_item_partial() with zero value"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.age = 0

        self.db.save(item=user, table_name=self.table_name)
        response = self.db.update_item_partial(item=user, table_name=self.table_name)
        self.assertIsNotNone(response)

    def test_false_value(self):
        """Test update_item_partial() with False value"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.active = False

        self.db.save(item=user, table_name=self.table_name)
        response = self.db.update_item_partial(item=user, table_name=self.table_name)
        self.assertIsNotNone(response)

    def test_multiple_fields(self):
        """Test update_item_partial() with multiple fields"""
        user = UserModel()
        user.pk = "user#user-123"
        user.sk = "user#user-123"
        user.id = "user-123"
        user.name = "John"
        user.email = "john@example.com"
        user.age = 30
        user.status = "active"

        self.db.save(item=user, table_name=self.table_name)

        user.name = "Jane"
        user.email = "jane@example.com"
        user.age = 31
        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["email"], "jane@example.com")
        self.assertEqual(response["Attributes"]["age"], 31)


# ============================================================================
# Empty Collection Filtering Tests
# ============================================================================


class UserModelWithCollections(DynamoDBModelBase):
    """User model with collection fields for testing empty collection filtering"""

    def __init__(self):
        super().__init__(self)
        self.pk = None
        self.sk = None
        self.name = None
        self.email = None
        self.tags = []
        self.metadata = {}
        self.items = []


@mock_aws
class TestUpdateItemPartialEmptyCollections(unittest.TestCase):
    """Tests for empty collection filtering in update_item_partial"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_empty_list_excluded_by_default(self):
        """
        Test that empty lists in the model are NOT sent to DynamoDB,
        preventing accidental overwrite of populated arrays.
        """
        # First, save an item with a populated tags array
        initial_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "tags": ["admin", "active"],
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        # Now create a model with empty tags (default) and update only name
        user = UserModelWithCollections()
        user.pk = "user-123"
        user.sk = "user-123"
        user.name = "Jane"
        # user.tags is [] by default - should NOT overwrite the existing tags

        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify tags were NOT overwritten with empty list
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["tags"], ["admin", "active"])

    def test_empty_dict_excluded_by_default(self):
        """
        Test that empty dicts in the model are NOT sent to DynamoDB,
        preventing accidental overwrite of populated maps.
        """
        # First, save an item with a populated metadata map
        initial_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "metadata": {"role": "admin", "level": 5},
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        # Now create a model with empty metadata (default) and update only name
        user = UserModelWithCollections()
        user.pk = "user-123"
        user.sk = "user-123"
        user.name = "Jane"

        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify metadata was NOT overwritten with empty dict
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["metadata"], {"role": "admin", "level": 5})

    def test_populated_list_is_included(self):
        """
        Test that non-empty lists ARE included in the update.
        """
        initial_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "tags": ["old-tag"],
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        user = UserModelWithCollections()
        user.pk = "user-123"
        user.sk = "user-123"
        user.name = "Jane"
        user.tags = ["new-tag-1", "new-tag-2"]

        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["tags"], ["new-tag-1", "new-tag-2"])

    def test_exclude_empty_collections_false_allows_overwrite(self):
        """
        Test that setting exclude_empty_collections=False allows empty
        collections to overwrite existing data.
        """
        initial_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "tags": ["admin", "active"],
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        user = UserModelWithCollections()
        user.pk = "user-123"
        user.sk = "user-123"
        user.name = "Jane"
        user.tags = []  # Intentionally clearing the tags

        response = self.db.update_item_partial(
            item=user,
            table_name=self.table_name,
            return_values="ALL_NEW",
            exclude_empty_collections=False,
        )

        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["tags"], [])

    def test_dict_input_empty_list_excluded(self):
        """
        Test that empty lists in dict input are also excluded by default.
        """
        initial_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "items": ["item-1", "item-2"],
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        update_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "Jane",
            "items": [],
        }

        response = self.db.update_item_partial(
            item=update_item, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["items"], ["item-1", "item-2"])

    def test_multiple_empty_collections_all_excluded(self):
        """
        Test that multiple empty collections are all excluded.
        """
        initial_item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "tags": ["admin"],
            "metadata": {"role": "admin"},
            "items": ["item-1"],
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        user = UserModelWithCollections()
        user.pk = "user-123"
        user.sk = "user-123"
        user.name = "Jane"

        response = self.db.update_item_partial(
            item=user, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Jane")
        self.assertEqual(response["Attributes"]["tags"], ["admin"])
        self.assertEqual(response["Attributes"]["metadata"], {"role": "admin"})
        self.assertEqual(response["Attributes"]["items"], ["item-1"])

    def test_only_empty_collections_raises_value_error(self):
        """
        Test that if the only non-key fields are empty collections,
        a ValueError is raised (no fields to update).
        """
        user = UserModelWithCollections()
        user.pk = "user-123"
        user.sk = "user-123"

        self.db.save(
            item={"pk": "user-123", "sk": "user-123", "name": "John"},
            table_name=self.table_name,
        )

        with self.assertRaises(ValueError) as ctx:
            self.db.update_item_partial(item=user, table_name=self.table_name)

        self.assertIn("No fields to update or clear", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
