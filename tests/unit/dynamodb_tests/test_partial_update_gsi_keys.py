"""
Unit tests for GSI key recomputation in DynamoDB.update_item_partial()

Verifies that when a model instance is provided to update_item_partial(),
GSI key attributes are recomputed via prep_for_save() and included in the
update expression so that GSI indexes stay in sync with field changes.

Uses moto for in-memory DynamoDB testing.
"""

import unittest
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase

# ---------------------------------------------------------------------------
# Test model with GSI keys that embed field values
# ---------------------------------------------------------------------------


class TaskModel(DynamoDBModelBase):
    """
    Test model with a GSI partition key that embeds the 'status' field.

    GSI1 pk = "task#<tenant_id>#status#<status>"
    GSI1 sk = "task#<task_id>"

    This means changing 'status' should recompute gsi1_pk.
    """

    def __init__(self):
        super().__init__()
        self.id: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.title: Optional[str] = None
        self.description: Optional[str] = None
        self.status: Optional[str] = None
        self.priority: Optional[int] = None
        self._setup_indexes()

    def _setup_indexes(self):
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("task", self.tenant_id), ("id", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("task", self.id))
        self.indexes.add_primary(primary)

        gsi1 = DynamoDBIndex(index_name="gsi1")
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(
            ("task", self.tenant_id), ("status", self.status)
        )
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(("task", self.id))
        self.indexes.add_secondary(gsi1)

    def prep_for_save(self):
        """Recompute GSI keys (mimics BaseModel.prep_for_save behavior)."""
        # In real models, this also sets timestamps and validates.
        # For testing, we just need the index lambdas to be re-evaluated
        # which happens automatically in to_resource_dictionary(include_indexes=True).
        pass


def create_test_table_with_gsi(dynamodb_resource, table_name):
    """Create a test DynamoDB table with a GSI."""
    return dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "gsi1_pk", "AttributeType": "S"},
            {"AttributeName": "gsi1_sk", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "gsi1",
                "KeySchema": [
                    {"AttributeName": "gsi1_pk", "KeyType": "HASH"},
                    {"AttributeName": "gsi1_sk", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )


# ===========================================================================
# Test 1: GSI key recomputation on partial update
# ===========================================================================


@mock_aws
class TestGSIKeyRecomputationOnPartialUpdate(unittest.TestCase):
    """Verify GSI key attributes are recomputed when a model field changes."""

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "tasks"
        create_test_table_with_gsi(self.db.dynamodb_resource, self.table_name)

    def test_gsi_key_updated_when_status_changes(self):
        """
        When status changes from 'pending' to 'completed', the GSI1 partition
        key should be recomputed to include the new status value.
        """
        task = TaskModel()
        task.id = "task-001"
        task.tenant_id = "tenant-abc"
        task.title = "My Task"
        task.status = "pending"

        # Save initial item (full PutItem)
        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        # Verify initial GSI key
        initial_response = self.db.get(
            key={
                "pk": task.indexes.primary.partition_key.value,
                "sk": task.indexes.primary.sort_key.value,
            },
            table_name=self.table_name,
        )
        initial_item = initial_response["Item"]
        self.assertIn("status#pending", initial_item["gsi1_pk"])

        # Now change status and do a partial update
        task.status = "completed"
        self.db.update_item_partial(item=task, table_name=self.table_name)

        # Verify the GSI key was updated in DynamoDB
        updated_response = self.db.get(
            key={
                "pk": task.indexes.primary.partition_key.value,
                "sk": task.indexes.primary.sort_key.value,
            },
            table_name=self.table_name,
        )
        updated_item = updated_response["Item"]

        # GSI1 pk should now contain the new status
        self.assertIn("status#completed", updated_item["gsi1_pk"])
        self.assertNotIn("status#pending", updated_item["gsi1_pk"])

    def test_gsi_sort_key_updated(self):
        """Verify GSI sort key is also included in the update."""
        task = TaskModel()
        task.id = "task-002"
        task.tenant_id = "tenant-abc"
        task.title = "Another Task"
        task.status = "pending"

        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        # Partial update — status changes
        task.status = "in_progress"
        self.db.update_item_partial(item=task, table_name=self.table_name)

        updated_response = self.db.get(
            key={
                "pk": task.indexes.primary.partition_key.value,
                "sk": task.indexes.primary.sort_key.value,
            },
            table_name=self.table_name,
        )
        updated_item = updated_response["Item"]

        # gsi1_sk should still be present (task#task-002)
        self.assertIn("task#task-002", updated_item["gsi1_sk"])
        # gsi1_pk should reflect new status
        self.assertIn("status#in_progress", updated_item["gsi1_pk"])


# ===========================================================================
# Test 2: GSI query after partial update
# ===========================================================================


@mock_aws
class TestGSIQueryAfterPartialUpdate(unittest.TestCase):
    """After updating a field in a GSI key, querying the GSI should find the record."""

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "tasks"
        create_test_table_with_gsi(self.db.dynamodb_resource, self.table_name)

    def test_query_gsi_finds_record_after_status_change(self):
        """
        After changing status from 'pending' to 'completed' via partial update,
        querying GSI1 for 'completed' should find the record, and querying for
        'pending' should NOT find it.
        """
        task = TaskModel()
        task.id = "task-010"
        task.tenant_id = "tenant-xyz"
        task.title = "GSI Query Test"
        task.status = "pending"

        # Save initial item
        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        # Verify we can find it via GSI with old status
        old_gsi_pk = DynamoDBKey.build_key(("task", "tenant-xyz"), ("status", "pending"))
        response = self.db.query(
            key=Key("gsi1_pk").eq(old_gsi_pk),
            table_name=self.table_name,
            index_name="gsi1",
        )
        self.assertEqual(response["Count"], 1)

        # Change status and partial update
        task.status = "completed"
        self.db.update_item_partial(item=task, table_name=self.table_name)

        # Query GSI for new status — should find the record
        new_gsi_pk = DynamoDBKey.build_key(("task", "tenant-xyz"), ("status", "completed"))
        response = self.db.query(
            key=Key("gsi1_pk").eq(new_gsi_pk),
            table_name=self.table_name,
            index_name="gsi1",
        )
        self.assertEqual(response["Count"], 1)
        self.assertEqual(response["Items"][0]["title"], "GSI Query Test")

        # Query GSI for old status — should NOT find the record
        response = self.db.query(
            key=Key("gsi1_pk").eq(old_gsi_pk),
            table_name=self.table_name,
            index_name="gsi1",
        )
        self.assertEqual(response["Count"], 0)


# ===========================================================================
# Test 3: Primary keys still protected
# ===========================================================================


@mock_aws
class TestPrimaryKeysStillProtected(unittest.TestCase):
    """Verify pk and sk are NOT included in the update SET expression."""

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "tasks"
        create_test_table_with_gsi(self.db.dynamodb_resource, self.table_name)

    def test_pk_and_sk_used_as_key_not_in_set_expression(self):
        """
        Primary key fields (pk, sk) should be used in the Key parameter
        and excluded from the SET expression. The update should succeed
        without trying to modify pk/sk.
        """
        task = TaskModel()
        task.id = "task-020"
        task.tenant_id = "tenant-abc"
        task.title = "Protected Keys Test"
        task.status = "pending"

        # Save initial item
        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        # Partial update — only change title
        task.title = "Updated Title"
        response = self.db.update_item_partial(
            item=task, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify the update succeeded and pk/sk are unchanged
        attrs = response["Attributes"]
        expected_pk = DynamoDBKey.build_key(("task", "tenant-abc"), ("id", "task-020"))
        expected_sk = DynamoDBKey.build_key(("task", "task-020"))
        self.assertEqual(attrs["pk"], expected_pk)
        self.assertEqual(attrs["sk"], expected_sk)
        self.assertEqual(attrs["title"], "Updated Title")

    def test_cannot_clear_primary_key_fields(self):
        """Attempting to clear pk or sk should raise ValueError."""
        task = TaskModel()
        task.id = "task-021"
        task.tenant_id = "tenant-abc"
        task.title = "Clear PK Test"
        task.status = "pending"

        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        with self.assertRaises(ValueError) as ctx:
            self.db.update_item_partial(
                item=task,
                table_name=self.table_name,
                fields_to_clear={"pk"},
            )
        self.assertIn("Cannot clear", str(ctx.exception))


# ===========================================================================
# Test 4: Concurrent-safe partial updates (simulated)
# ===========================================================================


@mock_aws
class TestConcurrentSafePartialUpdates(unittest.TestCase):
    """
    Simulate concurrent partial updates to verify that updating one field
    doesn't clobber other fields, and GSI keys remain correct.
    """

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "tasks"
        create_test_table_with_gsi(self.db.dynamodb_resource, self.table_name)

    def test_partial_update_field_a_does_not_clobber_b_and_c(self):
        """
        Save a record with fields A (status, in GSI key), B (title), C (description).
        Partial update that changes only A should not affect B and C.
        """
        task = TaskModel()
        task.id = "task-030"
        task.tenant_id = "tenant-abc"
        task.title = "Original Title"
        task.description = "Original Description"
        task.status = "pending"
        task.priority = 1

        # Save full item
        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        # Simulate Lambda 1: only changes status (field A)
        task_lambda1 = TaskModel()
        task_lambda1.id = "task-030"
        task_lambda1.tenant_id = "tenant-abc"
        task_lambda1.status = "completed"
        task_lambda1.title = "Original Title"
        task_lambda1.description = "Original Description"
        task_lambda1.priority = 1

        self.db.update_item_partial(item=task_lambda1, table_name=self.table_name)

        # Verify B and C are unchanged
        pk = DynamoDBKey.build_key(("task", "tenant-abc"), ("id", "task-030"))
        sk = DynamoDBKey.build_key(("task", "task-030"))
        response = self.db.get(key={"pk": pk, "sk": sk}, table_name=self.table_name)
        item = response["Item"]

        self.assertEqual(item["status"], "completed")
        self.assertEqual(item["title"], "Original Title")
        self.assertEqual(item["description"], "Original Description")
        self.assertEqual(item["priority"], 1)

    def test_sequential_partial_updates_preserve_gsi_keys(self):
        """
        After Lambda 1 updates field A (status), Lambda 2 updates field B (title).
        Verify that field A's GSI key is still correct after Lambda 2's update.
        """
        task = TaskModel()
        task.id = "task-031"
        task.tenant_id = "tenant-abc"
        task.title = "Original Title"
        task.description = "Original Description"
        task.status = "pending"

        # Save full item
        self.db.save(
            item=task.to_resource_dictionary(include_indexes=True),
            table_name=self.table_name,
        )

        # Lambda 1: change status to 'completed'
        task.status = "completed"
        self.db.update_item_partial(item=task, table_name=self.table_name)

        # Lambda 2: change title (status is still 'completed' on the model)
        task.title = "Updated Title"
        self.db.update_item_partial(item=task, table_name=self.table_name)

        # Verify GSI key still reflects 'completed'
        pk = DynamoDBKey.build_key(("task", "tenant-abc"), ("id", "task-031"))
        sk = DynamoDBKey.build_key(("task", "task-031"))
        response = self.db.get(key={"pk": pk, "sk": sk}, table_name=self.table_name)
        item = response["Item"]

        self.assertEqual(item["status"], "completed")
        self.assertEqual(item["title"], "Updated Title")
        self.assertIn("status#completed", item["gsi1_pk"])

        # Verify GSI query still works
        gsi_pk = DynamoDBKey.build_key(("task", "tenant-abc"), ("status", "completed"))
        gsi_response = self.db.query(
            key=Key("gsi1_pk").eq(gsi_pk),
            table_name=self.table_name,
            index_name="gsi1",
        )
        self.assertEqual(gsi_response["Count"], 1)
        self.assertEqual(gsi_response["Items"][0]["title"], "Updated Title")


# ===========================================================================
# Test 5: Non-model dict input still works
# ===========================================================================


@mock_aws
class TestNonModelDictInputStillWorks(unittest.TestCase):
    """When a raw dict is passed, behavior should be unchanged (no prep_for_save)."""

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "tasks"
        create_test_table_with_gsi(self.db.dynamodb_resource, self.table_name)

    def test_dict_input_updates_fields_normally(self):
        """Raw dict input should update fields without any GSI key logic."""
        # Save initial item
        initial_item = {
            "pk": "task#tenant-abc#id#task-040",
            "sk": "task#task-040",
            "title": "Dict Test",
            "status": "pending",
            "gsi1_pk": "task#tenant-abc#status#pending",
            "gsi1_sk": "task#task-040",
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        # Partial update with raw dict — only updates title
        update_dict = {
            "pk": "task#tenant-abc#id#task-040",
            "sk": "task#task-040",
            "title": "Updated Dict Title",
        }
        self.db.update_item_partial(item=update_dict, table_name=self.table_name)

        # Verify title was updated
        response = self.db.get(
            key={"pk": "task#tenant-abc#id#task-040", "sk": "task#task-040"},
            table_name=self.table_name,
        )
        item = response["Item"]
        self.assertEqual(item["title"], "Updated Dict Title")
        # GSI key should be unchanged (no recomputation for raw dicts)
        self.assertEqual(item["gsi1_pk"], "task#tenant-abc#status#pending")

    def test_dict_input_does_not_call_prep_for_save(self):
        """
        When a raw dict is passed, prep_for_save should not be called
        (it doesn't exist on dicts anyway). The update should work normally.
        """
        initial_item = {
            "pk": "dict-pk-001",
            "sk": "dict-sk-001",
            "name": "Original",
            "value": 42,
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        update_dict = {
            "pk": "dict-pk-001",
            "sk": "dict-sk-001",
            "name": "Updated",
        }
        response = self.db.update_item_partial(
            item=update_dict, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertEqual(response["Attributes"]["name"], "Updated")
        self.assertEqual(response["Attributes"]["value"], 42)

    def test_dict_input_with_gsi_fields_includes_them_in_update(self):
        """
        When a raw dict includes GSI key fields, they should be updatable
        (since pk/sk are the only protected fields for dict input).
        """
        initial_item = {
            "pk": "dict-pk-002",
            "sk": "dict-sk-002",
            "gsi1_pk": "old-gsi-value",
            "gsi1_sk": "old-gsi-sk",
            "name": "Test",
        }
        self.db.save(item=initial_item, table_name=self.table_name)

        update_dict = {
            "pk": "dict-pk-002",
            "sk": "dict-sk-002",
            "gsi1_pk": "new-gsi-value",
            "name": "Updated Test",
        }
        response = self.db.update_item_partial(
            item=update_dict, table_name=self.table_name, return_values="ALL_NEW"
        )

        self.assertEqual(response["Attributes"]["gsi1_pk"], "new-gsi-value")
        self.assertEqual(response["Attributes"]["name"], "Updated Test")


if __name__ == "__main__":
    unittest.main()
