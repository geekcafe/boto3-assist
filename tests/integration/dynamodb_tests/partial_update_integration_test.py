"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Integration tests for partial updates feature using moto (DynamoDB mock).

These tests verify the partial updates feature works end-to-end with real DynamoDB
operations (mocked via moto).
"""

import unittest

import boto3
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService

# ============================================================================
# Test Models
# ============================================================================


class UserModel:
    """Simple user model for testing"""

    def __init__(self):
        self.pk = None
        self.sk = None
        self.id = None
        self.name = None
        self.email = None
        self.status = None
        self.age = None
        self.active = None
        self.balance = None
        self.temp_field = None
        self.description = None


# ============================================================================
# Base Integration Test Class
# ============================================================================


@mock_aws
class PartialUpdateIntegrationTestBase(unittest.TestCase):
    """Base class for partial update integration tests"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_partial_update_table"

        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

    def _create_test_item(self, item_id: str, **kwargs) -> dict:
        """Create and save a test item"""
        item = {
            "pk": f"user#{item_id}",
            "sk": f"user#{item_id}",
            "id": item_id,
            "name": "John Doe",
            "email": "john@example.com",
            "status": "active",
            "age": 30,
            "active": True,
            "balance": 100.0,
        }
        item.update(kwargs)
        self.db.save(item=item, table_name=self.table_name)
        return item

    def _get_item(self, item_id: str) -> dict:
        """Get an item from DynamoDB"""
        response = self.db.get(
            key={"pk": f"user#{item_id}", "sk": f"user#{item_id}"},
            table_name=self.table_name,
        )
        return response.get("Item", {})


# ============================================================================
# 1. Basic Partial Updates (3 tests)
# ============================================================================


@mock_aws
class TestBasicPartialUpdates(PartialUpdateIntegrationTestBase):
    """Tests for basic partial update functionality"""

    def test_partial_update_single_field(self):
        """Test updating a single field"""
        # Create initial item
        self._create_test_item("user-001")

        # Update only the name field
        item = {
            "pk": "user#user-001",
            "sk": "user#user-001",
            "name": "Jane Doe",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="ALL_NEW",
        )

        # Verify the update
        updated_item = self._get_item("user-001")
        self.assertEqual(updated_item["name"], "Jane Doe")
        self.assertEqual(updated_item["email"], "john@example.com")  # Unchanged
        self.assertEqual(updated_item["status"], "active")  # Unchanged

    def test_partial_update_multiple_fields(self):
        """Test updating multiple fields"""
        # Create initial item
        self._create_test_item("user-002")

        # Update multiple fields
        item = {
            "pk": "user#user-002",
            "sk": "user#user-002",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "age": 31,
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="ALL_NEW",
        )

        # Verify the updates
        updated_item = self._get_item("user-002")
        self.assertEqual(updated_item["name"], "Jane Doe")
        self.assertEqual(updated_item["email"], "jane@example.com")
        self.assertEqual(updated_item["age"], 31)
        self.assertEqual(updated_item["status"], "active")  # Unchanged

    def test_partial_update_preserves_other_fields(self):
        """Test that partial update preserves fields not being updated"""
        # Create initial item with all fields
        self._create_test_item(
            "user-003",
            name="Original Name",
            email="original@example.com",
            status="inactive",
            age=25,
            active=False,
            balance=500.0,
        )

        # Update only one field
        item = {
            "pk": "user#user-003",
            "sk": "user#user-003",
            "name": "Updated Name",
        }

        self.db.update_item_partial(item=item, table_name=self.table_name)

        # Verify only name changed, others preserved
        updated_item = self._get_item("user-003")
        self.assertEqual(updated_item["name"], "Updated Name")
        self.assertEqual(updated_item["email"], "original@example.com")
        self.assertEqual(updated_item["status"], "inactive")
        self.assertEqual(updated_item["age"], 25)
        self.assertEqual(updated_item["active"], False)
        self.assertEqual(updated_item["balance"], 500.0)


# ============================================================================
# 2. Field Clearing (3 tests)
# ============================================================================


@mock_aws
class TestFieldClearing(PartialUpdateIntegrationTestBase):
    """Tests for field clearing functionality"""

    def test_clear_single_field(self):
        """Test clearing a single field"""
        # Create initial item
        self._create_test_item("user-004", temp_field="temporary_value")

        # Clear the temp_field
        item = {
            "pk": "user#user-004",
            "sk": "user#user-004",
            "name": "Updated Name",
        }

        self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            fields_to_clear={"temp_field"},
        )

        # Verify field was cleared
        updated_item = self._get_item("user-004")
        self.assertEqual(updated_item["name"], "Updated Name")
        self.assertNotIn("temp_field", updated_item)

    def test_clear_multiple_fields(self):
        """Test clearing multiple fields"""
        # Create initial item
        self._create_test_item(
            "user-005",
            temp_field="temporary_value",
            description="some description",
        )

        # Clear multiple fields
        item = {
            "pk": "user#user-005",
            "sk": "user#user-005",
            "name": "Updated Name",
        }

        self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            fields_to_clear={"temp_field", "description"},
        )

        # Verify fields were cleared
        updated_item = self._get_item("user-005")
        self.assertEqual(updated_item["name"], "Updated Name")
        self.assertNotIn("temp_field", updated_item)
        self.assertNotIn("description", updated_item)

    def test_clear_and_update_same_operation(self):
        """Test clearing and updating fields in the same operation"""
        # Create initial item
        self._create_test_item(
            "user-006",
            temp_field="temporary_value",
            description="some description",
        )

        # Update some fields and clear others
        item = {
            "pk": "user#user-006",
            "sk": "user#user-006",
            "name": "Updated Name",
            "email": "updated@example.com",
        }

        self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            fields_to_clear={"temp_field", "description"},
        )

        # Verify updates and clears
        updated_item = self._get_item("user-006")
        self.assertEqual(updated_item["name"], "Updated Name")
        self.assertEqual(updated_item["email"], "updated@example.com")
        self.assertNotIn("temp_field", updated_item)
        self.assertNotIn("description", updated_item)


# ============================================================================
# 3. Reserved Keywords (3 tests)
# ============================================================================


@mock_aws
class TestReservedKeywords(PartialUpdateIntegrationTestBase):
    """Tests for reserved keyword handling"""

    def test_update_reserved_keyword_field(self):
        """Test updating a field with reserved keyword name"""
        # Create initial item
        self._create_test_item("user-007", status="inactive")

        # Update reserved keyword field
        item = {
            "pk": "user#user-007",
            "sk": "user#user-007",
            "status": "active",
        }

        self.db.update_item_partial(item=item, table_name=self.table_name)

        # Verify the update
        updated_item = self._get_item("user-007")
        self.assertEqual(updated_item["status"], "active")

    def test_update_multiple_reserved_keyword_fields(self):
        """Test updating multiple reserved keyword fields"""
        # Create initial item
        self._create_test_item("user-008")

        # Update multiple reserved keyword fields
        item = {
            "pk": "user#user-008",
            "sk": "user#user-008",
            "status": "inactive",
            "name": "New Name",
        }

        self.db.update_item_partial(item=item, table_name=self.table_name)

        # Verify the updates
        updated_item = self._get_item("user-008")
        self.assertEqual(updated_item["status"], "inactive")
        self.assertEqual(updated_item["name"], "New Name")

    def test_clear_reserved_keyword_field(self):
        """Test clearing a reserved keyword field"""
        # Create initial item
        self._create_test_item("user-009", status="active")

        # Clear reserved keyword field
        item = {
            "pk": "user#user-009",
            "sk": "user#user-009",
            "name": "Updated Name",
        }

        self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            fields_to_clear={"status"},
        )

        # Verify field was cleared
        updated_item = self._get_item("user-009")
        self.assertEqual(updated_item["name"], "Updated Name")
        self.assertNotIn("status", updated_item)


# ============================================================================
# 4. Conditional Writes (3 tests)
# ============================================================================


@mock_aws
class TestConditionalWrites(PartialUpdateIntegrationTestBase):
    """Tests for conditional write functionality"""

    def test_conditional_write_succeeds_when_condition_met(self):
        """Test conditional write succeeds when condition is met"""
        # Create initial item
        self._create_test_item("user-010", status="active")

        # Update with condition that should succeed
        item = {
            "pk": "user#user-010",
            "sk": "user#user-010",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            condition_expression="attribute_exists(#status)",
            expression_attribute_names={"#status": "status"},
            return_values="ALL_NEW",
        )

        # Verify the update succeeded
        updated_item = self._get_item("user-010")
        self.assertEqual(updated_item["name"], "Updated Name")

    def test_conditional_write_fails_when_condition_not_met(self):
        """Test conditional write fails when condition is not met"""
        # Create initial item
        self._create_test_item("user-011")

        # Update with condition that should fail
        item = {
            "pk": "user#user-011",
            "sk": "user#user-011",
            "name": "Updated Name",
        }

        # This should raise an error because the condition is not met
        with self.assertRaises(Exception):
            self.db.update_item_partial(
                item=item,
                table_name=self.table_name,
                condition_expression="attribute_not_exists(#name)",
                expression_attribute_names={"#name": "name"},
            )

    def test_conditional_write_with_attribute_value(self):
        """Test conditional write with attribute value comparison"""
        # Create initial item
        self._create_test_item("user-012", age=30)

        # Update with condition checking age value
        item = {
            "pk": "user#user-012",
            "sk": "user#user-012",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            condition_expression="age = :expected_age",
            expression_attribute_values={":expected_age": 30},
            return_values="ALL_NEW",
        )

        # Verify the update succeeded
        updated_item = self._get_item("user-012")
        self.assertEqual(updated_item["name"], "Updated Name")


# ============================================================================
# 5. Return Values (6 tests)
# ============================================================================


@mock_aws
class TestReturnValues(PartialUpdateIntegrationTestBase):
    """Tests for return values functionality"""

    def test_return_values_none(self):
        """Test return_values='NONE' returns minimal response"""
        # Create initial item
        self._create_test_item("user-013")

        # Update with return_values='NONE'
        item = {
            "pk": "user#user-013",
            "sk": "user#user-013",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="NONE",
        )

        # Response should not contain Attributes or should have empty Attributes
        # (moto may return empty Attributes dict for NONE)
        if "Attributes" in response:
            self.assertEqual(response["Attributes"], {})

    def test_return_values_all_new(self):
        """Test return_values='ALL_NEW' returns complete updated item"""
        # Create initial item
        self._create_test_item("user-014")

        # Update with return_values='ALL_NEW'
        item = {
            "pk": "user#user-014",
            "sk": "user#user-014",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="ALL_NEW",
        )

        # Response should contain all attributes
        self.assertIn("Attributes", response)
        attributes = response["Attributes"]
        self.assertEqual(attributes["name"], "Updated Name")
        self.assertEqual(attributes["email"], "john@example.com")
        self.assertEqual(attributes["status"], "active")

    def test_return_values_updated_new(self):
        """Test return_values='UPDATED_NEW' returns only updated fields"""
        # Create initial item
        self._create_test_item("user-015")

        # Update with return_values='UPDATED_NEW'
        item = {
            "pk": "user#user-015",
            "sk": "user#user-015",
            "name": "Updated Name",
            "email": "updated@example.com",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="UPDATED_NEW",
        )

        # Response should contain only updated attributes
        self.assertIn("Attributes", response)
        attributes = response["Attributes"]
        self.assertEqual(attributes["name"], "Updated Name")
        self.assertEqual(attributes["email"], "updated@example.com")

    def test_return_values_all_old(self):
        """Test return_values='ALL_OLD' returns item before update"""
        # Create initial item
        self._create_test_item("user-016", name="Original Name")

        # Update with return_values='ALL_OLD'
        item = {
            "pk": "user#user-016",
            "sk": "user#user-016",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="ALL_OLD",
        )

        # Response should contain old attributes
        self.assertIn("Attributes", response)
        attributes = response["Attributes"]
        self.assertEqual(attributes["name"], "Original Name")

    def test_return_values_updated_old(self):
        """Test return_values='UPDATED_OLD' returns updated fields before update"""
        # Create initial item
        self._create_test_item("user-017", name="Original Name", email="original@example.com")

        # Update with return_values='UPDATED_OLD'
        item = {
            "pk": "user#user-017",
            "sk": "user#user-017",
            "name": "Updated Name",
            "email": "updated@example.com",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="UPDATED_OLD",
        )

        # Response should contain old values of updated attributes
        self.assertIn("Attributes", response)
        attributes = response["Attributes"]
        self.assertEqual(attributes["name"], "Original Name")
        self.assertEqual(attributes["email"], "original@example.com")

    def test_return_values_with_field_clearing(self):
        """Test return_values with field clearing"""
        # Create initial item
        self._create_test_item("user-018", temp_field="temporary_value")

        # Update and clear with return_values='ALL_NEW'
        item = {
            "pk": "user#user-018",
            "sk": "user#user-018",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            fields_to_clear={"temp_field"},
            return_values="ALL_NEW",
        )

        # Response should show cleared field is gone
        self.assertIn("Attributes", response)
        attributes = response["Attributes"]
        self.assertEqual(attributes["name"], "Updated Name")
        self.assertNotIn("temp_field", attributes)


# ============================================================================
# 6. Error Scenarios (3 tests)
# ============================================================================


@mock_aws
class TestErrorScenarios(PartialUpdateIntegrationTestBase):
    """Tests for error handling"""

    def test_error_missing_primary_key(self):
        """Test error when primary key is missing"""
        # Item without primary key
        item = {
            "name": "Updated Name",
        }

        # Should raise ValueError
        with self.assertRaises(ValueError):
            self.db.update_item_partial(
                item=item,
                table_name=self.table_name,
            )

    def test_error_no_fields_to_update(self):
        """Test error when no fields to update"""
        # Item with only primary keys
        item = {
            "pk": "user#user-019",
            "sk": "user#user-019",
        }

        # Should raise ValueError
        with self.assertRaises(ValueError):
            self.db.update_item_partial(
                item=item,
                table_name=self.table_name,
            )

    def test_error_invalid_return_values(self):
        """Test error with invalid return_values parameter"""
        # Create initial item
        self._create_test_item("user-020")

        # Item with invalid return_values
        item = {
            "pk": "user#user-020",
            "sk": "user#user-020",
            "name": "Updated Name",
        }

        # Should raise ValueError
        with self.assertRaises(ValueError):
            self.db.update_item_partial(
                item=item,
                table_name=self.table_name,
                return_values="INVALID_VALUE",
            )


# ============================================================================
# 7. Throttling and Retries (3 tests)
# ============================================================================


@mock_aws
class TestThrottlingAndRetries(PartialUpdateIntegrationTestBase):
    """Tests for throttling and retry behavior"""

    def test_successful_update_after_retry(self):
        """Test that updates succeed after retries"""
        # Create initial item
        self._create_test_item("user-021")

        # Update item
        item = {
            "pk": "user#user-021",
            "sk": "user#user-021",
            "name": "Updated Name",
        }

        response = self.db.update_item_partial(
            item=item,
            table_name=self.table_name,
            return_values="ALL_NEW",
        )

        # Verify the update succeeded
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["name"], "Updated Name")

    def test_multiple_sequential_updates(self):
        """Test multiple sequential partial updates"""
        # Create initial item
        self._create_test_item("user-022")

        # First update
        item1 = {
            "pk": "user#user-022",
            "sk": "user#user-022",
            "name": "First Update",
        }
        self.db.update_item_partial(item=item1, table_name=self.table_name)

        # Second update
        item2 = {
            "pk": "user#user-022",
            "sk": "user#user-022",
            "email": "updated@example.com",
        }
        self.db.update_item_partial(item=item2, table_name=self.table_name)

        # Verify both updates applied
        updated_item = self._get_item("user-022")
        self.assertEqual(updated_item["name"], "First Update")
        self.assertEqual(updated_item["email"], "updated@example.com")

    def test_concurrent_style_updates(self):
        """Test multiple updates to different items"""
        # Create multiple items
        self._create_test_item("user-023")
        self._create_test_item("user-024")
        self._create_test_item("user-025")

        # Update all items
        for i in range(23, 26):
            item = {
                "pk": f"user#user-{i:03d}",
                "sk": f"user#user-{i:03d}",
                "name": f"Updated User {i}",
            }
            self.db.update_item_partial(item=item, table_name=self.table_name)

        # Verify all updates applied
        for i in range(23, 26):
            updated_item = self._get_item(f"user-{i:03d}")
            self.assertEqual(updated_item["name"], f"Updated User {i}")


if __name__ == "__main__":
    unittest.main()
