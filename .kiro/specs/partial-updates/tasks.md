# Implementation Plan: Partial Updates Feature

## Overview

This implementation plan breaks down the partial updates feature into discrete, actionable coding tasks. The feature adds a `save_partial()` method to `DynamoDBModelBase` and a new `PartialUpdateBuilder` class to enable efficient selective field updates without replacing entire items.

The implementation follows a logical progression:
1. Create the core builder class and data structures
2. Implement the main `update_item_partial()` method on DynamoDB
3. Add the `save_partial()` convenience method to DynamoDBModelBase
4. Write comprehensive unit tests for each component
5. Add property-based tests for correctness properties
6. Create integration tests
7. Final validation and checkpoint

## Tasks

- [-] 1. Create UpdateExpressionComponents data structure and PartialUpdateBuilder class
  - [ ] 1.1 Create `src/boto3_assist/dynamodb/partial_update_builder.py` with UpdateExpressionComponents dataclass
    - Define UpdateExpressionComponents with update_expression, expression_attribute_names, expression_attribute_values fields
    - Add docstrings and type hints
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [ ] 1.2 Implement PartialUpdateBuilder class initialization and core structure
    - Create PartialUpdateBuilder class with __init__ method
    - Initialize DynamoDBReservedWords instance for reserved keyword detection
    - Add docstrings and type hints
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 1.3 Implement _separate_operations() method
    - Separate fields into SET operations (non-None values) and REMOVE operations (CLEAR_FIELD sentinels)
    - Handle None values by excluding them from updates
    - Return tuple of (set_fields dict, remove_fields set)
    - _Requirements: 1.3, 1.4, 4.2_

  - [ ] 1.4 Implement _build_set_clause() method
    - Build SET clause with reserved keyword handling
    - Generate expression attribute names for reserved keywords
    - Generate expression attribute values for all fields
    - Return tuple of (set_clause_str, expression_attribute_names, expression_attribute_values)
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.3_

  - [ ] 1.5 Implement _build_remove_clause() method
    - Build REMOVE clause with reserved keyword handling
    - Generate expression attribute names for reserved keywords
    - Return tuple of (remove_clause_str, expression_attribute_names)
    - _Requirements: 3.1, 3.2, 3.3, 4.2_

  - [ ] 1.6 Implement build_update_expression() method
    - Orchestrate the expression building process
    - Call _separate_operations() to identify SET and REMOVE fields
    - Call _build_set_clause() and _build_remove_clause()
    - Combine clauses into final update expression
    - Return UpdateExpressionComponents with all components
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [ ] 1.7 Implement placeholder generation helper methods
    - Implement _get_placeholder_name(field_name) to generate #field_name placeholders
    - Implement _get_placeholder_value(field_name) to generate :field_name placeholders
    - _Requirements: 4.1, 4.6_

- [-] 2. Implement DynamoDB.update_item_partial() method
  - [ ] 2.1 Add update_item_partial() method signature to DynamoDB class
    - Define method with all parameters: item, table_name, fields_to_clear, condition_expression, expression_attribute_names, expression_attribute_values, return_values, source
    - Add comprehensive docstring with examples
    - Add type hints for all parameters and return value
    - _Requirements: 1.1, 1.2, 1.5, 1.6_

  - [ ] 2.2 Implement input validation in update_item_partial()
    - Validate table_name is provided (raise ValueError if missing)
    - Validate primary key fields are populated (raise ValueError if missing)
    - Validate return_values is one of: NONE, ALL_NEW, UPDATED_NEW, ALL_OLD, UPDATED_OLD
    - Validate fields_to_clear doesn't contain primary key or index fields
    - _Requirements: 1.5, 1.6, 9.1, 9.2, 9.3, 9.5_

  - [ ] 2.3 Implement model-to-dict conversion in update_item_partial()
    - Convert DynamoDBModelBase instances to dictionaries
    - Handle both dict and model inputs
    - Extract primary key fields for the update key
    - _Requirements: 1.1, 1.2_

  - [ ] 2.4 Implement field identification and filtering in update_item_partial()
    - Get non-None fields using to_resource_dictionary(include_none=False)
    - Exclude primary key fields (pk, sk)
    - Exclude index fields (gsi1_pk, gsi1_sk, etc.)
    - Apply fields_to_clear parameter
    - Validate at least one field is being updated (raise ValueError if none)
    - _Requirements: 1.1, 1.3, 1.4, 6.5, 9.2_

  - [ ] 2.5 Implement PartialUpdateBuilder integration in update_item_partial()
    - Create PartialUpdateBuilder instance
    - Call build_update_expression() with identified fields
    - Get UpdateExpressionComponents from builder
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [ ] 2.6 Implement expression attribute merging in update_item_partial()
    - Merge auto-generated expression_attribute_names with user-provided ones
    - Merge auto-generated expression_attribute_values with user-provided ones
    - Handle conflicts (auto-generated takes precedence for field names/values)
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 2.7 Implement DynamoDB.update_item() call in update_item_partial()
    - Call self.update_item() with generated expression and merged attributes
    - Pass condition_expression if provided
    - Pass return_values parameter
    - Pass source parameter for logging
    - Return response from update_item()
    - _Requirements: 1.1, 1.2, 5.1, 5.2, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 2.8 Implement error handling and logging in update_item_partial()
    - Log successful updates at INFO level with table name and field count
    - Catch and re-raise ValueError for validation errors
    - Catch and re-raise RuntimeError for condition expression failures
    - Catch and re-raise ClientError for DynamoDB errors
    - Add helpful error messages with context
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [-] 3. Implement DynamoDBModelBase.save_partial() method
  - [ ] 3.1 Add save_partial() method signature to DynamoDBModelBase
    - Define method with parameters: table_name, fields_to_clear, condition_expression, expression_attribute_names, expression_attribute_values, return_values
    - Add comprehensive docstring with examples
    - Add type hints for all parameters and return value
    - _Requirements: 1.1, 1.2, 1.5, 1.6_

  - [ ] 3.2 Implement save_partial() delegation to DynamoDB.update_item_partial()
    - Get DynamoDB instance (from context or create new one)
    - Call update_item_partial() with self as item and provided parameters
    - Return response from update_item_partial()
    - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.3, 6.4_

  - [ ] 3.3 Implement integration with merge() pattern
    - Ensure save_partial() works correctly after merge() is called
    - Verify only merged fields are updated
    - Verify model instance is not modified by save_partial()
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 4. Checkpoint - Ensure core implementation is complete
  - Verify all methods are implemented with correct signatures
  - Verify all type hints are in place
  - Verify all docstrings are complete
  - Run basic smoke tests to ensure no syntax errors
  - Ask the user if questions arise.

- [ ] 5. Write unit tests for PartialUpdateBuilder
  - [ ] 5.1 Create test file `tests/unit/dynamodb_tests/partial_update_builder_test.py`
    - Set up test class with setUp method
    - Create mock models for testing
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ] 5.2 Write tests for _separate_operations() method
    - Test populated fields are identified correctly
    - Test None values are excluded
    - Test CLEAR_FIELD sentinels are detected
    - Test primary keys are excluded
    - Test index fields are excluded
    - _Requirements: 1.3, 1.4, 4.2_

  - [ ] 5.3 Write tests for _build_set_clause() method
    - Test SET clause is correctly formatted
    - Test multiple fields are comma-separated
    - Test reserved keywords generate placeholders
    - Test non-reserved keywords don't generate placeholders
    - Test expression attribute names are correct
    - Test expression attribute values are correct
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.3_

  - [ ] 5.4 Write tests for _build_remove_clause() method
    - Test REMOVE clause is correctly formatted
    - Test multiple fields are comma-separated
    - Test reserved keywords generate placeholders
    - Test non-reserved keywords don't generate placeholders
    - Test expression attribute names are correct
    - _Requirements: 3.1, 3.2, 3.3, 4.2_

  - [ ] 5.5 Write tests for build_update_expression() method
    - Test complete expression generation with SET and REMOVE
    - Test expression with only SET operations
    - Test expression with only REMOVE operations
    - Test empty expression raises error
    - Test all components are returned correctly
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [ ] 5.6 Write tests for placeholder generation methods
    - Test _get_placeholder_name() generates correct format
    - Test _get_placeholder_value() generates correct format
    - _Requirements: 4.1, 4.6_

- [x] 6. Write unit tests for DynamoDB.update_item_partial()
  - [ ] 6.1 Create test file `tests/unit/dynamodb_tests/dynamodb_partial_update_test.py`
    - Set up test class with mock DynamoDB
    - Create test models and data
    - _Requirements: 1.1, 1.2, 1.5, 1.6_

  - [ ] 6.2 Write validation tests
    - Test missing table_name raises ValueError
    - Test missing primary key raises ValueError
    - Test invalid return_values raises ValueError
    - Test fields_to_clear with primary key raises ValueError
    - Test no fields to update raises ValueError
    - _Requirements: 1.5, 1.6, 9.1, 9.2, 9.3, 9.5_

  - [ ] 6.3 Write field identification tests
    - Test non-None fields are identified
    - Test None values are excluded
    - Test primary keys are excluded
    - Test index fields are excluded
    - Test fields_to_clear are identified
    - _Requirements: 1.1, 1.3, 1.4, 6.5_

  - [ ] 6.4 Write expression generation tests
    - Test correct update expression is generated
    - Test expression attribute names are merged correctly
    - Test expression attribute values are merged correctly
    - Test user-provided attributes are preserved
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.6_

  - [ ] 6.5 Write conditional write tests
    - Test condition_expression is passed to update_item()
    - Test condition failure raises RuntimeError
    - Test condition success updates item
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 6.6 Write return values tests
    - Test return_values="NONE" returns minimal response
    - Test return_values="ALL_NEW" returns complete item
    - Test return_values="UPDATED_NEW" returns only updated fields
    - Test return_values="ALL_OLD" returns item before update
    - Test return_values="UPDATED_OLD" returns updated fields before update
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 6.7 Write error handling and logging tests
    - Test successful updates are logged at INFO level
    - Test validation errors are logged and re-raised
    - Test DynamoDB errors are logged and re-raised
    - Test error messages are helpful and descriptive
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 7. Write unit tests for DynamoDBModelBase.save_partial()
  - [x] 7.1 Create test file `tests/unit/dynamodb_tests/dynamodb_model_save_partial_test.py`
    - Set up test class with mock DynamoDB
    - Create test models
    - _Requirements: 1.1, 1.2, 1.5, 1.6_

  - [x] 7.2 Write basic save_partial() tests
    - Test save_partial() calls update_item_partial() correctly
    - Test parameters are passed through correctly
    - Test response is returned correctly
    - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.3, 6.4_

  - [x] 7.3 Write integration tests with merge() pattern
    - Test save_partial() works after merge()
    - Test only merged fields are updated
    - Test model instance is not modified
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 7.4 Write integration tests with map() pattern
    - Test save_partial() works after map()
    - Test loaded item can be partially updated
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 8. Write property-based tests for correctness properties
  - [x] 8.1 Create test file `tests/unit/dynamodb_tests/partial_update_properties_test.py`
    - Set up Hypothesis test class
    - Create strategies for generating test data
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3, 4.6_

  - [x] 8.2 Write property test for Idempotence of Partial Updates
    - **Property 1: Idempotence of Partial Updates**
    - **Validates: Requirements 1.1, 1.2, 6.4**
    - Generate model with random field values
    - Call save_partial() twice with same fields
    - Verify item state is identical after both calls
    - _Requirements: 1.1, 1.2, 6.4_

  - [x] 8.3 Write property test for Selective Field Update Correctness
    - **Property 2: Selective Field Update Correctness**
    - **Validates: Requirements 1.1, 1.3, 2.1, 2.2, 6.1**
    - Create item with known values for all fields
    - Load item and populate only subset of fields
    - Call save_partial()
    - Verify only populated fields changed, others unchanged
    - _Requirements: 1.1, 1.3, 2.1, 2.2, 6.1_

  - [x] 8.4 Write property test for Reserved Keyword Handling Correctness
    - **Property 3: Reserved Keyword Handling Correctness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    - For each DynamoDB reserved keyword
    - Create model with that field
    - Populate field and call save_partial()
    - Verify field was updated correctly in DynamoDB
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 8.5 Write property test for CLEAR_FIELD Sentinel Correctness
    - **Property 4: CLEAR_FIELD Sentinel Correctness**
    - **Validates: Requirements 1.3, 1.4, 4.2**
    - Generate field values including None and CLEAR_FIELD
    - Call save_partial() with fields_to_clear
    - Verify CLEAR_FIELD generates REMOVE operations
    - Verify None values are excluded
    - _Requirements: 1.3, 1.4, 4.2_

  - [x] 8.6 Write property test for Primary Key Immutability
    - **Property 5: Primary Key Immutability**
    - **Validates: Requirements 6.5, 9.5**
    - Generate primary key values
    - Attempt to update primary key fields
    - Verify primary keys are not updated in DynamoDB
    - _Requirements: 6.5, 9.5_

  - [x] 8.7 Write property test for Update Expression Syntax Correctness
    - **Property 6: Update Expression Syntax Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.6**
    - Generate field sets
    - Generate update expressions
    - Verify expressions can be executed without syntax errors
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [x] 8.8 Write property test for Field Filtering Correctness
    - **Property 7: Field Filtering Correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3**
    - Generate field sets and filter combinations
    - Verify only correct fields are updated based on filters
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 8.9 Write property test for Model Instance Immutability
    - **Property 8: Model Instance Immutability**
    - **Validates: Requirements 6.3**
    - Capture model state before save_partial()
    - Call save_partial()
    - Verify model state is unchanged
    - _Requirements: 6.3_

- [x] 9. Write integration tests
  - [x] 9.1 Create test file `tests/integration/dynamodb_tests/partial_update_integration_test.py`
    - Set up integration test class with real DynamoDB (or moto)
    - Create test table and models
    - _Requirements: 1.1, 1.2, 1.5, 1.6_

  - [x] 9.2 Write integration tests for basic partial updates
    - Test partial update works with real DynamoDB
    - Test only specified fields are updated
    - Test other fields remain unchanged
    - _Requirements: 1.1, 1.3, 2.1, 2.2, 6.1_

  - [x] 9.3 Write integration tests for field clearing
    - Test fields_to_clear removes fields correctly
    - Test multiple fields can be cleared
    - Test cleared fields are removed from item
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 9.4 Write integration tests for reserved keywords
    - Test reserved keyword fields are updated correctly
    - Test expression attribute names are generated correctly
    - Test multiple reserved keywords work together
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 9.5 Write integration tests for conditional writes
    - Test conditional write succeeds when condition is met
    - Test conditional write fails when condition is not met
    - Test condition failure raises RuntimeError
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 9.6 Write integration tests for return values
    - Test return_values="ALL_NEW" returns complete item
    - Test return_values="UPDATED_NEW" returns only updated fields
    - Test return_values="ALL_OLD" returns item before update
    - Test return_values="UPDATED_OLD" returns updated fields before update
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 9.7 Write integration tests for error scenarios
    - Test missing primary key raises error
    - Test invalid table name raises error
    - Test serialization errors are handled
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 9.8 Write integration tests for throttling and retries
    - Test throttling errors are retried
    - Test retries succeed after throttling
    - Test retry logging works correctly
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 10. Checkpoint - Ensure all tests pass
  - Run all unit tests and verify they pass
  - Run all property-based tests and verify they pass
  - Run all integration tests and verify they pass
  - Verify code coverage is adequate (>90% for new code)
  - Ask the user if questions arise.

- [x] 11. Documentation and examples
  - [x] 11.1 Add docstring examples to save_partial() method
    - Add basic usage example
    - Add field clearing example
    - Add conditional write example
    - Add return values example
    - Add merge() pattern example
    - _Requirements: 1.1, 1.2, 6.1, 6.2_

  - [x] 11.2 Add docstring examples to update_item_partial() method
    - Add basic usage example
    - Add field clearing example
    - Add conditional write example
    - Add return values example
    - _Requirements: 1.1, 1.2, 5.1, 5.2, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 11.3 Create usage guide document
    - Document basic usage patterns
    - Document field clearing patterns
    - Document conditional write patterns
    - Document error handling patterns
    - Document integration with merge() and map()
    - _Requirements: 1.1, 1.2, 6.1, 6.2_

- [x] 12. Final checkpoint - Ensure all tests pass and code is ready
  - Run full test suite one final time
  - Verify all tests pass
  - Verify code coverage is adequate
  - Verify no linting errors
  - Verify type hints are correct
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end functionality
- All code should follow existing project conventions and patterns
- All code should include comprehensive docstrings and type hints
- All code should be tested before moving to the next task
