"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for DynamoDB throttle retry logic (_retry_on_throttle)
"""

import unittest
from unittest.mock import MagicMock, patch

import boto3
from botocore.exceptions import ClientError
from hypothesis import given, settings
from hypothesis import strategies as st
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import RETRYABLE_THROTTLE_CODES, DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService


def _make_throttle_error():
    """Create a ProvisionedThroughputExceededException ClientError."""
    return ClientError(
        {
            "Error": {
                "Code": "ProvisionedThroughputExceededException",
                "Message": "Rate exceeded",
            }
        },
        "UpdateItem",
    )


def _make_throttling_exception_error():
    """Create a ThrottlingException ClientError."""
    return ClientError(
        {
            "Error": {
                "Code": "ThrottlingException",
                "Message": "Rate exceeded",
            }
        },
        "PutItem",
    )


def _make_request_limit_error():
    """Create a RequestLimitExceeded ClientError."""
    return ClientError(
        {
            "Error": {
                "Code": "RequestLimitExceeded",
                "Message": "Account-level request limit exceeded",
            }
        },
        "PutItem",
    )


def _make_validation_error():
    """Create a non-retryable ValidationException ClientError."""
    return ClientError(
        {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid expression",
            }
        },
        "UpdateItem",
    )


def _make_client_error(code: str) -> ClientError:
    """Create a ClientError with the given error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": f"Simulated {code}"}},
        "DynamoDBOperation",
    )


class TestRetryOnThrottle(unittest.TestCase):
    """Tests for the _retry_on_throttle helper method."""

    def setUp(self):
        self.db = DynamoDB()

    @patch("time.sleep", return_value=None)
    def test_succeeds_on_first_attempt(self, mock_sleep):
        """Operation succeeds immediately — no retries."""
        result = self.db._retry_on_throttle(
            lambda: {"ok": True},
            operation_name="test",
        )
        self.assertEqual(result, {"ok": True})
        mock_sleep.assert_not_called()

    @patch("time.sleep", return_value=None)
    def test_retries_on_throttle_then_succeeds(self, mock_sleep):
        """Throttle on first two attempts, succeed on third."""
        call_count = {"n": 0}

        def operation():
            call_count["n"] += 1
            if call_count["n"] <= 2:
                raise _make_throttle_error()
            return {"ok": True}

        result = self.db._retry_on_throttle(
            operation,
            operation_name="test",
        )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(call_count["n"], 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep", return_value=None)
    def test_raises_after_max_retries(self, mock_sleep):
        """Throttle on every attempt — raises after max_retries."""

        def operation():
            raise _make_throttle_error()

        with self.assertRaises(ClientError) as ctx:
            self.db._retry_on_throttle(
                operation,
                max_retries=3,
                operation_name="test",
            )
        self.assertEqual(
            ctx.exception.response["Error"]["Code"],
            "ProvisionedThroughputExceededException",
        )
        # initial attempt + 3 retries = 3 sleeps
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("time.sleep", return_value=None)
    def test_non_throttle_error_raises_immediately(self, mock_sleep):
        """Non-throttle ClientError is not retried."""

        def operation():
            raise _make_validation_error()

        with self.assertRaises(ClientError) as ctx:
            self.db._retry_on_throttle(
                operation,
                operation_name="test",
            )
        self.assertEqual(
            ctx.exception.response["Error"]["Code"],
            "ValidationException",
        )
        mock_sleep.assert_not_called()

    @patch("time.sleep", return_value=None)
    def test_exponential_backoff_timing(self, mock_sleep):
        """Verify backoff doubles each retry."""
        call_count = {"n": 0}

        def operation():
            call_count["n"] += 1
            if call_count["n"] <= 3:
                raise _make_throttle_error()
            return {"ok": True}

        self.db._retry_on_throttle(
            operation,
            initial_backoff=0.1,
            operation_name="test",
        )
        # Backoff sequence: 0.1, 0.2, 0.4
        sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
        self.assertAlmostEqual(sleep_args[0], 0.1)
        self.assertAlmostEqual(sleep_args[1], 0.2)
        self.assertAlmostEqual(sleep_args[2], 0.4)

    @patch("time.sleep", return_value=None)
    def test_non_client_error_not_caught(self, mock_sleep):
        """Non-ClientError exceptions propagate immediately."""

        def operation():
            raise ValueError("bad input")

        with self.assertRaises(ValueError):
            self.db._retry_on_throttle(
                operation,
                operation_name="test",
            )
        mock_sleep.assert_not_called()

    # --- New tests for ThrottlingException and RequestLimitExceeded ---

    @patch("time.sleep", return_value=None)
    def test_throttling_exception_triggers_retry_then_succeeds(self, mock_sleep):
        """ThrottlingException on first attempt, succeed on second."""
        call_count = {"n": 0}

        def operation():
            call_count["n"] += 1
            if call_count["n"] <= 1:
                raise _make_throttling_exception_error()
            return {"ok": True}

        result = self.db._retry_on_throttle(operation, operation_name="test")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(call_count["n"], 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("time.sleep", return_value=None)
    def test_request_limit_exceeded_triggers_retry_then_succeeds(self, mock_sleep):
        """RequestLimitExceeded on first attempt, succeed on second."""
        call_count = {"n": 0}

        def operation():
            call_count["n"] += 1
            if call_count["n"] <= 1:
                raise _make_request_limit_error()
            return {"ok": True}

        result = self.db._retry_on_throttle(operation, operation_name="test")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(call_count["n"], 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("time.sleep", return_value=None)
    def test_throttling_exception_raises_after_max_retries(self, mock_sleep):
        """ThrottlingException on every attempt — raises after max_retries."""

        def operation():
            raise _make_throttling_exception_error()

        with self.assertRaises(ClientError) as ctx:
            self.db._retry_on_throttle(operation, max_retries=3, operation_name="test")
        self.assertEqual(ctx.exception.response["Error"]["Code"], "ThrottlingException")
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("time.sleep", return_value=None)
    def test_request_limit_exceeded_raises_after_max_retries(self, mock_sleep):
        """RequestLimitExceeded on every attempt — raises after max_retries."""

        def operation():
            raise _make_request_limit_error()

        with self.assertRaises(ClientError) as ctx:
            self.db._retry_on_throttle(operation, max_retries=3, operation_name="test")
        self.assertEqual(ctx.exception.response["Error"]["Code"], "RequestLimitExceeded")
        self.assertEqual(mock_sleep.call_count, 3)

    def test_updated_default_parameters(self):
        """Verify _retry_on_throttle defaults are max_retries=9, initial_backoff=0.5."""
        import inspect

        sig = inspect.signature(self.db._retry_on_throttle)
        self.assertEqual(sig.parameters["max_retries"].default, 9)
        self.assertEqual(sig.parameters["initial_backoff"].default, 0.5)


class TestRetryOnThrottlePBT(unittest.TestCase):
    """Property-based tests for _retry_on_throttle throttle code handling."""

    def setUp(self):
        self.db = DynamoDB()

    @given(error_code=st.sampled_from(sorted(RETRYABLE_THROTTLE_CODES)))
    @settings(max_examples=20)
    @patch("time.sleep", return_value=None)
    def test_pbt_retryable_codes_trigger_retry(self, mock_sleep, error_code):
        """Property 1: Any error code in RETRYABLE_THROTTLE_CODES triggers retry."""
        call_count = {"n": 0}

        def operation():
            call_count["n"] += 1
            if call_count["n"] <= 1:
                raise _make_client_error(error_code)
            return {"ok": True}

        result = self.db._retry_on_throttle(operation, operation_name="pbt-test")
        self.assertEqual(result, {"ok": True})
        self.assertGreater(call_count["n"], 1, f"{error_code} should have triggered a retry")
        self.assertGreater(mock_sleep.call_count, 0)

    @given(
        error_code=st.sampled_from(
            [
                "ValidationException",
                "ResourceNotFoundException",
                "AccessDeniedException",
                "ConditionalCheckFailedException",
                "ItemCollectionSizeLimitExceededException",
                "InternalServerError",
                "ServiceUnavailable",
            ]
        )
    )
    @settings(max_examples=30)
    @patch("time.sleep", return_value=None)
    def test_pbt_non_retryable_codes_raise_immediately(self, mock_sleep, error_code):
        """Property 2: Any error code NOT in RETRYABLE_THROTTLE_CODES raises immediately."""

        def operation():
            raise _make_client_error(error_code)

        with self.assertRaises(ClientError) as ctx:
            self.db._retry_on_throttle(operation, operation_name="pbt-test")
        self.assertEqual(ctx.exception.response["Error"]["Code"], error_code)
        mock_sleep.assert_not_called()


@mock_aws
class TestThrottleRetryIntegration(unittest.TestCase):
    """Integration tests verifying retry wrapping on real DynamoDB operations."""

    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_throttle_table"

        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

        # Seed a test item
        self.db.save(
            item={"pk": "user#1", "sk": "user#1", "name": "Alice", "counter": 0},
            table_name=self.table_name,
        )

    def test_update_item_succeeds_normally(self):
        """update_item works end-to-end with retry wrapper in place."""
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#1", "sk": "user#1"},
            update_expression="ADD #counter :inc",
            expression_attribute_names={"#counter": "counter"},
            expression_attribute_values={":inc": 1},
            return_values="ALL_NEW",
        )
        item = self.db.get(
            key={"pk": "user#1", "sk": "user#1"},
            table_name=self.table_name,
        )
        self.assertEqual(item.get("Item", {}).get("counter"), 1)

    def test_save_succeeds_normally(self):
        """save works end-to-end with retry wrapper in place."""
        self.db.save(
            item={"pk": "user#2", "sk": "user#2", "name": "Bob"},
            table_name=self.table_name,
        )
        item = self.db.get(
            key={"pk": "user#2", "sk": "user#2"},
            table_name=self.table_name,
        )
        self.assertEqual(item.get("Item", {}).get("name"), "Bob")

    def test_query_succeeds_normally(self):
        """query works end-to-end with retry wrapper in place."""
        from boto3.dynamodb.conditions import Key

        response = self.db.query(
            key=Key("pk").eq("user#1"),
            table_name=self.table_name,
        )
        self.assertEqual(response["Count"], 1)

    def test_delete_succeeds_normally(self):
        """delete works end-to-end with retry wrapper in place."""
        self.db.delete(
            primary_key={"pk": "user#1", "sk": "user#1"},
            table_name=self.table_name,
        )
        item = self.db.get(
            key={"pk": "user#1", "sk": "user#1"},
            table_name=self.table_name,
        )
        self.assertNotIn("Item", item)


if __name__ == "__main__":
    unittest.main()
