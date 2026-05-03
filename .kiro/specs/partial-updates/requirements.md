# Partial Updates Feature - Requirements Document

## Introduction

The boto3-assist library provides a well-designed ORM pattern for DynamoDB models through `DynamoDBModelBase` and the `DynamoDB` class. Currently, users can perform full item replacements via `save()` or manual update expressions via `update_item()`. However, there is no integrated pattern for selectively updating only the fields that have been modified in a model instance, which is a common real-world use case.

This feature adds the ability to perform selective field updates by:
1. Populating only the fields that need to be changed in a model instance
2. Using a new `save_partial()` method that automatically generates update expressions
3. Mapping only populated fields to DynamoDB update expressions
4. Handling reserved keywords transparently
5. Supporting conditional writes and validation

This bridges the gap between the high-level ORM pattern and low-level update expressions, making partial updates as convenient as full saves.

## Glossary

- **Partial Update**: An update operation that modifies only specific fields of an item, leaving other fields unchanged.
- **Update Expression**: A DynamoDB expression string that specifies which attributes to modify (SET, ADD, REMOVE, DELETE operations).
- **Populated Field**: A model field that has been explicitly set to a non-None value (or explicitly cleared using CLEAR_FIELD).
- **Reserved Keyword**: DynamoDB attribute names that conflict with DynamoDB reserved words (e.g., "status", "name", "type") and require expression attribute name mappings.
- **Merge Strategy**: An enum defining how to handle field conflicts when merging updates (NON_NULL_WINS, UPDATES_WIN, EXISTING_WINS).
- **Expression Attribute Names**: A mapping from placeholder names (e.g., "#status") to actual attribute names, used to handle reserved keywords.
- **Expression Attribute Values**: A mapping from placeholder values (e.g., ":status_value") to actual values, used in update expressions.
- **Selective Model Mapping**: The process of identifying which fields in a model have been populated and mapping only those to update expression components.
- **Idempotent Update**: An update operation that produces the same result when applied multiple times.
- **Atomic Counter**: A numeric field that is incremented or decremented atomically using the ADD operation.
- **Conditional Write**: An update that only succeeds if a specified condition is met (e.g., version check, attribute existence).

## Requirements

### Requirement 1: Partial Update Method on DynamoDBModelBase

**User Story:** As a developer, I want to save only the fields I've modified in a model instance, so that I can perform efficient partial updates without replacing the entire item.

#### Acceptance Criteria

1. WHEN a model instance has only some fields populated, THE `DynamoDBModelBase` SHALL provide a `save_partial()` method that updates only those fields.
2. WHEN `save_partial()` is called, THE method SHALL generate an appropriate update expression automatically.
3. WHEN a field is set to None, THE `save_partial()` method SHALL treat it as "not populated" and exclude it from the update (unless explicitly marked with CLEAR_FIELD).
4. WHERE a field is explicitly marked with CLEAR_FIELD sentinel, THE `save_partial()` method SHALL include a REMOVE operation to clear that field to None.
5. WHEN `save_partial()` is called without a table_name, THE method SHALL raise a ValueError with a clear message.
6. WHEN `save_partial()` is called, THE method SHALL require the primary key fields to be populated, and raise ValueError if they are missing.

### Requirement 2: Field Clearing

**User Story:** As a developer, I want to explicitly clear (remove) specific fields from an item, so that I can remove data that's no longer needed.

#### Acceptance Criteria

1. WHEN `save_partial()` is called with `fields_to_clear` parameter, THE method SHALL remove the specified fields from the item.
2. WHEN a field is in `fields_to_clear`, THE method SHALL generate a REMOVE operation for that field.
3. WHEN `fields_to_clear` contains field names that don't exist on the model, THE method SHALL silently ignore them (no error).
4. WHEN `fields_to_clear` contains primary key or index fields, THE method SHALL raise ValueError indicating these fields cannot be cleared.
5. WHEN `fields_to_clear` is an empty list, THE method SHALL not generate any REMOVE operations.

### Requirement 3: Reserved Keyword Handling

**User Story:** As a developer, I want partial updates to work seamlessly with reserved keywords like "status", "name", and "type", so that I don't have to manually manage expression attribute names.

#### Acceptance Criteria

1. WHEN a model has a field that is a DynamoDB reserved keyword, THE `save_partial()` method SHALL automatically generate the appropriate expression attribute names mapping.
2. WHEN generating expression attribute names, THE method SHALL use the pattern `#field_name` for placeholders.
3. WHEN a field name is a reserved keyword, THE method SHALL include it in the ExpressionAttributeNames parameter automatically.
4. WHEN a field name is not a reserved keyword, THE method SHALL NOT include it in ExpressionAttributeNames.
5. WHEN the update expression is built, THE method SHALL use the placeholder names (e.g., `#status`) instead of the actual reserved keywords.

### Requirement 4: Update Expression Generation

**User Story:** As a developer, I want the library to automatically generate correct DynamoDB update expressions, so that I don't have to manually construct them.

#### Acceptance Criteria

1. WHEN `save_partial()` processes fields, THE method SHALL generate a SET clause for all populated fields that are not being removed.
2. WHEN `save_partial()` encounters a CLEAR_FIELD sentinel, THE method SHALL generate a REMOVE clause for that field.
3. WHEN multiple fields are being updated, THE method SHALL combine them into a single update expression with proper comma separation.
4. WHEN a field is an atomic counter (integer type with special semantics), THE method SHALL support ADD operations (future enhancement, see Requirement 7).
5. WHEN the update expression is empty (no fields to update), THE method SHALL raise ValueError with a clear message.
6. WHEN expression attribute values are generated, THE method SHALL use the pattern `:field_name` for placeholders.

### Requirement 5: Conditional Writes

**User Story:** As a developer, I want to support conditional partial updates, so that I can implement optimistic locking and prevent race conditions.

#### Acceptance Criteria

1. WHEN `save_partial()` is called with `condition_expression` parameter, THE method SHALL include the condition in the update operation.
2. WHEN a condition expression is provided, THE method SHALL pass it to the underlying `update_item()` call.
3. WHEN a condition expression fails, THE method SHALL raise RuntimeError with a descriptive message indicating the condition failed.
4. WHEN `condition_expression` is a string, THE method SHALL pass it directly to DynamoDB.
5. WHEN `condition_expression` is a boto3 ConditionBase object, THE method SHALL convert it to a string for the update operation.
6. WHERE `fail_if_changed` option is provided, THE method SHALL generate a condition expression that checks the version field hasn't changed (future enhancement, see Requirement 8).

### Requirement 6: Integration with Existing Patterns

**User Story:** As a developer, I want partial updates to work seamlessly with the existing ORM patterns, so that I can use them alongside `save()`, `merge()`, and `update_item()`.

#### Acceptance Criteria

1. WHEN a model is loaded via `map()` and then partially updated via `save_partial()`, THE operation SHALL work correctly without conflicts.
2. WHEN a model is updated via `merge()` and then saved via `save_partial()`, THE method SHALL only update the merged fields.
3. WHEN `save_partial()` is called, THE method SHALL NOT modify the model instance (read-only operation on the model).
4. WHEN `save_partial()` is called multiple times with different field sets, THE method SHALL generate correct update expressions each time.
5. WHEN a model has indexes defined, THE `save_partial()` method SHALL NOT attempt to update index fields (they are read-only).
6. WHEN a model has TTL set, THE `save_partial()` method SHALL include the TTL field in the update if it has been modified.

### Requirement 7: Atomic Counter Support (Optional)

**User Story:** As a developer, I want to increment or decrement numeric fields atomically, so that I can safely update counters in concurrent scenarios.

#### Acceptance Criteria

1. WHERE a field is marked as an atomic counter, THE `save_partial()` method SHALL support ADD operations instead of SET.
2. WHEN an atomic counter field is updated, THE method SHALL generate an ADD clause instead of a SET clause.
3. WHEN multiple atomic counters are being updated, THE method SHALL combine them into a single ADD clause.
4. WHEN both regular fields and atomic counters are being updated, THE method SHALL generate both SET and ADD clauses in the same update expression.

### Requirement 8: Optimistic Locking Support (Optional)

**User Story:** As a developer, I want to implement optimistic locking for partial updates, so that I can prevent lost updates in concurrent scenarios.

#### Acceptance Criteria

1. WHERE a model has a version field, THE `save_partial()` method SHALL support a `fail_if_changed` parameter.
2. WHEN `fail_if_changed=True` is provided, THE method SHALL automatically generate a condition expression that checks the version field.
3. WHEN the version check fails, THE method SHALL raise RuntimeError indicating the item has been modified.
4. WHEN the version check succeeds, THE method SHALL automatically increment the version field in the update expression.

### Requirement 9: Validation of Partial Updates

**User Story:** As a developer, I want validation to ensure partial updates are safe and correct, so that I can catch errors early.

#### Acceptance Criteria

1. WHEN `save_partial()` is called, THE method SHALL validate that the primary key fields are populated.
2. WHEN `save_partial()` is called, THE method SHALL validate that at least one field is being updated.
3. WHEN `save_partial()` is called with invalid parameters, THE method SHALL raise ValueError with a descriptive message.
4. WHEN a field value cannot be serialized to DynamoDB format, THE method SHALL raise RuntimeError with details about the field.
5. WHEN `save_partial()` is called, THE method SHALL validate that index fields are not being updated (they are read-only).

### Requirement 10: Return Values and Feedback

**User Story:** As a developer, I want to get feedback about what was updated, so that I can verify the operation succeeded and optionally get the updated item.

#### Acceptance Criteria

1. WHEN `save_partial()` is called with `return_values="NONE"` (default), THE method SHALL return an empty dict or minimal response.
2. WHEN `save_partial()` is called with `return_values="ALL_NEW"`, THE method SHALL return the complete updated item.
3. WHEN `save_partial()` is called with `return_values="UPDATED_NEW"`, THE method SHALL return only the fields that were updated.
4. WHEN `save_partial()` is called with `return_values="ALL_OLD"`, THE method SHALL return the complete item before the update.
5. WHEN `save_partial()` is called with `return_values="UPDATED_OLD"`, THE method SHALL return only the fields that were updated, before the update.

### Requirement 11: Error Handling and Logging

**User Story:** As a developer, I want clear error messages and logging, so that I can debug issues quickly.

#### Acceptance Criteria

1. WHEN `save_partial()` fails due to a condition expression, THE method SHALL raise RuntimeError with the condition that failed.
2. WHEN `save_partial()` fails due to a validation error, THE method SHALL raise ValueError with details about what was invalid.
3. WHEN `save_partial()` fails due to a DynamoDB error, THE method SHALL log the error and re-raise it with context.
4. WHEN `save_partial()` succeeds, THE method SHALL log the operation at INFO level with table name and field count.
5. WHEN `save_partial()` is called with invalid parameters, THE method SHALL provide helpful error messages suggesting correct usage.

### Requirement 12: Throttling and Retry Behavior

**User Story:** As a developer, I want partial updates to handle DynamoDB throttling gracefully, so that my application remains resilient.

#### Acceptance Criteria

1. WHEN `save_partial()` encounters a throttling error, THE method SHALL retry with exponential backoff (same as `save()` and `update_item()`).
2. WHEN retries are exhausted, THE method SHALL raise ClientError with the original error details.
3. WHEN `save_partial()` succeeds after a retry, THE method SHALL log the retry attempt.

## Correctness Properties

### Property 1: Idempotence of Partial Updates

**Description:** Applying the same partial update twice should produce the same result as applying it once.

**Property:** For any model instance `m` with fields `f1, f2, ..., fn` populated, calling `save_partial()` twice with the same field set should result in the same item state in DynamoDB.

**Rationale:** This ensures that network retries don't cause duplicate updates or unexpected state changes.

**Test Strategy:** Property-based test with generated field updates. Generate a model with random field values, call `save_partial()`, verify the item state, call `save_partial()` again with the same fields, verify the item state is identical.

### Property 2: Selective Field Update Correctness

**Description:** Only the specified fields should be updated; all other fields should remain unchanged.

**Property:** For any model instance with fields `{f1, f2, f3, f4}` where only `{f1, f2}` are populated, after `save_partial()`, the item in DynamoDB should have `f1` and `f2` updated to the new values, while `f3` and `f4` retain their original values.

**Rationale:** This is the core correctness property for partial updates. Updating unintended fields would be a critical bug.

**Test Strategy:** Property-based test with generated field sets. Create an item with known values for all fields, load it, populate only a subset of fields with new values, call `save_partial()`, verify only the populated fields changed and others remained the same.

### Property 3: Reserved Keyword Handling Correctness

**Description:** Fields with reserved keyword names should be updated correctly without manual expression attribute name management.

**Property:** For any model with a field named with a reserved keyword (e.g., "status"), calling `save_partial()` should generate the correct expression attribute names mapping and update the field correctly.

**Rationale:** Incorrect handling of reserved keywords is a common source of bugs. This property ensures the library handles them transparently.

**Test Strategy:** Property-based test with all DynamoDB reserved keywords. For each reserved keyword, create a model with that field, populate it, call `save_partial()`, verify the field was updated correctly in DynamoDB.

### Property 4: CLEAR_FIELD Sentinel Correctness

**Description:** Using CLEAR_FIELD should remove a field (set it to None), while None values should be ignored.

**Property:** For any model instance where a field is set to CLEAR_FIELD, calling `save_partial()` should generate a REMOVE operation for that field. For fields set to None, they should be excluded from the update.

**Rationale:** This property ensures the CLEAR_FIELD sentinel works as intended and doesn't conflict with None values.

**Test Strategy:** Property-based test with generated field values including None and CLEAR_FIELD. Verify that CLEAR_FIELD generates REMOVE operations and None values are excluded.

### Property 5: Primary Key Immutability

**Description:** Primary key fields should never be updated via `save_partial()`.

**Property:** For any model instance, attempting to update primary key fields via `save_partial()` should either be silently ignored or raise an error, but never actually update the primary key in DynamoDB.

**Rationale:** Updating primary keys would break the item's identity and is a critical error.

**Test Strategy:** Property-based test with generated primary key values. Attempt to update primary key fields, verify they are not updated in DynamoDB.

### Property 6: Conditional Write Correctness

**Description:** Conditional writes should only succeed when the condition is met.

**Property:** For any model instance with a condition expression, `save_partial()` should only update the item if the condition is satisfied. If the condition fails, the item should remain unchanged.

**Rationale:** Conditional writes are essential for optimistic locking and preventing race conditions.

**Test Strategy:** Property-based test with generated condition expressions. Create items with known state, apply conditional updates with conditions that should pass and fail, verify the item is updated only when the condition passes.

### Property 7: Update Expression Syntax Correctness

**Description:** Generated update expressions should be syntactically valid DynamoDB expressions.

**Property:** For any model instance with populated fields, the generated update expression should be a valid DynamoDB update expression that can be executed without syntax errors.

**Rationale:** Invalid update expressions would cause DynamoDB errors and failed updates.

**Test Strategy:** Property-based test with generated field sets. Generate update expressions, verify they can be executed against DynamoDB without syntax errors.

### Property 8: Decimal Conversion Correctness

**Description:** Numeric values should be correctly converted to Decimal for DynamoDB storage.

**Property:** For any model instance with numeric fields, calling `save_partial()` should convert them to Decimal format for DynamoDB, and retrieving the item should convert them back to native Python types correctly.

**Rationale:** DynamoDB requires Decimal types for numeric values, and incorrect conversion can cause data loss or type errors.

**Test Strategy:** Property-based test with generated numeric values (int, float). Call `save_partial()`, retrieve the item, verify the numeric values are correct.

### Property 9: Field Filtering Correctness

**Description:** `include_fields` and `exclude_fields` parameters should correctly filter which fields are updated.

**Property:** For any model instance with fields `{f1, f2, f3, f4}` and `include_fields={f1, f2}`, only `f1` and `f2` should be updated. For `exclude_fields={f3, f4}`, all fields except `f3` and `f4` should be updated.

**Rationale:** Incorrect field filtering could lead to unintended updates or missed updates.

**Test Strategy:** Property-based test with generated field sets and filter combinations. Verify that only the correct fields are updated based on the filters.

### Property 10: Return Values Correctness

**Description:** The `return_values` parameter should return the correct data based on the specified option.

**Property:** For any model instance with `return_values="ALL_NEW"`, the response should contain all attributes of the updated item. For `return_values="UPDATED_NEW"`, only the updated attributes should be returned.

**Rationale:** Incorrect return values could cause the caller to miss important data or receive unexpected data.

**Test Strategy:** Property-based test with generated field updates and return_values options. Verify the response contains the correct data for each return_values option.

## Constraints and Assumptions

### Constraints

1. **Primary Key Immutability**: Primary key fields (pk, sk) cannot be updated via `save_partial()`. Attempting to do so should raise an error or be silently ignored.

2. **Index Field Immutability**: Fields used in Global Secondary Indexes (GSI) or Local Secondary Indexes (LSI) cannot be updated via `save_partial()` if they are part of the index key. Attempting to do so should raise an error.

3. **Single Table Operation**: `save_partial()` operates on a single item in a single table. Batch operations are out of scope for this feature.

4. **DynamoDB Limits**: The generated update expression must comply with DynamoDB limits:
   - Maximum 25 attributes in a single update expression
   - Maximum expression attribute names and values as per DynamoDB limits
   - Item size must not exceed 400 KB after the update

5. **Reserved Keyword Handling**: The library must handle all DynamoDB reserved keywords transparently. A comprehensive list of reserved keywords must be maintained.

6. **Decimal Conversion**: All numeric values must be converted to Decimal for DynamoDB storage. The library must handle this automatically.

### Assumptions

1. **Model Initialization**: It is assumed that models are properly initialized with all fields set to None or a default value before being used with `save_partial()`.

2. **Primary Key Availability**: It is assumed that the primary key fields are always populated before calling `save_partial()`. The method will validate this and raise an error if they are missing.

3. **Table Existence**: It is assumed that the DynamoDB table exists and is accessible. The method will not create tables.

4. **Permissions**: It is assumed that the AWS credentials have the necessary permissions to perform UpdateItem operations on the table.

5. **Field Naming**: It is assumed that model field names match the DynamoDB attribute names (or are properly mapped via the serialization layer).

6. **Serialization Compatibility**: It is assumed that all model fields can be serialized to DynamoDB format using the existing serialization utilities.

7. **Backward Compatibility**: The new `save_partial()` method should not break existing code that uses `save()`, `merge()`, or `update_item()`.

## Out of Scope

The following items are explicitly out of scope for this feature:

1. **Batch Partial Updates**: Updating multiple items in a single batch operation. This would be a separate feature.

2. **Transactional Partial Updates**: Using partial updates within DynamoDB transactions. This would require integration with the transaction layer.

3. **Stream Processing**: Triggering DynamoDB Streams or Lambda functions based on partial updates. This is handled by DynamoDB itself.

4. **Global Tables**: Replication to Global Tables. This is handled by DynamoDB itself.

5. **TTL Management**: Automatic TTL field management beyond what's already supported in the model.

6. **Encryption**: Field-level encryption. This is handled by DynamoDB encryption at rest.

7. **Audit Logging**: Automatic audit trail of changes. This would be a separate feature.

8. **Schema Validation**: Complex schema validation beyond basic type checking. This is out of scope.

## Success Criteria

The feature will be considered successful when:

1. ✅ A `save_partial()` method is implemented on `DynamoDBModelBase` that generates correct update expressions.

2. ✅ Reserved keywords are handled transparently without requiring manual expression attribute name management.

3. ✅ Field filtering via `include_fields` and `exclude_fields` works correctly.

4. ✅ Conditional writes are supported with proper error handling.

5. ✅ All correctness properties pass with property-based tests.

6. ✅ Integration tests verify the feature works with real DynamoDB (or moto).

7. ✅ Documentation and examples are provided showing common use cases.

8. ✅ Backward compatibility is maintained with existing code.

9. ✅ Performance is comparable to manual `update_item()` calls.

10. ✅ Error messages are clear and helpful for debugging.
