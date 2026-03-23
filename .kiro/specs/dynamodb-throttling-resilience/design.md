# DynamoDB Throttling Resilience Bugfix Design

## Overview

The `batch_write_item()` and `_retry_on_throttle()` methods in `boto3-assist/src/boto3_assist/dynamodb/dynamodb.py` only retry on `ProvisionedThroughputExceededException`, ignoring `ThrottlingException` and `RequestLimitExceeded`. This causes GSI-triggered throttling to crash the entire NCA analysis pipeline. Additionally, the retry budget (5 retries, 0.1s initial backoff, ~3.2s max cumulative wait) is insufficient for GSI auto-scaling which can take 5-10+ seconds. The fix extracts a shared constant for retryable throttle codes, updates both methods to check against it, and increases retry parameters to survive auto-scaling lag.

## Glossary

- **Bug_Condition (C)**: A DynamoDB operation throws `ThrottlingException` or `RequestLimitExceeded` (error codes not currently retried), OR throws any retryable throttle error but the retry budget is exhausted too quickly due to insufficient max_retries/initial_backoff.
- **Property (P)**: All three throttling error codes are retried with exponential backoff, and the retry window is long enough (9 retries, 0.5s initial backoff, ~128s max cumulative) to survive GSI auto-scaling.
- **Preservation**: Existing retry behavior for `ProvisionedThroughputExceededException`, immediate raise for non-throttle errors, first-attempt success with no delay, unprocessed-items retry loop, and 25-item chunking must remain unchanged.
- **`_retry_on_throttle()`**: Generic retry wrapper at line ~156 in `dynamodb.py` used by `save`, `get`, `update_item`, `query`, and `delete` operations.
- **`batch_write_item()`**: Batch write method at line ~1474 in `dynamodb.py` with its own inline retry logic for both unprocessed items and `ClientError` throttling.
- **`RETRYABLE_THROTTLE_CODES`**: New module-level constant `{"ProvisionedThroughputExceededException", "ThrottlingException", "RequestLimitExceeded"}` to be shared by both methods.

## Bug Details

### Bug Condition

The bug manifests when DynamoDB throws `ThrottlingException` or `RequestLimitExceeded` during any operation that uses `_retry_on_throttle()` or `batch_write_item()`. These error codes are not recognized as retryable, so the exception propagates immediately. A secondary condition occurs when `ProvisionedThroughputExceededException` is thrown but the retry budget (5 retries × 0.1s doubling backoff = ~3.2s max) is exhausted before GSI auto-scaling completes (5-10+ seconds).

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type (operation_callable, error_response)
  OUTPUT: boolean

  error_code := error_response.Error.Code

  // Primary bug: unrecognized throttle codes
  IF error_code IN {"ThrottlingException", "RequestLimitExceeded"}
    RETURN TRUE
  END IF

  // Secondary bug: insufficient retry budget for any throttle code
  IF error_code IN {"ProvisionedThroughputExceededException", "ThrottlingException", "RequestLimitExceeded"}
    AND gsi_auto_scaling_in_progress()
    AND cumulative_backoff(max_retries=5, initial=0.1) < auto_scaling_duration()
    RETURN TRUE
  END IF

  RETURN FALSE
END FUNCTION
```

### Examples

- **ThrottlingException in batch_write_item**: Writing 10k profile splits triggers GSI throttling. DynamoDB returns `ThrottlingException`. The `except ClientError` block checks `error_code == "ProvisionedThroughputExceededException"`, which is `False`, so the exception is raised immediately. Pipeline crashes.
- **RequestLimitExceeded in _retry_on_throttle**: High-concurrency Lambda invocations hit the account-level request limit. `_retry_on_throttle` only checks for `ProvisionedThroughputExceededException`, so `RequestLimitExceeded` propagates. `save()`, `query()`, `update_item()`, `delete()` all fail.
- **ProvisionedThroughputExceededException with insufficient budget**: GSI auto-scaling takes 8 seconds. With 5 retries and 0.1s initial backoff, the cumulative wait is 0.1 + 0.2 + 0.4 + 0.8 + 1.6 = 3.1s. All retries exhausted before scaling completes.
- **ThrottlingException in _retry_on_throttle via save()**: A `save()` call triggers `ThrottlingException`. `_retry_on_throttle` doesn't recognize it, raises immediately.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `ProvisionedThroughputExceededException` continues to be retried with exponential backoff (same logic, just expanded error code set)
- Non-throttle `ClientError` exceptions (`ValidationException`, `ResourceNotFoundException`, `AccessDeniedException`, `ConditionalCheckFailedException`) are raised immediately without retry
- Non-`ClientError` exceptions (`ValueError`, `TypeError`, etc.) propagate immediately
- Operations that succeed on the first attempt return immediately with no delay
- `batch_write_item` unprocessed-items retry loop continues to function independently of the `ClientError` retry
- `batch_write_item` 25-item chunking logic is unchanged
- `batch_write_item` invalid operation validation (`put`/`delete` only) is unchanged
- All callers of `_retry_on_throttle` (`save`, `get`, `update_item`, `query`, `delete`) continue to work identically for non-throttle paths

**Scope:**
All inputs that do NOT involve `ThrottlingException`, `RequestLimitExceeded`, or retry budget exhaustion should be completely unaffected by this fix. This includes:
- Successful operations (no errors)
- Non-throttle ClientError exceptions
- Non-ClientError exceptions
- Unprocessed items handling in batch_write_item

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Incomplete Error Code Matching in `_retry_on_throttle()`**: Line ~190 checks `error_code == "ProvisionedThroughputExceededException"` as a string equality. `ThrottlingException` and `RequestLimitExceeded` are not checked, so they fall through to `raise`.

2. **Incomplete Error Code Matching in `batch_write_item()`**: Line ~1645 has the same single-code check in its `except ClientError` block. Same root cause, duplicated in a separate retry loop.

3. **Insufficient Retry Parameters**: Both methods use `max_retries=5` and `initial_backoff=0.1`, yielding a cumulative backoff of ~3.1 seconds. GSI auto-scaling can take 5-10+ seconds, so the retry budget is exhausted before capacity is provisioned.

4. **No Shared Constant for Retryable Codes**: The error codes are hardcoded as string literals in each method independently, violating DRY. The reference implementations in `geek-cafe-saas-sdk` (`with_throttling_retry`) and `Aplos-NCA-Calc-Engine` (`_is_transient_error`) correctly use all three codes but this pattern was not applied to `boto3-assist`.

## Correctness Properties

Property 1: Bug Condition - All Throttling Error Codes Are Retried

_For any_ DynamoDB operation that throws a `ClientError` with error code in `{"ThrottlingException", "RequestLimitExceeded", "ProvisionedThroughputExceededException"}`, the fixed `_retry_on_throttle()` and `batch_write_item()` SHALL retry the operation with exponential backoff rather than raising immediately.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Throttle Errors Raise Immediately

_For any_ DynamoDB operation that throws a `ClientError` with an error code NOT in `{"ThrottlingException", "RequestLimitExceeded", "ProvisionedThroughputExceededException"}`, the fixed code SHALL raise the exception immediately without retrying, preserving the existing fail-fast behavior for non-retryable errors.

**Validates: Requirements 3.1, 3.2, 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `boto3-assist/src/boto3_assist/dynamodb/dynamodb.py`

**Change 1: Add Module-Level Constant**

Add a `RETRYABLE_THROTTLE_CODES` set near the top of the file (after imports):
```python
RETRYABLE_THROTTLE_CODES = {
    "ProvisionedThroughputExceededException",
    "ThrottlingException",
    "RequestLimitExceeded",
}
```

**Change 2: Update `_retry_on_throttle()` Error Check**

Replace:
```python
if (
    error_code == "ProvisionedThroughputExceededException"
    and retry_count < max_retries
):
```
With:
```python
if (
    error_code in RETRYABLE_THROTTLE_CODES
    and retry_count < max_retries
):
```

**Change 3: Update `_retry_on_throttle()` Default Parameters**

Change `max_retries` default from `5` to `9` and `initial_backoff` default from `0.1` to `0.5`.

**Change 4: Update `batch_write_item()` Error Check**

Replace:
```python
if (
    error_code == "ProvisionedThroughputExceededException"
    and retry_count < max_retries
):
```
With:
```python
if (
    error_code in RETRYABLE_THROTTLE_CODES
    and retry_count < max_retries
):
```

**Change 5: Update `batch_write_item()` Retry Parameters**

Change `max_retries` from `5` to `9` and `backoff_time` from `0.1` to `0.5`.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that create `ClientError` instances with `ThrottlingException` and `RequestLimitExceeded` error codes, pass them to `_retry_on_throttle()` and `batch_write_item()`, and assert that retries occur. Run these tests on the UNFIXED code to observe failures and confirm the root cause.

**Test Cases**:
1. **ThrottlingException in _retry_on_throttle**: Call `_retry_on_throttle` with an operation that throws `ThrottlingException` then succeeds. Expect retry on fixed code, immediate raise on unfixed code. (will fail on unfixed code)
2. **RequestLimitExceeded in _retry_on_throttle**: Same as above with `RequestLimitExceeded`. (will fail on unfixed code)
3. **ThrottlingException in batch_write_item**: Mock `batch_write_item` to throw `ThrottlingException` on first call, succeed on second. (will fail on unfixed code)
4. **RequestLimitExceeded in batch_write_item**: Same as above with `RequestLimitExceeded`. (will fail on unfixed code)

**Expected Counterexamples**:
- `ThrottlingException` and `RequestLimitExceeded` are raised immediately without retry
- Confirms root cause: error code check is limited to `ProvisionedThroughputExceededException`

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedFunction(input)
  ASSERT result retried with exponential backoff
  ASSERT result eventually succeeded or exhausted retries gracefully
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalFunction(input) = fixedFunction(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-throttle errors and successful operations, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Non-Throttle Error Preservation**: Generate random non-throttle error codes (`ValidationException`, `ResourceNotFoundException`, `AccessDeniedException`, `ConditionalCheckFailedException`, etc.) and verify they raise immediately without retry on both unfixed and fixed code.
2. **Success Path Preservation**: Verify operations that succeed on first attempt return immediately with no sleep calls on both unfixed and fixed code.
3. **ProvisionedThroughputExceededException Preservation**: Verify existing retry behavior for `ProvisionedThroughputExceededException` continues to work identically (retries with backoff, raises after max retries).

### Unit Tests

- Test `_retry_on_throttle` retries on `ThrottlingException` then succeeds
- Test `_retry_on_throttle` retries on `RequestLimitExceeded` then succeeds
- Test `_retry_on_throttle` raises after max retries for each throttle code
- Test `_retry_on_throttle` non-throttle `ClientError` raises immediately (preservation)
- Test `_retry_on_throttle` non-`ClientError` exceptions propagate immediately (preservation)
- Test `_retry_on_throttle` success on first attempt with no sleep (preservation)
- Test `batch_write_item` retries on `ThrottlingException`
- Test `batch_write_item` retries on `RequestLimitExceeded`
- Test `batch_write_item` non-throttle error raises immediately (preservation)
- Test updated default parameters (max_retries=9, initial_backoff=0.5)
- Test exponential backoff timing with new defaults

### Property-Based Tests

- Generate random error codes from a set of known DynamoDB error codes and verify: throttle codes are retried, non-throttle codes raise immediately
- Generate random retry counts and backoff values and verify exponential backoff formula holds
- Generate random batch sizes and verify chunking + retry behavior is consistent

### Integration Tests

- Test full save → throttle → retry → success flow with moto
- Test full batch_write_item → throttle → retry → success flow with moto
- Test that existing integration tests continue to pass unchanged
