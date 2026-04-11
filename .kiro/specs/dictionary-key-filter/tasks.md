# Implementation Plan: Dictionary Key Filter

## Overview

Add an optional `keys` parameter to `DynamoDBModelBase.to_dictionary()` and `DynamoDBModelBase.to_dict()` that filters the returned dictionary to include only specified top-level keys. The filtering is applied after full serialization to avoid interfering with existing logic.

## Tasks

- [x] 1. Add `keys` parameter to `to_dictionary` and `to_dict`
  - [x] 1.1 Modify `to_dictionary` in `boto3-assist/src/boto3_assist/dynamodb/dynamodb_model_base.py`
    - Add `keys: List[str] | None = None` parameter to the method signature
    - After the call to `DynamoDBSerializer.to_resource_dictionary`, add filtering: `if keys is not None: d = {k: v for k, v in d.items() if k in keys}`
    - Return the filtered (or unfiltered) dictionary
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1, 3.2_

  - [x] 1.2 Modify `to_dict` in `boto3-assist/src/boto3_assist/dynamodb/dynamodb_model_base.py`
    - Add `keys: List[str] | None = None` parameter to the method signature
    - Pass `keys` through to `self.to_dictionary(include_none=include_none, keys=keys)`
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 2. Write tests for key filtering
  - [x] 2.1 Write unit tests in `boto3-assist/tests/unit/dynamodb_tests/test_dictionary_key_filter.py`
    - Test `to_dictionary(keys=["id", "first_name"])` returns exactly those two fields on a `User` instance
    - Test `to_dictionary(keys=["nonexistent"])` returns `{}`
    - Test `to_dictionary(keys=[])` returns `{}`
    - Test `to_dictionary()` with no keys arg returns the full dictionary (backward compatibility)
    - Test `to_dict(keys=...)` matches `to_dictionary(keys=...)`
    - Test `include_none=False` interaction: `to_dictionary(include_none=False, keys=["field_that_is_none"])` returns `{}`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.2, 2.3_

  - [ ]* 2.2 Write property test for key subset correctness
    - **Property 1: Key filtering produces the correct subset**
    - Use `hypothesis` to generate `User` instances and random key subsets (including non-existent keys)
    - Assert filtered dict keys == intersection of requested keys and full dict keys, and values match
    - File: `boto3-assist/tests/unit/dynamodb_tests/test_dictionary_key_filter_properties.py`
    - **Validates: Requirements 1.1, 1.2, 1.4, 3.2**

  - [ ]* 2.3 Write property test for None-keys backward compatibility
    - **Property 2: None-keys preserves backward compatibility**
    - Assert `to_dictionary(keys=None)` == `to_dictionary()` for any generated `User` instance
    - File: `boto3-assist/tests/unit/dynamodb_tests/test_dictionary_key_filter_properties.py`
    - **Validates: Requirements 1.3**

  - [ ]* 2.4 Write property test for to_dict / to_dictionary equivalence
    - **Property 3: to_dict and to_dictionary equivalence**
    - Assert `to_dict(keys=keys)` == `to_dictionary(keys=keys)` for any generated `User` and any `keys` value
    - File: `boto3-assist/tests/unit/dynamodb_tests/test_dictionary_key_filter_properties.py`
    - **Validates: Requirements 2.2, 2.3**

  - [ ]* 2.5 Write property test for filter-then-map round trip
    - **Property 4: Filter-then-map round trip**
    - For any `User` instance and any non-empty subset of its serialized keys, filter via `to_dictionary(keys=subset)` then `map()` onto a new `User` — assert each filtered attribute matches the original
    - File: `boto3-assist/tests/unit/dynamodb_tests/test_dictionary_key_filter_properties.py`
    - **Validates: Requirements 4.1**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The implementation is minimal: two method signature changes and a single dict comprehension
- Property tests use `hypothesis` (already in `requirements.dev.txt`)
- Test model: `User` from `tests/unit/dynamodb_tests/db_models/user_model.py`
