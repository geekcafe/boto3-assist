# Update Expressions: Efficient Attribute Modifications

## Introduction

Update expressions allow you to modify specific attributes of a DynamoDB item without replacing the entire item. This is more efficient than retrieving, modifying, and saving the whole item.

Key benefits:
- **Atomic operations** - Race-condition safe
- **Network efficient** - Only send changes, not entire item
- **Cost effective** - Lower WCU consumption
- **Flexible** - Combine multiple operations

This guide covers:
- Four update operations: SET, ADD, REMOVE, DELETE
- Atomic counters and sets
- List and map operations
- Conditional updates
- Best practices

## Why Update Expressions?

### The Problem: Read-Modify-Write

```python
# ❌ Inefficient: Read-modify-write pattern
response = db.get(key={"pk": "post#123", "sk": "post#123"}, table_name="posts")
post = response["Item"]
post["views"] += 1  # Race condition! Multiple requests = lost updates
db.save(item=post, table_name="posts")
```

### The Solution: Atomic Updates

```python
# ✅ Efficient: Direct atomic update
db.update_item(
    table_name="posts",
    key={"pk": "post#123", "sk": "post#123"},
    update_expression="ADD views :inc",
    expression_attribute_values={":inc": 1}
)
# Atomic, fast, race-condition safe!
```

## Basic Usage

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB

db = DynamoDB()

db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET email = :email",
    expression_attribute_values={":email": "new@example.com"}
)
```

## The Four Operations

### 1. SET - Assign or Update Attributes

Use `SET` to create or update attributes.

#### Set Single Attribute

```python
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET email = :email",
    expression_attribute_values={":email": "user@example.com"}
)
```

#### Set Multiple Attributes

```python
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET email = :email, phone = :phone, city = :city",
    expression_attribute_values={
        ":email": "user@example.com",
        ":phone": "555-1234",
        ":city": "San Francisco"
    }
)
```

#### Set with Reserved Words

```python
db.update_item(
    table_name="orders",
    key={"pk": "order#456", "sk": "order#456"},
    update_expression="SET #status = :status, #comment = :comment",
    expression_attribute_names={
        "#status": "status",    # 'status' is reserved
        "#comment": "comment"   # 'comment' is reserved
    },
    expression_attribute_values={
        ":status": "shipped",
        ":comment": "Express delivery"
    }
)
```

#### Set with Math Expressions

```python
# Increment/decrement numbers
db.update_item(
    table_name="counters",
    key={"pk": "counter#1", "sk": "counter#1"},
    update_expression="SET count = count + :inc, price = price - :discount",
    expression_attribute_values={
        ":inc": 5,
        ":discount": 10.50
    }
)
```

#### Set Default Value (if_not_exists)

```python
# Set value only if attribute doesn't exist
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET login_count = if_not_exists(login_count, :default)",
    expression_attribute_values={":default": 0}
)
```

### 2. ADD - Atomic Counters and Sets

Use `ADD` for numeric counters (atomic!) and adding to sets.

#### Atomic Counter (Increment)

```python
# Increment view count atomically (race-condition safe!)
db.update_item(
    table_name="posts",
    key={"pk": "post#123", "sk": "post#123"},
    update_expression="ADD views :inc",
    expression_attribute_values={":inc": 1}
)
```

#### Atomic Counter (Decrement)

```python
# Decrement by using negative number
db.update_item(
    table_name="inventory",
    key={"pk": "product#456", "sk": "product#456"},
    update_expression="ADD stock :dec",
    expression_attribute_values={":dec": -5}
)
```

#### Multiple Counters

```python
# Update multiple metrics atomically
db.update_item(
    table_name="analytics",
    key={"pk": "daily#2024-10-15", "sk": "metrics"},
    update_expression="ADD page_views :pv, clicks :c, conversions :conv",
    expression_attribute_values={
        ":pv": 1,
        ":c": 3,
        ":conv": 1
    }
)
```

#### Add to Set

```python
# Add items to a set (automatically prevents duplicates)
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="ADD tags :new_tags",
    expression_attribute_values={
        ":new_tags": {"premium", "verified", "admin"}
    }
)
```

### 3. REMOVE - Delete Attributes

Use `REMOVE` to delete attributes from an item.

#### Remove Single Attribute

```python
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="REMOVE temp_field"
)
```

#### Remove Multiple Attributes

```python
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="REMOVE temp1, temp2, temp3"
)
```

### 4. DELETE - Remove from Set

Use `DELETE` to remove specific items from a set.

```python
# Remove tags from set
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="DELETE tags :remove_tags",
    expression_attribute_values={
        ":remove_tags": {"premium", "trial"}
    }
)
```

## Combining Operations

You can combine multiple operations in one update:

```python
# Combine SET, ADD, and REMOVE
db.update_item(
    table_name="posts",
    key={"pk": "post#789", "sk": "post#789"},
    update_expression=(
        "SET #status = :status, updated_at = :now "
        "ADD views :inc, likes :like_inc "
        "REMOVE draft_field"
    ),
    expression_attribute_names={
        "#status": "status"
    },
    expression_attribute_values={
        ":status": "published",
        ":now": "2024-10-15T20:00:00Z",
        ":inc": 1,
        ":like_inc": 5
    }
)
```

## List Operations

### Append to List

```python
db.update_item(
    table_name="documents",
    key={"pk": "doc#123", "sk": "doc#123"},
    update_expression="SET #history = list_append(#history, :new_entry)",
    expression_attribute_names={"#history": "history"},
    expression_attribute_values={
        ":new_entry": [{
            "action": "updated",
            "timestamp": "2024-10-15T20:00:00Z",
            "user": "user-456"
        }]
    }
)
```

### Prepend to List

```python
db.update_item(
    table_name="documents",
    key={"pk": "doc#123", "sk": "doc#123"},
    update_expression="SET #history = list_append(:new_entry, #history)",
    expression_attribute_names={"#history": "history"},
    expression_attribute_values={
        ":new_entry": [{"action": "created", "timestamp": "2024-10-14"}]
    }
)
```

## Nested Attributes

Update attributes in nested maps:

```python
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET settings.notifications = :enabled, settings.theme = :theme",
    expression_attribute_values={
        ":enabled": True,
        ":theme": "dark"
    }
)
```

## Return Values

Get the updated item back without a separate read:

```python
response = db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET last_login = :now ADD login_count :inc",
    expression_attribute_values={
        ":now": "2024-10-15T20:00:00Z",
        ":inc": 1
    },
    return_values="ALL_NEW"  # Return updated item
)

updated_user = response["Attributes"]
print(f"Total logins: {updated_user['login_count']}")
```

### Return Value Options

| Option | Returns |
|--------|---------|
| `NONE` | Nothing (default) |
| `ALL_OLD` | Item as it was before update |
| `ALL_NEW` | Item as it is after update |
| `UPDATED_OLD` | Only updated attributes before update |
| `UPDATED_NEW` | Only updated attributes after update |

## Real-World Patterns

### Pattern 1: Atomic View Counter

```python
def increment_post_views(post_id):
    """Increment post view count atomically"""
    db = DynamoDB()

    db.update_item(
        table_name="posts",
        key={"pk": f"post#{post_id}", "sk": f"post#{post_id}"},
        update_expression="ADD views :inc",
        expression_attribute_values={":inc": 1}
    )
```

### Pattern 2: Inventory Reservation

```python
def reserve_inventory(product_id, quantity):
    """Reserve inventory with stock check"""
    db = DynamoDB()

    try:
        response = db.update_item(
            table_name="products",
            key={"pk": f"product#{product_id}", "sk": f"product#{product_id}"},
            update_expression="SET stock = stock - :qty",
            expression_attribute_values={":qty": quantity},
            condition_expression="stock >= :qty",
            return_values="ALL_NEW"
        )

        remaining = response["Attributes"]["stock"]
        return {"success": True, "remaining_stock": remaining}
    except RuntimeError:
        return {"success": False, "error": "Insufficient stock"}
```

### Pattern 3: Activity Log

```python
def log_activity(user_id, action):
    """Append activity to user's log"""
    db = DynamoDB()

    db.update_item(
        table_name="users",
        key={"pk": f"user#{user_id}", "sk": f"user#{user_id}"},
        update_expression="SET activity_log = list_append(activity_log, :entry)",
        expression_attribute_values={
            ":entry": [{
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
    )
```

### Pattern 4: Status Transition

```python
def ship_order(order_id):
    """Ship order only if status is 'pending'"""
    db = DynamoDB()

    try:
        db.update_item(
            table_name="orders",
            key={"pk": f"order#{order_id}", "sk": f"order#{order_id}"},
            update_expression="SET #status = :shipped, shipped_at = :now",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={
                ":shipped": "shipped",
                ":now": datetime.utcnow().isoformat(),
                ":pending": "pending"
            },
            condition_expression="#status = :pending"
        )
        return {"success": True}
    except RuntimeError:
        return {"success": False, "error": "Order not in pending status"}
```

### Pattern 5: Optimistic Locking

```python
def update_document_with_version(doc_id, content, expected_version):
    """Update document with version check"""
    db = DynamoDB()

    try:
        response = db.update_item(
            table_name="documents",
            key={"pk": f"doc#{doc_id}", "sk": f"doc#{doc_id}"},
            update_expression="SET content = :content, version = version + :inc",
            expression_attribute_values={
                ":content": content,
                ":inc": 1,
                ":expected_version": expected_version
            },
            condition_expression="version = :expected_version",
            return_values="ALL_NEW"
        )

        new_version = response["Attributes"]["version"]
        return {"success": True, "version": new_version}
    except RuntimeError:
        return {"success": False, "error": "Version conflict"}
```

## Best Practices

### 1. Use Updates Instead of Put for Modifications

```python
# ✅ Good: Update only what changed
db.update_item(
    table_name="users",
    key={"pk": "user#123", "sk": "user#123"},
    update_expression="SET email = :email",
    expression_attribute_values={":email": "new@example.com"}
)

# ❌ Bad: Replace entire item for one field change
user = db.get(...)["Item"]
user["email"] = "new@example.com"
db.save(item=user, table_name="users")
```

### 2. Use ADD for Counters

```python
# ✅ Good: Atomic counter (race-condition safe)
db.update_item(
    update_expression="ADD views :inc",
    expression_attribute_values={":inc": 1}
)

# ❌ Bad: Read-modify-write (race conditions!)
item = db.get(...)["Item"]
item["views"] += 1
db.save(item=item, table_name="table")
```

### 3. Use Conditions for Data Integrity

```python
# ✅ Good: Check stock before decrementing
db.update_item(
    update_expression="SET stock = stock - :qty",
    expression_attribute_values={":qty": 5},
    condition_expression="stock >= :qty"
)

# ❌ Bad: No validation (could go negative!)
db.update_item(
    update_expression="SET stock = stock - :qty",
    expression_attribute_values={":qty": 5}
)
```

### 4. Use return_values to Avoid Extra Reads

```python
# ✅ Good: Get updated values in one call
response = db.update_item(
    update_expression="ADD count :inc",
    expression_attribute_values={":inc": 1},
    return_values="ALL_NEW"
)
count = response["Attributes"]["count"]

# ❌ Bad: Two separate calls
db.update_item(...)
response = db.get(...)  # Extra network call
count = response["Item"]["count"]
```

### 5. Combine Operations When Possible

```python
# ✅ Good: One update with multiple operations
db.update_item(
    update_expression="SET #status = :status ADD views :inc REMOVE temp",
    expression_attribute_names={"#status": "status"},
    expression_attribute_values={":status": "active", ":inc": 1}
)

# ❌ Bad: Multiple separate updates
db.update_item(update_expression="SET #status = :status", ...)
db.update_item(update_expression="ADD views :inc", ...)
db.update_item(update_expression="REMOVE temp")
```

## Common Mistakes to Avoid

### 1. Forgetting Expression Attribute Names for Reserved Words

```python
# ❌ Wrong: 'status' is reserved
db.update_item(
    update_expression="SET status = :status",
    expression_attribute_values={":status": "active"}
)

# ✅ Correct: Use expression attribute names
db.update_item(
    update_expression="SET #status = :status",
    expression_attribute_names={"#status": "status"},
    expression_attribute_values={":status": "active"}
)
```

### 2. Using SET for Counters

```python
# ❌ Wrong: Race conditions possible
db.update_item(
    update_expression="SET count = count + :inc",
    expression_attribute_values={":inc": 1}
)

# ✅ Correct: Use ADD for atomic counters
db.update_item(
    update_expression="ADD count :inc",
    expression_attribute_values={":inc": 1}
)
```

### 3. Not Handling Conditional Failures

```python
# ❌ Wrong: No error handling
db.update_item(
    update_expression="SET stock = stock - :qty",
    condition_expression="stock >= :qty",
    expression_attribute_values={":qty": 5}
)

# ✅ Correct: Handle condition failures
try:
    db.update_item(...)
except RuntimeError:
    print("Insufficient stock")
```

## Performance & Cost

### WCU Consumption

Update expressions consume WCUs based on item size:
- 1 KB item = 1 WCU
- Same cost as `put_item`
- But more efficient (only send changes, not entire item)

### Network Efficiency

| Operation | Data Sent | Network Calls |
|-----------|-----------|---------------|
| **Update Expression** | Only changes | 1 |
| **Read-Modify-Write** | Entire item × 2 | 2 (get + put) |

## Summary

**Key Takeaways:**

1. ✅ **Four operations**: SET, ADD, REMOVE, DELETE
2. ✅ **Atomic counters** use ADD (race-condition safe)
3. ✅ **Combine operations** for efficiency
4. ✅ **Use conditions** for data integrity
5. ✅ **return_values** avoids extra reads
6. ✅ **More efficient** than read-modify-write
7. ⚠️ **Reserved words** need expression attribute names

**When to Use:**
- Modifying specific attributes
- Atomic counters (views, likes, inventory)
- List operations (append, prepend)
- Set operations (tags, permissions)
- Conditional updates with integrity checks

## Related Guides

- [Conditional Writes](9-guide-conditional-writes.md) - Using conditions with updates
- [Transactions](8-guide-transactions.md) - Atomic multi-item operations
- [Creating Service Layers](3-guide-service-layers.md) - Using updates in services

## Example Code

Complete working examples:
- [`examples/dynamodb/update_expressions_example.py`](../../../examples/dynamodb/update_expressions_example.py)
- [`tests/unit/dynamodb_tests/dynamodb_update_expressions_test.py`](../../../tests/unit/dynamodb_tests/dynamodb_update_expressions_test.py)
