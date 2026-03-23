"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for batch_write_item() throttle retry logic.
Validates that ThrottlingException and RequestLimitExceeded are retried
with exponential backoff, and non-throttle errors raise immediately.
"""

import inspect
import unittest
from unittest.mock import MagicMock, patch

import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import RETRYABLE_THROTTLE_CODES, DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService


def _make_client_error(code: str) -> ClientError:
    """Create a ClientError with the given error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": f"Simulated {code}"}},
        "BatchWriteItem",
    )


@mock_aws
class TestBatchWriteItemThrottleRetry(unittest.TestCase):
    """Tests for batch_write_item throttle retry on ThrottlingException and RequestLimitExceeded."""

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_batch_throttle_table"

        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

        self.test_items = [
            {"pk": f"user#{i}", "sk": f"user#{i}", "name": f"User {i}"} for i in range(3)
        ]

    @patch("time.sleep", return_value=None)
    def test_throttling_exception_triggers_retry_then_succeeds(self, mock_sleep):
        """ThrottlingException on first call, succeed on second."""
        original_batch_write = self.db.dynamodb_resource.meta.client.batch_write_item
        call_count = {"n": 0}

        def mock_batch_write(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise _make_client_error("ThrottlingException")
            return original_batch_write(**kwargs)

        self.db.dynamodb_resource.meta.client.batch_write_item = mock_batch_write

        response = self.db.batch_write_item(items=self.test_items, table_name=self.table_name)
        self.assertEqual(response["ProcessedCount"], 3)
        self.assertEqual(call_count["n"], 2)
        self.assertGreater(mock_sleep.call_count, 0)

    @patch("time.sleep", return_value=None)
    def test_request_limit_exceeded_triggers_retry_then_succeeds(self, mock_sleep):
        """RequestLimitExceeded on first call, succeed on second."""
        original_batch_write = self.db.dynamodb_resource.meta.client.batch_write_item
        call_count = {"n": 0}

        def mock_batch_write(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise _make_client_error("RequestLimitExceeded")
            return original_batch_write(**kwargs)

        self.db.dynamodb_resource.meta.client.batch_write_item = mock_batch_write

        response = self.db.batch_write_item(items=self.test_items, table_name=self.table_name)
        self.assertEqual(response["ProcessedCount"], 3)
        self.assertEqual(call_count["n"], 2)
        self.assertGreater(mock_sleep.call_count, 0)

    @patch("time.sleep", return_value=None)
    def test_non_throttle_error_raises_immediately(self, mock_sleep):
        """Non-throttle ClientError (ValidationException) raises without retry."""

        def mock_batch_write(**kwargs):
            raise _make_client_error("ValidationException")

        self.db.dynamodb_resource.meta.client.batch_write_item = mock_batch_write

        with self.assertRaises(ClientError) as ctx:
            self.db.batch_write_item(items=self.test_items, table_name=self.table_name)
        self.assertEqual(ctx.exception.response["Error"]["Code"], "ValidationException")
        mock_sleep.assert_not_called()

    def test_updated_retry_parameters(self):
        """Verify batch_write_item uses max_retries=9 and backoff_time=0.5."""
        # We inspect the source code to verify the hardcoded values
        source = inspect.getsource(self.db.batch_write_item)
        self.assertIn("max_retries = 9", source)
        self.assertIn("backoff_time = 0.5", source)


if __name__ == "__main__":
    unittest.main()
