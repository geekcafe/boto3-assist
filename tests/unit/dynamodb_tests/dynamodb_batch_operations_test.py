"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for DynamoDB batch operations (batch_get_item, batch_write_item)
"""

import unittest

import boto3
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService


@mock_aws
class TestBatchGetItem(unittest.TestCase):
    """Tests for batch_get_item method"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_batch_table"

        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

        # Create test data
        self._create_test_data()

    def _create_test_data(self):
        """Create 10 test users"""
        for i in range(10):
            user_id = f"user-{str(i).zfill(3)}"
            item = {
                "pk": f"user#{user_id}",
                "sk": f"user#{user_id}",
                "id": user_id,
                "name": f"User {i}",
                "age": 20 + i,
                "email": f"user{i}@example.com",
            }
            self.db.save(item=item, table_name=self.table_name)

    def test_batch_get_small_batch(self):
        """Test batch get with less than 100 items"""
        keys = [
            {"pk": "user#user-000", "sk": "user#user-000"},
            {"pk": "user#user-001", "sk": "user#user-001"},
            {"pk": "user#user-002", "sk": "user#user-002"},
        ]

        response = self.db.batch_get_item(keys=keys, table_name=self.table_name)

        self.assertIn("Items", response)
        self.assertEqual(len(response["Items"]), 3)
        self.assertEqual(response["Count"], 3)

        # Verify correct items returned
        ids = [item["id"] for item in response["Items"]]
        self.assertIn("user-000", ids)
        self.assertIn("user-001", ids)
        self.assertIn("user-002", ids)

    def test_batch_get_all_users(self):
        """Test batch get retrieving all 10 users"""
        keys = [
            {"pk": f"user#user-{str(i).zfill(3)}", "sk": f"user#user-{str(i).zfill(3)}"}
            for i in range(10)
        ]

        response = self.db.batch_get_item(keys=keys, table_name=self.table_name)

        self.assertEqual(len(response["Items"]), 10)
        self.assertEqual(response["Count"], 10)

    def test_batch_get_with_projection(self):
        """Test batch get with projection expression"""
        keys = [
            {"pk": "user#user-000", "sk": "user#user-000"},
            {"pk": "user#user-001", "sk": "user#user-001"},
        ]

        response = self.db.batch_get_item(
            keys=keys,
            table_name=self.table_name,
            projection_expression="id,#name,email",
            expression_attribute_names={"#name": "name"},
        )

        self.assertEqual(len(response["Items"]), 2)

        # Verify only projected attributes returned
        for item in response["Items"]:
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("email", item)
            # pk, sk, age should NOT be present
            self.assertNotIn("pk", item)
            self.assertNotIn("sk", item)
            self.assertNotIn("age", item)

    def test_batch_get_nonexistent_keys(self):
        """Test batch get with some nonexistent keys"""
        keys = [
            {"pk": "user#user-000", "sk": "user#user-000"},  # Exists
            {"pk": "user#user-999", "sk": "user#user-999"},  # Doesn't exist
            {"pk": "user#user-001", "sk": "user#user-001"},  # Exists
        ]

        response = self.db.batch_get_item(keys=keys, table_name=self.table_name)

        # Should only return 2 items (the ones that exist)
        self.assertEqual(len(response["Items"]), 2)

    def test_batch_get_empty_keys(self):
        """Test batch get with empty keys list"""
        response = self.db.batch_get_item(keys=[], table_name=self.table_name)

        self.assertEqual(len(response["Items"]), 0)
        self.assertEqual(response["Count"], 0)

    def test_batch_get_decimal_conversion(self):
        """Test that numbers are converted from Decimal to int/float"""
        # Create item with numeric fields
        item = {
            "pk": "test#decimal",
            "sk": "test#decimal",
            "id": "test-decimal",
            "count": 42,
            "price": 19.99,
        }
        self.db.save(item=item, table_name=self.table_name)

        # Retrieve with batch get
        keys = [{"pk": "test#decimal", "sk": "test#decimal"}]
        response = self.db.batch_get_item(keys=keys, table_name=self.table_name)

        item = response["Items"][0]

        # Verify types are native Python types, not Decimal
        self.assertIsInstance(item["count"], int)
        self.assertIsInstance(item["price"], float)
        self.assertEqual(item["count"], 42)
        self.assertEqual(item["price"], 19.99)


@mock_aws
class TestBatchWriteItem(unittest.TestCase):
    """Tests for batch_write_item method"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_batch_write_table"

        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

    def test_batch_write_put_small_batch(self):
        """Test batch write with less than 25 items (put operation)"""
        items = [
            {"pk": f"user#user-{i}", "sk": f"user#user-{i}", "id": f"user-{i}", "name": f"User {i}"}
            for i in range(5)
        ]

        response = self.db.batch_write_item(
            items=items, table_name=self.table_name, operation="put"
        )

        self.assertEqual(response["ProcessedCount"], 5)
        self.assertEqual(response["UnprocessedCount"], 0)

        # Verify items were created
        for i in range(5):
            result = self.db.get(
                key={"pk": f"user#user-{i}", "sk": f"user#user-{i}"}, table_name=self.table_name
            )
            self.assertIn("Item", result)
            self.assertEqual(result["Item"]["name"], f"User {i}")

    def test_batch_write_put_large_batch(self):
        """Test batch write with more than 25 items (auto-chunking)"""
        items = [
            {"pk": f"user#user-{i}", "sk": f"user#user-{i}", "id": f"user-{i}", "name": f"User {i}"}
            for i in range(50)  # 50 items = 2 batches
        ]

        response = self.db.batch_write_item(
            items=items, table_name=self.table_name, operation="put"
        )

        self.assertEqual(response["ProcessedCount"], 50)
        self.assertEqual(response["UnprocessedCount"], 0)

        # Spot check a few items
        for i in [0, 25, 49]:
            result = self.db.get(
                key={"pk": f"user#user-{i}", "sk": f"user#user-{i}"}, table_name=self.table_name
            )
            self.assertIn("Item", result)

    def test_batch_write_delete(self):
        """Test batch write with delete operation"""
        # First create some items
        for i in range(5):
            item = {
                "pk": f"user#user-{i}",
                "sk": f"user#user-{i}",
                "id": f"user-{i}",
                "name": f"User {i}",
            }
            self.db.save(item=item, table_name=self.table_name)

        # Verify they exist
        for i in range(5):
            result = self.db.get(
                key={"pk": f"user#user-{i}", "sk": f"user#user-{i}"}, table_name=self.table_name
            )
            self.assertIn("Item", result)

        # Now delete them with batch write
        keys = [{"pk": f"user#user-{i}", "sk": f"user#user-{i}"} for i in range(5)]

        response = self.db.batch_write_item(
            items=keys, table_name=self.table_name, operation="delete"
        )

        self.assertEqual(response["ProcessedCount"], 5)
        self.assertEqual(response["UnprocessedCount"], 0)

        # Verify they're deleted
        for i in range(5):
            result = self.db.get(
                key={"pk": f"user#user-{i}", "sk": f"user#user-{i}"}, table_name=self.table_name
            )
            self.assertNotIn("Item", result)

    def test_batch_write_invalid_operation(self):
        """Test batch write with invalid operation type"""
        items = [{"pk": "test", "sk": "test"}]

        with self.assertRaises(ValueError) as context:
            self.db.batch_write_item(items=items, table_name=self.table_name, operation="invalid")

        self.assertIn("Invalid operation", str(context.exception))

    def test_batch_write_mixed_operations(self):
        """Test creating and then deleting items in separate batch operations"""
        # Create 10 items
        create_items = [
            {"pk": f"user#user-{i}", "sk": f"user#user-{i}", "id": f"user-{i}", "name": f"User {i}"}
            for i in range(10)
        ]

        create_response = self.db.batch_write_item(
            items=create_items, table_name=self.table_name, operation="put"
        )

        self.assertEqual(create_response["ProcessedCount"], 10)

        # Delete first 5 items
        delete_keys = [{"pk": f"user#user-{i}", "sk": f"user#user-{i}"} for i in range(5)]

        delete_response = self.db.batch_write_item(
            items=delete_keys, table_name=self.table_name, operation="delete"
        )

        self.assertEqual(delete_response["ProcessedCount"], 5)

        # Verify first 5 are deleted
        for i in range(5):
            result = self.db.get(
                key={"pk": f"user#user-{i}", "sk": f"user#user-{i}"}, table_name=self.table_name
            )
            self.assertNotIn("Item", result)

        # Verify last 5 still exist
        for i in range(5, 10):
            result = self.db.get(
                key={"pk": f"user#user-{i}", "sk": f"user#user-{i}"}, table_name=self.table_name
            )
            self.assertIn("Item", result)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
