# Partial Updates Feature - Design Document

## Overview

The partial updates feature adds a `save_partial()` method to `DynamoDBModelBase` that enables efficient selective field updates without replacing entire items. This design bridges the gap between the high-level ORM pattern and low-level DynamoDB update expressions.

### Key Design Goals

1. **Simplicity**: Developers populate only the fields they want to update and call `save_partial()`
2. **Transparency**: Reserved keywords are handled automatically without manual expression attribute name management
3. **Flexibility**: Support field filtering, conditional writes, and various return value options
4. **Consistency**: Integrate seamlessly with existing patterns (`map()`, `merge()`, `update_item()`)
5. **Safety**: Validate inputs, protect primary keys and index fields, provide clear error messages

## Architecture

### High-Level Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    DynamoDBModelBase                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  save_partial(table_name, include_fields, exclude_fields)   │
│  │  ├─ Validate inputs (primary keys, table name)              │
│  │  ├─ Identify populated fields                               │
│  │  ├─ Apply field filters (include/exclude)                   │
│  │  ├─ Delegate to PartialUpdateBuilder                        │
│  │  └─ Call DynamoDB.update_item() with generated expression   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PartialUpdateBuilder (NEW)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  build_update_expression(model, fields_to_update)           │
│  │  ├─ Separate fields into SET and REMOVE operations         │
│  │  ├─ Handle reserved keywords                                │
│  │  ├─ Generate expression attribute names                     │
│  │  ├─ Generate expression attribute values                    │
│  │  └─ Return UpdateExpressionComponents                       │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           DynamoDBReservedWords (EXISTING)                       │
│  ├─ is_reserved_word(word)                                      │
│  └─ transform_attributes(field_names)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DynamoDB.update_item()                          │
│  ├─ Execute update expression with retry logic                  │
│  ├─ Handle conditional check failures                           │
│  └─ Return response with optional attributes                    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Model instance with populated fields, optional filters, optional conditions
2. **Validation**: Check primary keys, table name, field filters
3. **Field Identification**: Determine which fields are populated (not None, or explicitly CLEAR_FIELD)
4. **Expression Generation**: Build SET/REMOVE clauses with reserved keyword handling
5. **DynamoDB Call**: Execute update_item() with generated expression
6. **Output**: Response with optional attributes based on return_values parameter

## Components and Interfaces

### 1. DynamoDB.update_item_partial() Method

**Location**: `src/boto3_assist/dynamodb/dynamodb.py`

**Signature**:
```python
def update_item_partial(
    self,
    item: Union[Dict[str, Any], DynamoDBModelBase],
    table_name: str,
    fields_to_clear: Optional[Set[str] | List[str]] = None,
    condition_expression: Optional[str] = None,
    expression_attribute_names: Optional[Dict[str, str]] = None,
    expression_attribute_values: Optional[Dict[str, Any]] = None,
    return_values: str = "NONE",
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform a partial update on an item in DynamoDB using only populated fields.

    This is a convenience method that automatically generates an UpdateItem expression
    from a model or dictionary. Only non-None fields are updated (SET operations).
    Fields specified in fields_to_clear are removed (REMOVE operations).
    Primary key fields and index fields are protected from updates.

    Args:
        item: Item to update. Can be a dictionary or DynamoDBModelBase instance.
            Must include all primary key attributes.
        table_name: DynamoDB table name
        fields_to_clear: Optional set of field names to remove from the item
        condition_expression: Optional condition that must be satisfied
        expression_attribute_names: Additional attribute name mappings (merged with auto-generated)
        expression_attribute_values: Additional value mappings (merged with auto-generated)
        return_values: What to return ("NONE", "ALL_NEW", "UPDATED_NEW", "ALL_OLD", "UPDATED_OLD")
        source: Optional identifier for logging/tracking

    Returns:
        DynamoDB response dict with optional Attributes based on return_values

    Raises:
        ValueError: If table_name is missing or primary keys not populated
        RuntimeError: If condition expression fails or serialization error occurs
        ClientError: For DynamoDB errors

    Examples:
        >>> user = User()
        >>> user.id = "user-123"
        >>> user.name = "John Doe"
        >>> user.email = "john@example.com"
        >>> db = DynamoDB()
        >>> # Only name and email are updated (id is primary key)
        >>> response = db.update_item_partial(item=user, table_name="users")

        >>> # Clear specific fields
        >>> response = db.update_item_partial(
        ...     item=user,
        ...     table_name="users",
        ...     fields_to_clear={"temp_field", "description"}
        ... )
    """
```

**Responsibilities**:
- Validate inputs (table_name, primary keys)
- Convert model to dictionary if needed
- Identify non-None fields using field introspection
- Exclude primary key and index fields
- Delegate to PartialUpdateBuilder for expression generation
- Call DynamoDB.update_item() with generated expression
- Handle errors and logging

### 2. PartialUpdateBuilder Class (NEW)

**Location**: `src/boto3_assist/dynamodb/partial_update_builder.py`

**Purpose**: Encapsulates the logic for building update expressions from model fields

**Key Methods**:

```python
class PartialUpdateBuilder:
    """Builds DynamoDB update expressions for partial updates."""

    def __init__(self, model: DynamoDBModelBase):
        """Initialize with a model instance."""
        self.model = model
        self.reserved_words = DynamoDBReservedWords()

    def build_update_expression(
        self,
        fields_to_update: Dict[str, Any],
    ) -> UpdateExpressionComponents:
        """
        Build update expression components from fields to update.

        Args:
            fields_to_update: Dict of {field_name: field_value} to update

        Returns:
            UpdateExpressionComponents with expression, names, and values
        """

    def _separate_operations(
        self,
        fields_to_update: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Set[str]]:
        """
        Separate fields into SET operations and REMOVE operations.

        Returns:
            (set_fields, remove_fields) where:
            - set_fields: {field_name: value} for SET clause
            - remove_fields: {field_name} for REMOVE clause
        """

    def _build_set_clause(
        self,
        set_fields: Dict[str, Any],
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Build SET clause with reserved keyword handling.

        Returns:
            (set_clause_str, expression_attribute_names, expression_attribute_values)
        """

    def _build_remove_clause(
        self,
        remove_fields: Set[str],
    ) -> Tuple[str, Dict[str, str]]:
        """
        Build REMOVE clause with reserved keyword handling.

        Returns:
            (remove_clause_str, expression_attribute_names)
        """

    def _get_placeholder_name(self, field_name: str) -> str:
        """Get expression attribute name placeholder for a field."""

    def _get_placeholder_value(self, field_name: str) -> str:
        """Get expression attribute value placeholder for a field."""
```

**Data Structure**:

```python
@dataclass
class UpdateExpressionComponents:
    """Components of a DynamoDB update expression."""

    update_expression: str
    """The complete update expression (e.g., "SET #name = :name REMOVE temp_field")"""

    expression_attribute_names: Dict[str, str]
    """Mapping of placeholders to actual attribute names (e.g., {"#status": "status"})"""

    expression_attribute_values: Dict[str, Any]
    """Mapping of placeholders to values (e.g., {":name": "John"})"""
```

### 3. Field Population Tracking

**Strategy**: Automatic detection of non-None fields at call time

**Algorithm**:
1. Get all model attributes using `to_resource_dictionary(include_none=False)`
2. This automatically excludes None values
3. Exclude primary key fields (pk, sk)
4. Exclude index fields (gsi1_pk, gsi1_sk, etc.)
5. Remaining fields are sent as SET operations
6. Fields in `fields_to_clear` are sent as REMOVE operations

**Rationale**:
- Simple and intuitive: non-None fields are automatically updated
- No need to track state during model initialization
- Works naturally with existing patterns
- Backward compatible with existing code
- Optional `fields_to_clear` for explicit field removal

**Implementation**:
```python
def _get_fields_to_update(self) -> Dict[str, Any]:
    """
    Get non-None fields that should be updated.

    Returns dict of {field_name: field_value} for all non-None fields,
    excluding primary key and index fields.
    """
    # Get dict without None values and without indexes
    fields = self.to_resource_dictionary(include_none=False, include_indexes=False)

    # Remove primary key fields
    pk_name = self.indexes.primary.partition_key.attribute_name
    sk_name = self.indexes.primary.sort_key.attribute_name
    fields.pop(pk_name, None)
    fields.pop(sk_name, None)

    # Remove GSI key fields
    for gsi in self.indexes.secondaries.values():
        fields.pop(gsi.partition_key.attribute_name, None)
        fields.pop(gsi.sort_key.attribute_name, None)

    return fields
```

## Update Expression Generation Algorithm

### Step 1: Identify Fields to Update

```
Input: Model instance
Output: Dict[field_name, field_value]

1. Get all non-None model attributes (excluding None)
2. Remove primary key fields (pk, sk)
3. Remove index fields (gsi1_pk, gsi1_sk, etc.)
4. Return remaining fields
```

### Step 2: Identify Fields to Clear

```
Input: fields_to_clear parameter (optional)
Output: Set[field_name]

1. If fields_to_clear is provided, use it as-is
2. Otherwise, return empty set
3. Exclude primary key and index fields from clearing
```

### Step 3: Build SET Clause

```
Input: fields_to_update Dict[field_name, field_value]
Output: (set_clause_str, expression_attribute_names, expression_attribute_values)

1. For each field in fields_to_update:
   a. Check if field is reserved keyword
   b. If reserved: use placeholder #field_name
   c. If not reserved: use field_name directly
   d. Create value placeholder :field_name
   e. Add to expression_attribute_names if reserved
   f. Add to expression_attribute_values
   g. Append "field_placeholder = :field_name" to clauses

2. Join clauses with ", "
3. Return "SET " + joined_clauses
```

### Step 4: Build REMOVE Clause

```
Input: fields_to_clear Set[field_name]
Output: (remove_clause_str, expression_attribute_names)

1. For each field in fields_to_clear:
   a. Check if field is reserved keyword
   b. If reserved: use placeholder #field_name
   c. If not reserved: use field_name directly
   d. Add to expression_attribute_names if reserved
   e. Append field_placeholder to clauses

2. Join clauses with ", "
3. Return "REMOVE " + joined_clauses
```

### Step 5: Combine Clauses

```
Input: set_clause_str, remove_clause_str
Output: update_expression_str

1. Collect non-empty clauses
2. Join with " "
3. Return combined expression
```

### Example Walkthrough

**Model**:
```python
class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.name = None
        self.status = None  # Reserved keyword
        self.email = None
        self.temp_field = None
```

**Call**:
```python
user = User()
user.id = "user-123"
user.name = "John Doe"
user.status = "active"
# email and temp_field are None (not updated)

user.save_partial(
    table_name="users",
    fields_to_clear={"temp_field"}
)
```

**Processing**:
1. Fields to update (non-None): {id, name, status}
2. After excluding primary key: {name, status}
3. Fields to clear: {temp_field}
4. Reserved keywords: {status}
5. SET clause: "SET name = :name, #status = :status"
6. REMOVE clause: "REMOVE temp_field"
7. Final expression: "SET name = :name, #status = :status REMOVE temp_field"
8. Expression attribute names: {"#status": "status"}
9. Expression attribute values: {":name": "John Doe", ":status": "active"}

## Data Models

### UpdateExpressionComponents

```python
@dataclass
class UpdateExpressionComponents:
    """Components of a DynamoDB update expression."""

    update_expression: str
    expression_attribute_names: Dict[str, str]
    expression_attribute_values: Dict[str, Any]
```

### PartialUpdateOptions

```python
@dataclass
class PartialUpdateOptions:
    """Options for partial update operations."""

    table_name: str
    include_fields: Optional[Set[str]] = None
    exclude_fields: Optional[Set[str]] = None
    condition_expression: Optional[str] = None
    expression_attribute_names: Optional[Dict[str, str]] = None
    expression_attribute_values: Optional[Dict[str, Any]] = None
    return_values: str = "NONE"
```

## Integration Points

### 1. Integration with DynamoDB.update_item()

The `save_partial()` method calls `DynamoDB.update_item()` with the generated expression:

```python
response = db.update_item(
    table_name=table_name,
    key=primary_key,
    update_expression=update_expression,
    expression_attribute_values=expression_attribute_values,
    expression_attribute_names=expression_attribute_names,
    condition_expression=condition_expression,
    return_values=return_values,
)
```

**Benefits**:
- Reuses existing retry logic and error handling
- Consistent with other update operations
- Leverages decimal conversion utilities

### 2. Integration with DynamoDBModelBase.merge()

The `merge()` method can be used to populate fields before calling `save_partial()`:

```python
# Load existing item
existing = User().map(db_response)

# Merge partial updates
existing.merge({"name": "Jane", "status": "inactive"})

# Save only merged fields
existing.save_partial(table_name="users")
```

### 3. Integration with DynamoDBReservedWords

The `PartialUpdateBuilder` uses `DynamoDBReservedWords` to detect and handle reserved keywords:

```python
reserved_words = DynamoDBReservedWords()
if reserved_words.is_reserved_word(field_name):
    # Use placeholder
    placeholder = f"#{field_name}"
    expression_attribute_names[placeholder] = field_name
```

### 4. Integration with Indexes

Primary key and index fields are protected from updates:

```python
# Get primary key field names
pk_name = self.indexes.primary.partition_key.attribute_name
sk_name = self.indexes.primary.sort_key.attribute_name

# Get GSI field names
for gsi in self.indexes.secondaries.values():
    gsi_pk = gsi.partition_key.attribute_name
    gsi_sk = gsi.sort_key.attribute_name

# Exclude these from updates
protected_fields = {pk_name, sk_name, gsi_pk, gsi_sk}
```

## Error Handling

### Validation Errors (ValueError)

Raised during input validation:

1. **Missing table_name**: "table_name is required for save_partial()"
2. **Missing primary key**: "Primary key field '{pk_name}' is not populated"
3. **Empty include_fields**: "include_fields cannot be empty"
4. **No fields to update**: "No fields to update after applying filters"
5. **Invalid return_values**: "return_values must be one of: NONE, ALL_NEW, UPDATED_NEW, ALL_OLD, UPDATED_OLD"

### Runtime Errors (RuntimeError)

Raised during execution:

1. **Condition expression failed**: "Conditional check failed for update in {table_name}. Condition: {condition_expression}"
2. **Serialization error**: "Failed to serialize field '{field_name}': {error_details}"
3. **DynamoDB error**: Re-raised with context

### Logging

- **INFO**: Successful updates with table name and field count
- **WARNING**: Retry attempts, throttling
- **ERROR**: Failed updates, serialization errors

## Performance Considerations

### 1. Reserved Keyword Caching

The `DynamoDBReservedWords` class loads the reserved words list once and caches it:

```python
class DynamoDBReservedWords:
    def __init__(self):
        self.__list = self.__read_list()  # Cached
```

**Impact**: O(1) lookup for reserved word checks

### 2. Expression Generation Efficiency

The `PartialUpdateBuilder` generates expressions in a single pass:

```
Time Complexity: O(n) where n = number of fields to update
Space Complexity: O(n) for expression components
```

### 3. Comparison to Manual update_item()

`save_partial()` has minimal overhead compared to manual `update_item()` calls:

- Field introspection: ~1-2ms for typical models
- Expression generation: ~0.5-1ms
- DynamoDB call: ~50-200ms (network bound)

**Total overhead**: <5% compared to DynamoDB call time

### 4. Optimization Opportunities

Future optimizations:
- Cache expression components for repeated updates
- Batch multiple partial updates
- Lazy field introspection for large models

## Testing Strategy

### Unit Tests

**Location**: `tests/unit/dynamodb_tests/partial_update_tests.py`

**Test Categories**:

1. **Field Identification**
   - Populated fields are correctly identified
   - None values are excluded
   - CLEAR_FIELD sentinels are detected
   - Primary keys are excluded
   - Index fields are excluded

2. **Expression Generation**
   - SET clauses are correctly formatted
   - REMOVE clauses are correctly formatted
   - Multiple fields are properly comma-separated
   - Reserved keywords use placeholders
   - Non-reserved keywords don't use placeholders

3. **Field Filtering**
   - include_fields correctly filters fields
   - exclude_fields correctly filters fields
   - Both filters work together
   - Non-existent fields are silently ignored
   - Empty include_fields raises error

4. **Reserved Keyword Handling**
   - Reserved keywords generate placeholders
   - Expression attribute names are correct
   - Expression attribute values are correct
   - Non-reserved keywords don't generate placeholders

5. **Error Handling**
   - Missing table_name raises ValueError
   - Missing primary key raises ValueError
   - No fields to update raises ValueError
   - Invalid return_values raises ValueError

6. **Integration**
   - Works with merge() pattern
   - Works with map() pattern
   - Model instance is not modified
   - Multiple calls generate correct expressions

### Property-Based Tests

**Framework**: Hypothesis (Python)

**Test Categories**:

1. **Idempotence**: Calling save_partial() twice produces same result
2. **Selective Updates**: Only specified fields are updated
3. **Reserved Keyword Correctness**: Reserved keywords handled correctly
4. **CLEAR_FIELD Correctness**: CLEAR_FIELD generates REMOVE operations
5. **Primary Key Immutability**: Primary keys are never updated
6. **Field Filtering Correctness**: Filters work correctly
7. **Expression Syntax**: Generated expressions are valid

### Integration Tests

**Location**: `tests/integration/dynamodb_tests/partial_update_integration_tests.py`

**Test Categories**:

1. **DynamoDB Operations**
   - Partial updates work with real DynamoDB (or moto)
   - Conditional writes succeed/fail correctly
   - Return values are correct
   - Throttling and retries work

2. **Model Integration**
   - Works with various model types
   - Works with indexes
   - Works with TTL fields
   - Works with nested objects

3. **Error Scenarios**
   - Condition expression failures
   - Serialization errors
   - DynamoDB errors
   - Throttling and retries

## Code Examples

### Basic Usage

```python
# Load existing item
user = User().map(db_response)

# Populate fields to update
user.name = "Jane Doe"
user.status = "inactive"

# Update only non-None fields
db = DynamoDB()
response = db.update_item_partial(item=user, table_name="users")
# Only name and status are updated (id is primary key)
```

### Clearing Fields

```python
# Clear specific fields by passing fields_to_clear
response = db.update_item_partial(
    item=user,
    table_name="users",
    fields_to_clear={"temp_field", "description"}
)
# temp_field and description are removed from the item
```

### With Conditional Write

```python
# Only update if version hasn't changed
response = db.update_item_partial(
    item=user,
    table_name="users",
    condition_expression="version = :expected_version",
    expression_attribute_values={":expected_version": 5}
)
```

### With Return Values

```python
# Get updated item back
response = db.update_item_partial(
    item=user,
    table_name="users",
    return_values="ALL_NEW"
)
updated_user = response.get("Attributes", {})
```

### With merge() Pattern

```python
# Load existing
existing = User().map(db_response)

# Merge partial updates
updates = {"name": "Jane", "status": "active"}
existing.merge(updates)

# Update only non-None fields
db = DynamoDB()
response = db.update_item_partial(item=existing, table_name="users")
```

### Combining Updates and Clears

```python
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"
# temp_field is None (not updated)

db = DynamoDB()
response = db.update_item_partial(
    item=user,
    table_name="users",
    fields_to_clear={"temp_field", "old_data"}
)
# name and email are SET, temp_field and old_data are REMOVED
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Idempotence of Partial Updates

**Description**: Applying the same partial update twice should produce the same result as applying it once.

**Property**: For any model instance with fields populated, calling `save_partial()` twice with the same field set should result in the same item state in DynamoDB.

**Validates**: Requirements 1.1, 1.2, 6.4

**Test Strategy**: Property-based test with generated field updates. Generate a model with random field values, call `save_partial()`, verify the item state, call `save_partial()` again with the same fields, verify the item state is identical.

### Property 2: Selective Field Update Correctness

**Description**: Only the specified fields should be updated; all other fields should remain unchanged.

**Property**: For any model instance with fields {f1, f2, f3, f4} where only {f1, f2} are populated, after `save_partial()`, the item in DynamoDB should have f1 and f2 updated to the new values, while f3 and f4 retain their original values.

**Validates**: Requirements 1.1, 1.3, 2.1, 2.2, 6.1

**Test Strategy**: Property-based test with generated field sets. Create an item with known values for all fields, load it, populate only a subset of fields with new values, call `save_partial()`, verify only the populated fields changed and others remained the same.

### Property 3: Reserved Keyword Handling Correctness

**Description**: Fields with reserved keyword names should be updated correctly without manual expression attribute name management.

**Property**: For any model with a field named with a reserved keyword (e.g., "status"), calling `save_partial()` should generate the correct expression attribute names mapping and update the field correctly.

**Validates**: Requirements 3.1, 3.2, 3.3, 3.4, 3.5

**Test Strategy**: Property-based test with all DynamoDB reserved keywords. For each reserved keyword, create a model with that field, populate it, call `save_partial()`, verify the field was updated correctly in DynamoDB.

### Property 4: CLEAR_FIELD Sentinel Correctness

**Description**: Using CLEAR_FIELD should remove a field (set it to None), while None values should be ignored.

**Property**: For any model instance where a field is set to CLEAR_FIELD, calling `save_partial()` should generate a REMOVE operation for that field. For fields set to None, they should be excluded from the update.

**Validates**: Requirements 1.3, 1.4, 4.2

**Test Strategy**: Property-based test with generated field values including None and CLEAR_FIELD. Verify that CLEAR_FIELD generates REMOVE operations and None values are excluded.

### Property 5: Primary Key Immutability

**Description**: Primary key fields should never be updated via `save_partial()`.

**Property**: For any model instance, attempting to update primary key fields via `save_partial()` should either be silently ignored or raise an error, but never actually update the primary key in DynamoDB.

**Validates**: Requirements 6.5, 9.5

**Test Strategy**: Property-based test with generated primary key values. Attempt to update primary key fields, verify they are not updated in DynamoDB.

### Property 6: Update Expression Syntax Correctness

**Description**: Generated update expressions should be syntactically valid DynamoDB expressions.

**Property**: For any model instance with populated fields, the generated update expression should be a valid DynamoDB update expression that can be executed without syntax errors.

**Validates**: Requirements 4.1, 4.2, 4.3, 4.6

**Test Strategy**: Property-based test with generated field sets. Generate update expressions, verify they can be executed against DynamoDB without syntax errors.

### Property 7: Field Filtering Correctness

**Description**: `include_fields` and `exclude_fields` parameters should correctly filter which fields are updated.

**Property**: For any model instance with fields {f1, f2, f3, f4} and `include_fields={f1, f2}`, only f1 and f2 should be updated. For `exclude_fields={f3, f4}`, all fields except f3 and f4 should be updated.

**Validates**: Requirements 2.1, 2.2, 2.3

**Test Strategy**: Property-based test with generated field sets and filter combinations. Verify that only the correct fields are updated based on the filters.

### Property 8: Model Instance Immutability

**Description**: Calling `save_partial()` should not modify the model instance.

**Property**: For any model instance, calling `save_partial()` should not change any of the model's field values.

**Validates**: Requirements 6.3

**Test Strategy**: Property-based test with generated field updates. Capture model state before `save_partial()`, call the method, verify model state is unchanged.

## Future Enhancements

### 1. Atomic Counter Support (Requirement 7)

Add support for ADD operations on numeric fields:

```python
class AtomicCounter:
    """Marker for fields that should use ADD operations."""
    pass

# Usage
user.view_count = AtomicCounter(1)  # Increment by 1
user.save_partial(table_name="users")
# Generates: ADD view_count :view_count
```

### 2. Optimistic Locking (Requirement 8)

Add automatic version field handling:

```python
response = user.save_partial(
    table_name="users",
    fail_if_changed=True  # Auto-check version field
)
# Automatically increments version field
```

### 3. Batch Partial Updates

Support updating multiple items efficiently:

```python
db.batch_save_partial(
    items=[user1, user2, user3],
    table_name="users"
)
```

### 4. Transactional Partial Updates

Support partial updates within transactions:

```python
db.transact_write_items([
    TransactWriteItem(
        Update=user.save_partial_transact(table_name="users")
    )
])
```

## Constraints and Assumptions

### Constraints

1. **Primary Key Immutability**: Primary key fields cannot be updated
2. **Index Field Immutability**: Index key fields cannot be updated
3. **Single Item**: Only updates one item at a time
4. **DynamoDB Limits**: Must comply with DynamoDB expression limits (25 attributes max)
5. **Reserved Keyword Handling**: All DynamoDB reserved keywords must be handled

### Assumptions

1. **Model Initialization**: Models are properly initialized with fields set to None
2. **Primary Key Availability**: Primary key fields are always populated before calling `save_partial()`
3. **Table Existence**: DynamoDB table exists and is accessible
4. **Permissions**: AWS credentials have UpdateItem permissions
5. **Field Naming**: Model field names match DynamoDB attribute names
6. **Serialization**: All model fields can be serialized to DynamoDB format

## Summary

The partial updates feature provides a clean, intuitive API for selective field updates while maintaining consistency with existing ORM patterns. By automating reserved keyword handling and expression generation, it reduces boilerplate and error-prone manual expression construction. The design prioritizes safety through validation and protection of critical fields, while maintaining flexibility through field filtering and conditional writes.
