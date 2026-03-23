# Tasks

## Task 1: Add RETRYABLE_THROTTLE_CODES constant and update _retry_on_throttle()

- [x] 1.1 Add `RETRYABLE_THROTTLE_CODES` module-level constant (set of three error codes) near the top of `boto3-assist/src/boto3_assist/dynamodb/dynamodb.py` after imports
- [x] 1.2 Update `_retry_on_throttle()` to check `error_code in RETRYABLE_THROTTLE_CODES` instead of `error_code == "ProvisionedThroughputExceededException"`
- [x] 1.3 Update `_retry_on_throttle()` default parameters: `max_retries=9`, `initial_backoff=0.5`
- [x] 1.4 Update `_retry_on_throttle()` log message from "Throughput exceeded" to "Throttled" to reflect broader error code coverage

## Task 2: Update batch_write_item() retry logic

- [x] 2.1 Update `batch_write_item()` ClientError handler to check `error_code in RETRYABLE_THROTTLE_CODES` instead of `error_code == "ProvisionedThroughputExceededException"`
- [x] 2.2 Update `batch_write_item()` retry parameters: `max_retries=9`, `backoff_time=0.5`
- [x] 2.3 Update `batch_write_item()` log message to reflect broader error code coverage

## Task 3: Unit tests for _retry_on_throttle() bug fix

- [x] 3.1 Add helper `_make_throttling_exception_error()` that creates a `ClientError` with code `ThrottlingException`
- [x] 3.2 Add helper `_make_request_limit_error()` that creates a `ClientError` with code `RequestLimitExceeded`
- [x] 3.3 Add test: `ThrottlingException` triggers retry then succeeds
- [x] 3.4 Add test: `RequestLimitExceeded` triggers retry then succeeds
- [x] 3.5 Add test: `ThrottlingException` raises after max retries exhausted
- [x] 3.6 Add test: `RequestLimitExceeded` raises after max retries exhausted
- [x] 3.7 Add test: verify updated default parameters (max_retries=9, initial_backoff=0.5)
- [x] 3.8 [PBT-exploration] Property test: for any error code in RETRYABLE_THROTTLE_CODES, _retry_on_throttle retries the operation (Property 1)
- [x] 3.9 [PBT-preservation] Property test: for any error code NOT in RETRYABLE_THROTTLE_CODES, _retry_on_throttle raises immediately without retry (Property 2)

## Task 4: Unit tests for batch_write_item() bug fix

- [x] 4.1 Add test: `ThrottlingException` in batch_write_item triggers retry then succeeds
- [x] 4.2 Add test: `RequestLimitExceeded` in batch_write_item triggers retry then succeeds
- [x] 4.3 Add test: non-throttle `ClientError` in batch_write_item raises immediately (preservation)
- [x] 4.4 Add test: verify batch_write_item updated retry parameters (max_retries=9, backoff_time=0.5)

## Task 5: Run all tests and verify

- [x] 5.1 Run existing throttle retry tests to verify no regressions: `source boto3-assist/.venv/bin/activate && python -m pytest boto3-assist/tests/unit/dynamodb_tests/dynamodb_throttle_retry_test.py -v --ignore=tests/integration`
- [x] 5.2 Run existing batch operations tests to verify no regressions: `source boto3-assist/.venv/bin/activate && python -m pytest boto3-assist/tests/unit/dynamodb_tests/dynamodb_batch_operations_test.py -v --ignore=tests/integration`
- [x] 5.3 Run full unit test suite to verify no regressions: `source boto3-assist/.venv/bin/activate && python -m pytest boto3-assist/tests/unit/ -v --ignore=tests/integration`
