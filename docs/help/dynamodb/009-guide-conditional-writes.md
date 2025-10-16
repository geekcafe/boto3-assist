# Conditional Writes and Optimistic Locking

## Introduction

Conditional writes allow you to control when DynamoDB write operations succeed based on the current state of items. This is essential for:
- Preventing race conditions
- Implementing optimistic locking
- Ensuring data integrity
- Preventing duplicate records

This guide covers:
- Conditional expressions in `save()`
- Optimistic locking patterns with version numbers
- Common conditional patterns
- Error handling and retry strategies

## Why Conditional Writes?

### The Problem Without Conditions

```python
# ❌ Race condition - two users can overwrite each other
user1_doc = db.get(...)
user2_doc = db.get(...)  # Both read version 1

user1_doc['content'] = "User 1 changes"
db.save(user1_doc)  # Saves successfully

user2_doc['content'] = "User 2 changes"
db.save(user2_doc)  # Overwrites User 1's changes! 💥
```

### The Solution: Conditional Writes

```python
# ✅ With optimistic locking - conflicts detected
current_version = doc['version']

updated_doc['version'] = current_version + 1
db.save(
    item=updated_doc,
    condition_expression="#version = :expected_version",
    expression_attribute_names={"#version": "version"},
    expression_attribute_values={":expected_version": current_version}
)
# Fails if version changed - User 2 knows to refresh!
```

## Basic Usage

### Prevent Duplicates

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB

db = DynamoDB()

user = {
    "pk": "user#001",
    "sk": "user#001",
    "id": "001",
    "email": "user@example.com"
}

# Only create if doesn't already exist
db.save(
    item=user,
    table_name="users",
    fail_if_exists=True  # Built-in helper
)
```

### Custom Condition Expression

```python
# Update only if status is "pending"
db.save(
    item=order,
    table_name="orders",
    condition_expression="#status = :pending",
    expression_attribute_names={"#status": "status"},
    expression_attribute_values={":pending": "pending"}
)
```

## Condition Expression Syntax

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `#status = :active` |
| `<>` | Not equal | `#status <> :deleted` |
| `<` | Less than | `price < :max_price` |
| `<=` | Less than or equal | `age <= :max_age` |
| `>` | Greater than | `balance > :min_balance` |
| `>=` | Greater than or equal | `stock >= :min_stock` |

### Logical Operators

```python
# AND
condition_expression="#status = :active AND balance >= :min_balance"

# OR
condition_expression="#type = :premium OR #type = :gold"

# NOT
condition_expression="NOT #deleted = :true"

# Combination
condition_expression="(#status = :active OR #status = :pending) AND balance > :zero"
```

### Functions

#### attribute_exists

```python
# Update only if item exists
condition_expression="attribute_exists(pk)"
```

#### attribute_not_exists

```python
# Create only if item doesn't exist
condition_expression="attribute_not_exists(pk)"
```

#### begins_with

```python
# Only update if email starts with specific domain
condition_expression="begins_with(email, :domain)"
expression_attribute_values={":domain": "@company.com"}
```

#### size

```python
# Only update if list has items
condition_expression="size(tags) > :min_size"
expression_attribute_values={":min_size": 0}
```

#### contains

```python
# Only update if list contains value
condition_expression="contains(tags, :tag)"
expression_attribute_values={":tag": "premium"}
```

## Optimistic Locking Pattern

Optimistic locking uses version numbers to detect conflicts:

### Basic Implementation

```python
def update_document_with_locking(doc_id, new_content):
    """Update document with optimistic locking"""
    db = DynamoDB()
    table_name = "documents"
    
    # 1. Read current version
    response = db.get(
        key={"pk": f"doc#{doc_id}", "sk": f"doc#{doc_id}"},
        table_name=table_name
    )
    
    current_version = response["Item"]["version"]
    current_doc = response["Item"]
    
    # 2. Prepare update with incremented version
    updated_doc = {
        "pk": f"doc#{doc_id}",
        "sk": f"doc#{doc_id}",
        "id": doc_id,
        "content": new_content,
        "version": current_version + 1  # Increment version
    }
    
    # 3. Save with version check
    try:
        db.save(
            item=updated_doc,
            table_name=table_name,
            condition_expression="#version = :expected_version",
            expression_attribute_names={"#version": "version"},
            expression_attribute_values={":expected_version": current_version}
        )
        return {"success": True, "version": current_version + 1}
    except RuntimeError:
        return {"success": False, "error": "Version conflict - document was modified"}
```

### With Retry Logic

```python
def update_with_retry(doc_id, new_content, max_retries=3):
    """Update with automatic retry on version conflicts"""
    db = DynamoDB()
    table_name = "documents"
    
    for attempt in range(max_retries):
        try:
            # Read current state
            response = db.get(
                key={"pk": f"doc#{doc_id}", "sk": f"doc#{doc_id}"},
                table_name=table_name
            )
            current_version = response["Item"]["version"]
            
            # Prepare update
            updated_doc = {
                "pk": f"doc#{doc_id}",
                "sk": f"doc#{doc_id}",
                "id": doc_id,
                "content": new_content,
                "version": current_version + 1
            }
            
            # Attempt save
            db.save(
                item=updated_doc,
                table_name=table_name,
                condition_expression="#version = :expected_version",
                expression_attribute_names={"#version": "version"},
                expression_attribute_values={":expected_version": current_version}
            )
            
            return {"success": True, "attempt": attempt + 1}
            
        except RuntimeError:
            if attempt < max_retries - 1:
                continue  # Retry
            else:
                return {"success": False, "error": "Max retries exceeded"}
```

## Common Patterns

### Pattern 1: Unique Email Registration

```python
def register_user(email, user_data):
    """Register user with unique email check"""
    db = DynamoDB()
    
    # Create user record
    user = {
        "pk": f"user#{user_data['id']}",
        "sk": f"user#{user_data['id']}",
        **user_data
    }
    
    # Create email index
    email_record = {
        "pk": "emails#",
        "sk": f"email#{email}",
        "user_id": user_data['id']
    }
    
    # Save user
    try:
        db.save(item=user, table_name="users", fail_if_exists=True)
        
        # Save email (must be unique)
        db.save(
            item=email_record,
            table_name="users",
            condition_expression="attribute_not_exists(sk)"
        )
        return {"success": True}
    except RuntimeError:
        return {"success": False, "error": "User or email already exists"}
```

### Pattern 2: Inventory Reservation

```python
def reserve_inventory(product_id, quantity):
    """Reserve inventory with stock check"""
    db = DynamoDB()
    table_name = "products"
    
    # Read current stock
    response = db.get(
        key={"pk": f"product#{product_id}", "sk": f"product#{product_id}"},
        table_name=table_name
    )
    current_stock = response["Item"]["stock"]
    
    # Decrement stock
    updated_product = {
        "pk": f"product#{product_id}",
        "sk": f"product#{product_id}",
        "stock": current_stock - quantity
    }
    
    try:
        # Only update if sufficient stock
        db.save(
            item=updated_product,
            table_name=table_name,
            condition_expression="stock >= :quantity",
            expression_attribute_values={":quantity": quantity}
        )
        return {"success": True, "remaining_stock": current_stock - quantity}
    except RuntimeError:
        return {"success": False, "error": "Insufficient stock"}
```

### Pattern 3: Status Workflow

```python
def transition_order_status(order_id, from_status, to_status):
    """Transition order status with validation"""
    db = DynamoDB()
    table_name = "orders"
    
    # Read order
    response = db.get(
        key={"pk": f"order#{order_id}", "sk": f"order#{order_id}"},
        table_name=table_name
    )
    order = response["Item"]
    order["status"] = to_status
    
    try:
        # Only transition if currently in expected status
        db.save(
            item=order,
            table_name=table_name,
            condition_expression="#status = :from_status",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":from_status": from_status}
        )
        return {"success": True}
    except RuntimeError:
        return {"success": False, "error": f"Order not in '{from_status}' status"}
```

### Pattern 4: Idempotent Operations

```python
def log_event_once(event_id, event_data):
    """Log event exactly once (idempotent)"""
    db = DynamoDB()
    table_name = "events"
    
    event = {
        "pk": f"event#{event_id}",
        "sk": f"event#{event_id}",
        "id": event_id,
        **event_data
    }
    
    try:
        # Only create if doesn't exist
        db.save(
            item=event,
            table_name=table_name,
            fail_if_exists=True
        )
        return {"success": True, "message": "Event logged"}
    except RuntimeError:
        return {"success": True, "message": "Event already logged (idempotent)"}
```

## Error Handling

### Catching Conditional Failures

```python
try:
    db.save(
        item=item,
        table_name="users",
        condition_expression="#version = :v",
        expression_attribute_names={"#version": "version"},
        expression_attribute_values={":v": 5}
    )
    print("✅ Save successful")
    
except RuntimeError as e:
    if "Conditional check failed" in str(e):
        print("⚠️ Condition not met - refresh and retry")
    else:
        print(f"❌ Other error: {e}")
```

### Graceful Degradation

```python
def safe_update(item, table_name, max_attempts=3):
    """Update with graceful failure"""
    db = DynamoDB()
    
    for attempt in range(max_attempts):
        try:
            db.save(
                item=item,
                table_name=table_name,
                condition_expression="attribute_exists(pk)"
            )
            return {"success": True}
        except RuntimeError:
            if attempt < max_attempts - 1:
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
    
    return {"success": False, "error": "Update failed after retries"}
```

## Best Practices

### 1. Always Use Version Numbers for Concurrent Updates

```python
# ✅ Good: Version number prevents conflicts
item = {
    "pk": "doc#1",
    "sk": "doc#1",
    "content": "...",
    "version": 2  # ← Include version
}

db.save(
    item=item,
    table_name="documents",
    condition_expression="#version = :v",
    expression_attribute_names={"#version": "version"},
    expression_attribute_values={":v": 1}
)

# ❌ Bad: No version check - race conditions possible
db.save(item=item, table_name="documents")
```

### 2. Use Specific Conditions

```python
# ✅ Good: Specific condition
condition_expression="#status = :pending AND balance >= :amount"

# ❌ Bad: No validation
# Just save without checking
```

### 3. Handle Conflicts Gracefully

```python
# ✅ Good: User-friendly error handling
try:
    db.save(...)
except RuntimeError:
    return {
        "error": "Document was modified by another user",
        "action": "Please refresh and try again"
    }

# ❌ Bad: Let exception bubble up
db.save(...)  # Crashes on conflict
```

### 4. Add Retry Logic for Transient Conflicts

```python
# ✅ Good: Automatic retry
for attempt in range(3):
    try:
        db.save(...)
        break
    except RuntimeError:
        if attempt < 2:
            continue

# ❌ Bad: Give up immediately
db.save(...)
```

### 5. Log Conditional Failures

```python
import logging

try:
    db.save(
        item=item,
        table_name="users",
        condition_expression="..."
    )
except RuntimeError as e:
    logging.warning(
        f"Conditional check failed for {item['pk']}",
        extra={"condition": condition_expression, "error": str(e)}
    )
```

## Performance Considerations

### Conditional Writes Cost

Conditional writes have the **same WCU cost** as regular writes:
- 1 KB item = 1 WCU (whether conditional or not)
- Failed conditions still consume WCUs

### When to Use Conditions

✅ **Use conditions when:**
- Data integrity is critical
- Preventing duplicates
- Implementing workflows
- Concurrent updates expected

❌ **Skip conditions when:**
- Single-writer scenario
- Data can be eventually consistent
- Performance is critical and conflicts rare

## Summary

**Key Takeaways:**

1. ✅ **Conditional writes prevent race conditions** and ensure data integrity
2. ✅ **Optimistic locking with versions** detects concurrent modifications
3. ✅ **`fail_if_exists`** is a shortcut for preventing duplicates
4. ✅ **Custom conditions** support complex validation logic
5. ✅ **Retry logic** handles transient conflicts gracefully
6. ⚠️ **Always increment version** numbers when using optimistic locking
7. ⚠️ **Failed conditions consume WCUs** - design appropriately

**Common Use Cases:**
- User registration (unique email)
- Inventory management (stock checks)
- Financial operations (balance checks)
- Document editing (version conflicts)
- Workflow transitions (status validation)

## Related Guides

- [Transactions](8-guide-transactions.md) - Atomic multi-item operations
- [Creating Service Layers](3-guide-service-layers.md) - Using conditions in services
- [Testing with Moto](4-guide-testing-with-moto.md) - Test conditional logic

## Example Code

Complete working examples:
- [`examples/dynamodb/conditional_writes_example.py`](../../../examples/dynamodb/conditional_writes_example.py)
- [`tests/unit/dynamodb_tests/dynamodb_conditional_test.py`](../../../tests/unit/dynamodb_tests/dynamodb_conditional_test.py)
