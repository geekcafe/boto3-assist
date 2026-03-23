# Bugfix Requirements Document

## Introduction

The `batch_write_item()` method in `boto3-assist/src/boto3_assist/dynamodb/dynamodb.py` fails the entire NCA analysis pipeline when DynamoDB GSI auto-scaling triggers throttling during large batch writes (e.g., 10k profile splits). The retry logic only handles `ProvisionedThroughputExceededException` but not `ThrottlingException` or `RequestLimitExceeded`, causing GSI-triggered throttling to fall through to an unhandled raise. This is inconsistent with the rest of the codebase, where the retry decorator (`with_throttling_retry`) and transient error detection (`_is_transient_error`) correctly handle all three throttling error codes.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN DynamoDB throws `ThrottlingException` during a `batch_write_item` call (e.g., GSI auto-scaling throughput exceeded) THEN the system raises the exception immediately without retrying, causing the entire analysis pipeline to fail.

1.2 WHEN DynamoDB throws `RequestLimitExceeded` during a `batch_write_item` call THEN the system raises the exception immediately without retrying, causing the entire analysis pipeline to fail.

1.3 WHEN DynamoDB throws `ProvisionedThroughputExceededException` during a `batch_write_item` call and the retry budget is exhausted after 5 retries with a maximum cumulative backoff of ~3.2 seconds THEN the system fails because GSI auto-scaling can take 5-10+ seconds to provision additional capacity, making the retry window insufficient.

### Expected Behavior (Correct)

2.1 WHEN DynamoDB throws `ThrottlingException` during a `batch_write_item` call THEN the system SHALL retry the operation with exponential backoff, identical to how `ProvisionedThroughputExceededException` is currently handled.

2.2 WHEN DynamoDB throws `RequestLimitExceeded` during a `batch_write_item` call THEN the system SHALL retry the operation with exponential backoff, identical to how `ProvisionedThroughputExceededException` is currently handled.

2.3 WHEN DynamoDB throws any retryable throttling exception (`ProvisionedThroughputExceededException`, `ThrottlingException`, or `RequestLimitExceeded`) during a `batch_write_item` call THEN the system SHALL retry up to 9 times (increased from 5) with an initial backoff of 500ms (increased from 100ms) to allow sufficient time for GSI auto-scaling to complete.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN DynamoDB throws `ProvisionedThroughputExceededException` during a `batch_write_item` call and retries are available THEN the system SHALL CONTINUE TO retry the operation with exponential backoff.

3.2 WHEN DynamoDB throws a non-throttling `ClientError` (e.g., `ValidationException`, `ResourceNotFoundException`, `AccessDeniedException`) during a `batch_write_item` call THEN the system SHALL CONTINUE TO raise the exception immediately without retrying.

3.3 WHEN a `batch_write_item` call succeeds on the first attempt without any throttling THEN the system SHALL CONTINUE TO return the response immediately without any delay.

3.4 WHEN a `batch_write_item` call returns `UnprocessedItems` in the response (not a ClientError exception) THEN the system SHALL CONTINUE TO retry unprocessed items using the existing unprocessed-items retry loop.

3.5 WHEN the batch contains more than 25 items THEN the system SHALL CONTINUE TO chunk items into batches of 25 and process each chunk independently.
