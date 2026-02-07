"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for DynamoDB conditional expressions and optimistic locking
"""

import unittest

import boto3
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService


@mock_aws
class TestConditionalExpressions(unittest.TestCase):
    """Tests for conditional expression support in save() method"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_conditional_table"

        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

    def test_save_with_fail_if_exists(self):
        """Test save with fail_if_exists prevents duplicates"""
        item = {"pk": "user#001", "sk": "user#001", "id": "001", "name": "Alice"}

        # First save should succeed
        response = self.db.save(item=item, table_name=self.table_name, fail_if_exists=True)
        self.assertIn("ResponseMetadata", response)

        # Second save should fail
        with self.assertRaises(RuntimeError) as context:
            self.db.save(item=item, table_name=self.table_name, fail_if_exists=True)

        self.assertIn("already exists", str(context.exception))

    def test_save_with_custom_condition(self):
        """Test save with custom condition expression"""
        # Create item with initial version
        item = {
            "pk": "doc#001",
            "sk": "doc#001",
            "id": "001",
            "content": "Initial content",
            "version": 1,
        }
        self.db.save(item=item, table_name=self.table_name)

        # Update with matching version (should succeed)
        updated_item = {
            "pk": "doc#001",
            "sk": "doc#001",
            "id": "001",
            "content": "Updated content",
            "version": 2,
        }

        response = self.db.save(
            item=updated_item,
            table_name=self.table_name,
            condition_expression="#version = :expected_version",
            expression_attribute_names={"#version": "version"},
            expression_attribute_values={":expected_version": 1},
        )
        self.assertIn("ResponseMetadata", response)

        # Verify update succeeded
        result = self.db.get(key={"pk": "doc#001", "sk": "doc#001"}, table_name=self.table_name)
        self.assertEqual(result["Item"]["version"], 2)
        self.assertEqual(result["Item"]["content"], "Updated content")

    def test_save_with_version_mismatch(self):
        """Test save fails when version doesn't match"""
        # Create item with version 1
        item = {"pk": "doc#002", "sk": "doc#002", "id": "002", "content": "Initial", "version": 1}
        self.db.save(item=item, table_name=self.table_name)

        # Try to update with wrong version (should fail)
        updated_item = {
            "pk": "doc#002",
            "sk": "doc#002",
            "id": "002",
            "content": "Updated",
            "version": 2,
        }

        with self.assertRaises(RuntimeError) as context:
            self.db.save(
                item=updated_item,
                table_name=self.table_name,
                condition_expression="#version = :expected_version",
                expression_attribute_names={"#version": "version"},
                expression_attribute_values={":expected_version": 999},  # Wrong version!
            )

        self.assertIn("Conditional check failed", str(context.exception))

        # Verify item unchanged
        result = self.db.get(key={"pk": "doc#002", "sk": "doc#002"}, table_name=self.table_name)
        self.assertEqual(result["Item"]["version"], 1)
        self.assertEqual(result["Item"]["content"], "Initial")

    def test_save_with_attribute_exists_condition(self):
        """Test save only if attribute exists"""
        # Create item
        item = {"pk": "user#003", "sk": "user#003", "id": "003", "name": "Bob", "status": "active"}
        self.db.save(item=item, table_name=self.table_name)

        # Update only if status exists (should succeed)
        updated_item = {
            "pk": "user#003",
            "sk": "user#003",
            "id": "003",
            "name": "Bob Updated",
            "status": "active",
        }

        response = self.db.save(
            item=updated_item,
            table_name=self.table_name,
            condition_expression="attribute_exists(#status)",
            expression_attribute_names={"#status": "status"},
        )
        self.assertIn("ResponseMetadata", response)

    def test_save_with_attribute_not_exists_condition(self):
        """Test save only if attribute doesn't exist"""
        # Try to save new item only if it doesn't exist
        item = {"pk": "user#004", "sk": "user#004", "id": "004", "name": "Charlie"}

        # First save should succeed
        response = self.db.save(
            item=item,
            table_name=self.table_name,
            condition_expression="attribute_not_exists(pk)",
        )
        self.assertIn("ResponseMetadata", response)

        # Second save should fail
        with self.assertRaises(RuntimeError):
            self.db.save(
                item=item,
                table_name=self.table_name,
                condition_expression="attribute_not_exists(pk)",
            )

    def test_save_with_comparison_condition(self):
        """Test save with value comparison"""
        # Create account with balance
        item = {"pk": "account#001", "sk": "account#001", "id": "001", "balance": 100}
        self.db.save(item=item, table_name=self.table_name)

        # Update only if balance >= 50 (should succeed)
        updated_item = {"pk": "account#001", "sk": "account#001", "id": "001", "balance": 50}

        response = self.db.save(
            item=updated_item,
            table_name=self.table_name,
            condition_expression="balance >= :min_balance",
            expression_attribute_values={":min_balance": 50},
        )
        self.assertIn("ResponseMetadata", response)

        # Try to update with insufficient balance (should fail)
        updated_item["balance"] = 25

        with self.assertRaises(RuntimeError):
            self.db.save(
                item=updated_item,
                table_name=self.table_name,
                condition_expression="balance >= :min_balance",
                expression_attribute_values={":min_balance": 100},  # Current balance is 50
            )

    def test_save_with_complex_condition(self):
        """Test save with AND/OR conditions"""
        # Create item
        item = {"pk": "item#001", "sk": "item#001", "id": "001", "status": "active", "version": 1}
        self.db.save(item=item, table_name=self.table_name)

        # Update only if status=active AND version=1
        updated_item = {
            "pk": "item#001",
            "sk": "item#001",
            "id": "001",
            "status": "inactive",
            "version": 2,
        }

        response = self.db.save(
            item=updated_item,
            table_name=self.table_name,
            condition_expression="#status = :active AND #version = :v1",
            expression_attribute_names={"#status": "status", "#version": "version"},
            expression_attribute_values={":active": "active", ":v1": 1},
        )
        self.assertIn("ResponseMetadata", response)


@mock_aws
class TestOptimisticLocking(unittest.TestCase):
    """Tests for optimistic locking patterns"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_optimistic_lock_table"

        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

    def test_optimistic_lock_success(self):
        """Test successful optimistic lock update"""
        # Create document with version 1
        doc = {
            "pk": "doc#lock-001",
            "sk": "doc#lock-001",
            "id": "lock-001",
            "content": "Version 1",
            "version": 1,
        }
        self.db.save(item=doc, table_name=self.table_name)

        # Read current version
        response = self.db.get(
            key={"pk": "doc#lock-001", "sk": "doc#lock-001"}, table_name=self.table_name
        )
        current_version = response["Item"]["version"]

        # Update with version check
        updated_doc = {
            "pk": "doc#lock-001",
            "sk": "doc#lock-001",
            "id": "lock-001",
            "content": "Version 2",
            "version": current_version + 1,
        }

        response = self.db.save(
            item=updated_doc,
            table_name=self.table_name,
            condition_expression="#version = :expected_version",
            expression_attribute_names={"#version": "version"},
            expression_attribute_values={":expected_version": current_version},
        )

        self.assertIn("ResponseMetadata", response)

        # Verify update
        result = self.db.get(
            key={"pk": "doc#lock-001", "sk": "doc#lock-001"}, table_name=self.table_name
        )
        self.assertEqual(result["Item"]["version"], 2)
        self.assertEqual(result["Item"]["content"], "Version 2")

    def test_optimistic_lock_conflict(self):
        """Test optimistic lock detects conflicts"""
        # Create document
        doc = {
            "pk": "doc#lock-002",
            "sk": "doc#lock-002",
            "id": "lock-002",
            "content": "Original",
            "version": 1,
        }
        self.db.save(item=doc, table_name=self.table_name)

        # User A reads document
        response_a = self.db.get(
            key={"pk": "doc#lock-002", "sk": "doc#lock-002"}, table_name=self.table_name
        )
        version_a = response_a["Item"]["version"]

        # User B reads document
        response_b = self.db.get(
            key={"pk": "doc#lock-002", "sk": "doc#lock-002"}, table_name=self.table_name
        )
        version_b = response_b["Item"]["version"]

        # User A updates successfully
        doc_a = {
            "pk": "doc#lock-002",
            "sk": "doc#lock-002",
            "id": "lock-002",
            "content": "Updated by A",
            "version": version_a + 1,
        }
        self.db.save(
            item=doc_a,
            table_name=self.table_name,
            condition_expression="#version = :expected_version",
            expression_attribute_names={"#version": "version"},
            expression_attribute_values={":expected_version": version_a},
        )

        # User B tries to update (should fail - version conflict)
        doc_b = {
            "pk": "doc#lock-002",
            "sk": "doc#lock-002",
            "id": "lock-002",
            "content": "Updated by B",
            "version": version_b + 1,
        }

        with self.assertRaises(RuntimeError) as context:
            self.db.save(
                item=doc_b,
                table_name=self.table_name,
                condition_expression="#version = :expected_version",
                expression_attribute_names={"#version": "version"},
                expression_attribute_values={":expected_version": version_b},
            )

        self.assertIn("Conditional check failed", str(context.exception))

        # Verify only A's update succeeded
        result = self.db.get(
            key={"pk": "doc#lock-002", "sk": "doc#lock-002"}, table_name=self.table_name
        )
        self.assertEqual(result["Item"]["content"], "Updated by A")


def main():
    unittest.main()


if __name__ == "__main__":
    main()
