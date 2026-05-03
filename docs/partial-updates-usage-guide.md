# Partial Updates Guide

## Introduction

Partial updates allow you to modify only specific fields of a DynamoDB item without replacing the entire item. This is essential for:
- Efficient updates when only a few fields change
- Avoiding unnecessary data transfer
- Preventing accidental overwrites of other fields
- Reducing write capacity consumption

This guide covers:
- Basic partial update patterns
- Field clearing and removal
- Conditional writes with partial updates
- Error handling and validation
- Integration with existing patterns (`merge()`, `map()`)
- Reserved keyword handling

## Why Partial Updates?

### The Problem Without Partial Updates

```python
# ❌ Full replacement - overwrites all fields
user = {
    "pk": "user#123",
    "sk": "user#123",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "address": "123 Main St",
    "preferences": {...},
    "metadata": {...}
}

# If we only want to update name and email, we must provide ALL fields
# Risk: If we forget a field, it gets overwritten with None or default
db.save(item=user, table_name="users")  # Replaces entire item
```

### The Solution: Partial Updates

```python
# ✅ Partial update - only specified fields are updated
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"
# Other fields (phone, address, preferences, metadata) are not touched

# Only name and email are updated in DynamoDB
response = user.save_partial(table_name="users")
# Other fields remain unchanged
```

## Basic Usage

### Simple Field Update

```python
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase

class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.name = None
        self.email = None
        self.phone = None
        self.status = None

# Create a user instance with only the fields to update
user = User()
user.id = "user-123"  # Primary key (required)
user.name = "Jane Doe"
user.email = "jane@example.com"
# phone and status are None (not updated)

# Save only the populated fields
response = user.save_partial(table_name="users")
# Result: Only name and email are updated in DynamoDB
```

### Updating After Loading

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB

db = DynamoDB()

# Load existing item
response = db.get(
    key={"pk": "user#123", "sk": "user#123"},
    table_name="users"
)
user = User().map(response["Item"])

# Update specific fields
user.name = "Jane Doe"
user.email = "jane@example.com"

# Save only the updated fields
response = user.save_partial(table_name="users")
# Result: Only name and email are updated; other fields unchanged
```

## Field Clearing Patterns

### Removing a Single Field

```python
# Clear a field by including it in fields_to_clear
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    fields_to_clear={"phone"}
)
# Result: name is SET, phone is REMOVED
```

### Removing Multiple Fields

```python
# Clear multiple fields at once
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    fields_to_clear={"phone", "address", "temp_data"}
)
# Result: name is SET, phone/address/temp_data are REMOVED
```

### Combining Updates and Clears

```python
# Update some fields and clear others in a single operation
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"

response = user.save_partial(
    table_name="users",
    fields_to_clear={"phone", "old_address", "temp_field"}
)
# Result: name and email are SET, phone/old_address/temp_field are REMOVED
```

### Clearing All Optional Fields

```python
# Get all optional field names
optional_fields = {"phone", "address", "preferences", "metadata"}

user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    fields_to_clear=optional_fields
)
# Result: name is SET, all optional fields are REMOVED
```

## Conditional Write Patterns

### Version-Based Optimistic Locking

```python
# Update only if version hasn't changed
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.version = 5

try:
    response = user.save_partial(
        table_name="users",
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": 5}
    )
    print("✅ Update successful")
except RuntimeError:
    print("⚠️ Version conflict - item was modified by another user")
```

### Attribute Existence Check

```python
# Update only if item exists
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    condition_expression="attribute_exists(pk)"
)
# Result: Update only succeeds if item exists
```

### Status-Based Conditional Update

```python
# Update only if status is in a specific state
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.status = "active"

response = user.save_partial(
    table_name="users",
    condition_expression="#status = :pending",
    expression_attribute_names={"#status": "status"},
    expression_attribute_values={":pending": "pending"}
)
# Result: Update only if current status is "pending"
```

### Complex Conditional Logic

```python
# Multiple conditions with AND/OR
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    condition_expression="(#status = :active OR #status = :pending) AND version = :v",
    expression_attribute_names={"#status": "status"},
    expression_attribute_values={
        ":active": "active",
        ":pending": "pending",
        ":v": 5
    }
)
# Result: Update only if status is active/pending AND version is 5
```

## Return Values Patterns

### Get Updated Item Back

```python
# Return the complete updated item
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    return_values="ALL_NEW"
)
updated_user = response.get("Attributes", {})
print(f"Updated user: {updated_user}")
```

### Get Only Updated Fields

```python
# Return only the fields that were updated
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"

response = user.save_partial(
    table_name="users",
    return_values="UPDATED_NEW"
)
updated_fields = response.get("Attributes", {})
# Result: {"name": "Jane Doe", "email": "jane@example.com"}
```

### Get Previous Values

```python
# Return the item before the update
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    return_values="ALL_OLD"
)
previous_user = response.get("Attributes", {})
print(f"Previous user: {previous_user}")
```

### Get Previous Updated Fields

```python
# Return only the fields that were updated, before the update
user = User()
user.id = "user-123"
user.name = "Jane Doe"

response = user.save_partial(
    table_name="users",
    return_values="UPDATED_OLD"
)
previous_fields = response.get("Attributes", {})
# Result: {"name": "John Doe"}  (previous value)
```

## Error Handling Patterns

### Handling Validation Errors

```python
from botocore.exceptions import ClientError

user = User()
user.id = "user-123"
user.name = "Jane Doe"

try:
    response = user.save_partial(table_name="users")
except ValueError as e:
    # Validation error (missing primary key, invalid parameters, etc.)
    print(f"❌ Validation error: {e}")
except RuntimeError as e:
    # Condition expression failed or serialization error
    print(f"❌ Runtime error: {e}")
except ClientError as e:
    # DynamoDB error (throttling, permissions, etc.)
    print(f"❌ DynamoDB error: {e}")
```

### Handling Condition Failures

```python
user = User()
user.id = "user-123"
user.name = "Jane Doe"

try:
    response = user.save_partial(
        table_name="users",
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": 5}
    )
    print("✅ Update successful")
except RuntimeError as e:
    if "Conditional check failed" in str(e):
        print("⚠️ Condition not met - refresh and retry")
    else:
        print(f"❌ Other error: {e}")
```

### Retry Logic for Transient Failures

```python
import time

def update_with_retry(user, table_name, max_retries=3):
    """Update with automatic retry on transient failures"""
    for attempt in range(max_retries):
        try:
            response = user.save_partial(table_name=table_name)
            return {"success": True, "attempt": attempt + 1}
        except ClientError as e:
            if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(0.1 * (2 ** attempt))
                    continue
            raise
    return {"success": False, "error": "Max retries exceeded"}
```

## Integration with Existing Patterns

### Using with merge()

```python
# Load existing item
response = db.get(
    key={"pk": "user#123", "sk": "user#123"},
    table_name="users"
)
existing = User().map(response["Item"])

# Merge partial updates
updates = {
    "name": "Jane Doe",
    "email": "jane@example.com"
}
existing.merge(updates)

# Save only merged fields
response = existing.save_partial(table_name="users")
# Result: Only name and email are updated
```

### Using with map()

```python
# Load item from DynamoDB
response = db.get(
    key={"pk": "user#123", "sk": "user#123"},
    table_name="users"
)

# Map to model
user = User().map(response["Item"])

# Update specific fields
user.name = "Jane Doe"
user.email = "jane@example.com"

# Save only updated fields
response = user.save_partial(table_name="users")
```

### Batch Partial Updates

```python
# Update multiple items with partial updates
users_to_update = [
    {"id": "user-1", "name": "Jane Doe"},
    {"id": "user-2", "name": "John Smith"},
    {"id": "user-3", "name": "Alice Johnson"}
]

for user_data in users_to_update:
    user = User()
    user.id = user_data["id"]
    user.name = user_data["name"]

    try:
        response = user.save_partial(table_name="users")
        print(f"✅ Updated {user.id}")
    except Exception as e:
        print(f"❌ Failed to update {user.id}: {e}")
```

## Reserved Keyword Handling

### Automatic Placeholder Generation

```python
# Fields with reserved keywords are handled automatically
class Order(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.status = None  # Reserved keyword
        self.type = None    # Reserved keyword
        self.name = None    # Reserved keyword

order = Order()
order.id = "order-123"
order.status = "pending"
order.type = "standard"
order.name = "Order #123"

# No need to manually handle reserved keywords
response = order.save_partial(table_name="orders")
# Library automatically generates:
# - Expression attribute names: {"#status": "status", "#type": "type", "#name": "name"}
# - Update expression: "SET #status = :status, #type = :type, #name = :name"
```

### Custom Expression Attribute Names

```python
# You can provide additional expression attribute names if needed
order = Order()
order.id = "order-123"
order.status = "pending"

response = order.save_partial(
    table_name="orders",
    expression_attribute_names={"#custom": "custom_field"},
    expression_attribute_values={":custom": "value"}
)
# Library merges auto-generated names with your custom ones
```

## Performance Considerations

### Partial Updates vs Full Saves

```python
# ❌ Full save - sends entire item
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"
user.phone = "555-1234"
user.address = "123 Main St"
user.preferences = {...}  # Large nested object
user.metadata = {...}     # Large nested object

db.save(item=user, table_name="users")
# Sends entire item to DynamoDB

# ✅ Partial update - sends only changed fields
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"

response = user.save_partial(table_name="users")
# Sends only name and email to DynamoDB
# Reduces network traffic and write capacity consumption
```

### Write Capacity Consumption

```python
# Partial updates consume the same WCU as full saves
# 1 KB of data = 1 WCU (whether partial or full)

# Example:
# - Full save of 5 KB item = 5 WCU
# - Partial update of 1 KB = 1 WCU
# - Partial update of 5 KB = 5 WCU

# Benefit: Only pay for what you update
```

## Common Use Cases

### User Profile Updates

```python
# Update user profile without affecting other data
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"
user.phone = "555-1234"

response = user.save_partial(table_name="users")
# Only profile fields are updated
```

### Status Transitions

```python
# Update status without affecting other fields
order = Order()
order.id = "order-123"
order.status = "shipped"

response = order.save_partial(table_name="orders")
# Only status is updated
```

### Cleanup Operations

```python
# Remove temporary or obsolete fields
user = User()
user.id = "user-123"

response = user.save_partial(
    table_name="users",
    fields_to_clear={"temp_token", "old_email", "migration_flag"}
)
# Temporary fields are removed
```

### Incremental Updates

```python
# Update fields as they become available
user = User()
user.id = "user-123"

# First update: basic info
user.name = "Jane Doe"
user.save_partial(table_name="users")

# Later: add email
user.email = "jane@example.com"
user.save_partial(table_name="users")

# Later: add phone
user.phone = "555-1234"
user.save_partial(table_name="users")
```

## Best Practices

### 1. Always Populate Primary Keys

```python
# ✅ Good: Primary key is populated
user = User()
user.id = "user-123"  # Primary key
user.name = "Jane Doe"
response = user.save_partial(table_name="users")

# ❌ Bad: Primary key is missing
user = User()
user.name = "Jane Doe"
response = user.save_partial(table_name="users")  # Raises ValueError
```

### 2. Use Conditional Writes for Concurrent Updates

```python
# ✅ Good: Version check prevents conflicts
response = user.save_partial(
    table_name="users",
    condition_expression="version = :expected_version",
    expression_attribute_values={":expected_version": 5}
)

# ❌ Bad: No version check - race conditions possible
response = user.save_partial(table_name="users")
```

### 3. Handle Errors Gracefully

```python
# ✅ Good: Specific error handling
try:
    response = user.save_partial(table_name="users")
except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"Condition failed: {e}")
except ClientError as e:
    print(f"DynamoDB error: {e}")

# ❌ Bad: No error handling
response = user.save_partial(table_name="users")
```

### 4. Use Return Values When Needed

```python
# ✅ Good: Get updated item back for verification
response = user.save_partial(
    table_name="users",
    return_values="ALL_NEW"
)
updated_user = response.get("Attributes", {})

# ❌ Bad: Ignore return values when you need them
response = user.save_partial(table_name="users")
# Can't verify what was actually updated
```

### 5. Clear Fields Explicitly

```python
# ✅ Good: Explicitly clear fields
response = user.save_partial(
    table_name="users",
    fields_to_clear={"temp_field"}
)

# ❌ Bad: Assume None values clear fields
user.temp_field = None
response = user.save_partial(table_name="users")
# None values are ignored, field is not cleared
```

### 6. Use merge() for Complex Updates

```python
# ✅ Good: Use merge() for multiple updates
existing = User().map(db_response)
existing.merge({
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "555-1234"
})
response = existing.save_partial(table_name="users")

# ❌ Bad: Manual field assignment
existing.name = "Jane Doe"
existing.email = "jane@example.com"
existing.phone = "555-1234"
response = existing.save_partial(table_name="users")
```

## Troubleshooting

### "Primary key field 'pk' is not populated"

```python
# Problem: Primary key is missing
user = User()
user.name = "Jane Doe"
response = user.save_partial(table_name="users")  # ❌ Error

# Solution: Always populate primary key
user = User()
user.id = "user-123"  # Primary key
user.name = "Jane Doe"
response = user.save_partial(table_name="users")  # ✅ Works
```

### "No fields to update or clear"

```python
# Problem: No fields to update
user = User()
user.id = "user-123"
# All other fields are None
response = user.save_partial(table_name="users")  # ❌ Error

# Solution: Populate at least one field
user = User()
user.id = "user-123"
user.name = "Jane Doe"  # At least one field
response = user.save_partial(table_name="users")  # ✅ Works
```

### "Conditional check failed"

```python
# Problem: Condition not met
try:
    response = user.save_partial(
        table_name="users",
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": 5}
    )
except RuntimeError:
    # ❌ Condition failed

# Solution: Refresh item and retry
response = db.get(
    key={"pk": "user#123", "sk": "user#123"},
    table_name="users"
)
user = User().map(response["Item"])
user.name = "Jane Doe"
response = user.save_partial(table_name="users")  # ✅ Works with current version
```

### "Cannot clear primary key or index fields"

```python
# Problem: Trying to clear protected fields
response = user.save_partial(
    table_name="users",
    fields_to_clear={"id"}  # ❌ Primary key
)

# Solution: Only clear non-protected fields
response = user.save_partial(
    table_name="users",
    fields_to_clear={"temp_field", "old_data"}  # ✅ Non-protected fields
)
```

## Summary

**Key Takeaways:**

1. ✅ **Partial updates modify only specified fields** - other fields remain unchanged
2. ✅ **Primary keys are required** - always populate them
3. ✅ **Use `fields_to_clear`** to explicitly remove fields
4. ✅ **Conditional writes prevent conflicts** - use version checks for concurrent updates
5. ✅ **Reserved keywords are handled automatically** - no manual placeholder management needed
6. ✅ **Return values provide feedback** - use them to verify updates
7. ⚠️ **None values are ignored** - use `fields_to_clear` to remove fields
8. ⚠️ **Conditions consume WCUs** - even if they fail

**Common Use Cases:**
- User profile updates
- Status transitions
- Cleanup operations
- Incremental updates
- Concurrent updates with optimistic locking

## Related Guides

- [Conditional Writes](help/dynamodb/009-guide-conditional-writes.md) - Optimistic locking patterns
- [Update Expressions](help/dynamodb/010-guide-update-expressions.md) - Advanced expression syntax
- [Defining Models](help/dynamodb/002-guide-defining-models.md) - Model structure and fields
- [Service Layers](help/dynamodb/003-guide-service-layers.md) - Using partial updates in services

## Example Code

Complete working examples:
- [`examples/dynamodb/partial_updates_example.py`](../examples/dynamodb/partial_updates_example.py)
- [`tests/unit/dynamodb_tests/dynamodb_model_save_partial_test.py`](../tests/unit/dynamodb_tests/dynamodb_model_save_partial_test.py)
- [`tests/integration/dynamodb_tests/partial_update_integration_test.py`](../tests/integration/dynamodb_tests/partial_update_integration_test.py)
