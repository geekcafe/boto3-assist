# Transactions: Atomic Multi-Item Operations

## Introduction

DynamoDB transactions provide **ACID guarantees** for operations spanning multiple items. All operations in a transaction succeed together or fail together - no partial updates.

This is critical for:
- Financial operations (transfers, payments)
- Inventory management
- User registration with uniqueness checks
- Any operation requiring data consistency

This guide covers:
- `transact_write_items`: Atomic writes
- `transact_get_items`: Consistent reads
- When to use transactions vs batch operations
- Real-world patterns and best practices

## Why Transactions?

### The Problem Without Transactions

```python
# ❌ Without transactions - can partially fail
db.update_item(...)  # Deduct from account A - SUCCESS
db.update_item(...)  # Add to account B - FAILS!
# Result: Money disappeared! 💸
```

### The Solution: Transactions

```python
# ✅ With transactions - all-or-nothing
operations = [
    {'Update': {...}},  # Deduct from account A
    {'Update': {...}}   # Add to account B
]
db.transact_write_items(operations=operations)
# Result: Both succeed or both fail (atomic)
```

## transact_write_items: Atomic Writes

### Basic Usage

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB

db = DynamoDB()

operations = [
    {
        'Put': {
            'TableName': 'users',
            'Item': {
                'pk': 'user#001',
                'sk': 'user#001',
                'name': 'Alice'
            }
        }
    },
    {
        'Put': {
            'TableName': 'users',
            'Item': {
                'pk': 'user#002',
                'sk': 'user#002',
                'name': 'Bob'
            }
        }
    }
]

response = db.transact_write_items(operations=operations)
# Both users created, or neither created
```

### Supported Operations

Transactions support four operation types:

#### 1. Put - Create or Replace

```python
{
    'Put': {
        'TableName': 'users',
        'Item': {'pk': 'user#1', 'sk': 'user#1', 'name': 'Alice'},
        'ConditionExpression': 'attribute_not_exists(pk)'  # Optional condition
    }
}
```

#### 2. Update - Modify Attributes

```python
{
    'Update': {
        'TableName': 'accounts',
        'Key': {'pk': 'account#1', 'sk': 'account#1'},
        'UpdateExpression': 'SET balance = balance + :amount',
        'ExpressionAttributeValues': {':amount': 100},
        'ConditionExpression': 'attribute_exists(pk)'  # Optional condition
    }
}
```

#### 3. Delete - Remove Item

```python
{
    'Delete': {
        'TableName': 'sessions',
        'Key': {'pk': 'session#123', 'sk': 'session#123'},
        'ConditionExpression': 'expired = :true',  # Optional condition
        'ExpressionAttributeValues': {':true': True}
    }
}
```

#### 4. ConditionCheck - Validate Without Modifying

```python
{
    'ConditionCheck': {
        'TableName': 'users',
        'Key': {'pk': 'user#1', 'sk': 'user#1'},
        'ConditionExpression': '#status = :active',
        'ExpressionAttributeNames': {'#status': 'status'},
        'ExpressionAttributeValues': {':active': 'active'}
    }
}
```

## Real-World Examples

### Example 1: Money Transfer

```python
def transfer_money(from_account, to_account, amount):
    """Transfer money atomically between accounts"""
    db = DynamoDB()

    operations = [
        {
            'Update': {
                'TableName': 'accounts',
                'Key': {'pk': f'account#{from_account}', 'sk': f'account#{from_account}'},
                'UpdateExpression': 'SET balance = balance - :amount',
                'ConditionExpression': 'balance >= :amount',  # No overdraft!
                'ExpressionAttributeValues': {':amount': amount}
            }
        },
        {
            'Update': {
                'TableName': 'accounts',
                'Key': {'pk': f'account#{to_account}', 'sk': f'account#{to_account}'},
                'UpdateExpression': 'SET balance = balance + :amount',
                'ExpressionAttributeValues': {':amount': amount}
            }
        }
    ]

    try:
        db.transact_write_items(operations=operations)
        return True
    except Exception as e:
        print(f"Transfer failed: {e}")
        return False
```

### Example 2: User Registration (Uniqueness Check)

```python
def register_user(user_id, email):
    """Register user ensuring email uniqueness"""
    db = DynamoDB()

    operations = [
        {
            'Put': {
                'TableName': 'users',
                'Item': {
                    'pk': f'user#{user_id}',
                    'sk': f'user#{user_id}',
                    'email': email
                },
                'ConditionExpression': 'attribute_not_exists(pk)'  # User ID unique
            }
        },
        {
            'Put': {
                'TableName': 'users',
                'Item': {
                    'pk': 'emails#',
                    'sk': f'email#{email}',
                    'user_id': user_id
                },
                'ConditionExpression': 'attribute_not_exists(sk)'  # Email unique
            }
        }
    ]

    try:
        db.transact_write_items(operations=operations)
        return True
    except Exception as e:
        print(f"Registration failed: {e}")
        return False
```

### Example 3: Inventory Reservation

```python
def reserve_inventory(order_id, items):
    """Reserve inventory for order atomically"""
    db = DynamoDB()

    operations = []

    # Decrement inventory for each item
    for product_id, quantity in items:
        operations.append({
            'Update': {
                'TableName': 'products',
                'Key': {'pk': f'product#{product_id}', 'sk': f'product#{product_id}'},
                'UpdateExpression': 'SET stock = stock - :qty',
                'ConditionExpression': 'stock >= :qty',  # Must have stock!
                'ExpressionAttributeValues': {':qty': quantity}
            }
        })

    # Create order
    operations.append({
        'Put': {
            'TableName': 'orders',
            'Item': {
                'pk': f'order#{order_id}',
                'sk': f'order#{order_id}',
                'items': [{'product_id': pid, 'qty': qty} for pid, qty in items],
                'status': 'reserved'
            }
        }
    })

    try:
        db.transact_write_items(operations=operations)
        return True
    except Exception as e:
        print(f"Reservation failed: {e}")
        return False
```

### Example 4: Optimistic Locking

```python
def update_document_with_version_check(doc_id, new_content):
    """Update document with optimistic locking"""
    db = DynamoDB()

    # Read current version
    response = db.get(
        key={'pk': f'doc#{doc_id}', 'sk': f'doc#{doc_id}'},
        table_name='documents'
    )

    current_version = response['Item']['version']

    # Update with version check
    operations = [{
        'Update': {
            'TableName': 'documents',
            'Key': {'pk': f'doc#{doc_id}', 'sk': f'doc#{doc_id}'},
            'UpdateExpression': 'SET content = :content, version = :new_ver',
            'ConditionExpression': 'version = :expected_ver',
            'ExpressionAttributeValues': {
                ':content': new_content,
                ':new_ver': current_version + 1,
                ':expected_ver': current_version
            }
        }
    }]

    try:
        db.transact_write_items(operations=operations)
        return True
    except Exception as e:
        print("Version conflict - document was modified by another user")
        return False
```

## transact_get_items: Consistent Reads

Get multiple items with strong consistency:

```python
keys = [
    {
        'Key': {'pk': 'user#123', 'sk': 'user#123'},
        'TableName': 'users'
    },
    {
        'Key': {'pk': 'account#123', 'sk': 'account#123'},
        'TableName': 'accounts'
    }
]

response = db.transact_get_items(keys=keys)
items = response['Items']

# All items retrieved from same consistent snapshot
```

### With Projection

```python
keys = [
    {
        'Key': {'pk': 'user#123', 'sk': 'user#123'},
        'TableName': 'users',
        'ProjectionExpression': 'id,#name,email',
        'ExpressionAttributeNames': {'#name': 'name'}
    }
]

response = db.transact_get_items(keys=keys)
```

## Limits and Constraints

### Transaction Limits

| Limit | Value |
|-------|-------|
| Max operations per transaction | 100 |
| Max item size | 400 KB |
| Max total transaction size | 4 MB |
| Max transaction duration | N/A (synchronous) |

### Important Constraints

1. **Cannot target same item twice**
   ```python
   # ❌ This will fail
   operations = [
       {'Update': {'Key': {'pk': 'item#1', 'sk': 'item#1'}, ...}},
       {'Update': {'Key': {'pk': 'item#1', 'sk': 'item#1'}, ...}}  # Same item!
   ]
   ```

2. **All operations must succeed**
   - One failure = entire transaction rolls back
   - No partial updates

3. **Strongly consistent reads only**
   - `transact_get_items` always uses strong consistency
   - Costs 2x RCUs compared to eventually consistent

4. **Cannot combine get and write in one transaction**
   - Use `transact_get_items` OR `transact_write_items`
   - Not both together

## Cost Considerations

### Write Costs

Transactions cost **2x WCUs** compared to regular writes:

```
Regular Put: 1 item × 1 KB = 1 WCU
Transaction Put: 1 item × 1 KB = 2 WCUs
```

### Read Costs

Transaction gets cost **2x RCUs** (always strongly consistent):

```
Regular Get (eventually consistent): 1 item × 4 KB = 0.5 RCU
Regular Get (strongly consistent): 1 item × 4 KB = 1 RCU
Transaction Get: 1 item × 4 KB = 2 RCUs
```

### When Cost is Worth It

✅ **Use transactions when:**
- Data consistency is critical
- Failures would corrupt data
- Business logic requires atomicity
- Examples: payments, inventory, user registration

❌ **Avoid transactions when:**
- Operations are independent
- Eventual consistency is acceptable
- Batch operations suffice
- Examples: logging, metrics, bulk imports

## Batch vs Transactions

| Feature | Batch Operations | Transactions |
|---------|------------------|--------------|
| **Atomicity** | No | Yes (all-or-nothing) |
| **Conditions** | No | Yes |
| **Max items** | Get: 100, Write: 25 | 100 |
| **Cost** | 1x | 2x |
| **Speed** | Fast | Slower |
| **Use case** | Bulk operations | Critical operations |

### Decision Flow

```
Need atomicity (all-or-nothing)?
    Yes → Use transactions
    No → Need conditions?
        Yes → Use individual operations
        No → Use batch operations
```

## Error Handling

### Transaction Failures

```python
try:
    db.transact_write_items(operations=operations)
    print("✅ Transaction successful")

except RuntimeError as e:
    # Transaction cancelled (condition failed, validation error)
    print(f"Transaction failed: {e}")
    # Could retry or handle gracefully

except ValueError as e:
    # Invalid parameters (too many operations, etc.)
    print(f"Invalid request: {e}")

except Exception as e:
    # Other errors (throttling, service errors)
    print(f"Unexpected error: {e}")
    # Implement retry with backoff
```

### Handling Specific Failures

```python
try:
    db.transact_write_items(operations=operations)
except RuntimeError as e:
    error_msg = str(e)

    if "ConditionalCheckFailed" in error_msg:
        print("Condition not met (e.g., insufficient balance)")
    elif "ValidationException" in error_msg:
        print("Invalid operation structure")
    elif "DuplicateItem" in error_msg:
        print("Tried to target same item twice")
    else:
        print(f"Other failure: {error_msg}")
```

## Best Practices

### 1. Keep Transactions Small

```python
# ✅ Good: 2-5 operations
operations = [op1, op2, op3]

# ❌ Bad: 50+ operations (use batch if no atomicity needed)
operations = [op1, op2, ..., op50]
```

### 2. Use Idempotency Tokens for Retries

```python
import uuid

token = str(uuid.uuid4())

db.transact_write_items(
    operations=operations,
    client_request_token=token  # Safe to retry with same token
)
```

### 3. Add Conditions for Data Integrity

```python
# ✅ Good: Prevent overdraft
{
    'Update': {
        'UpdateExpression': 'SET balance = balance - :amount',
        'ConditionExpression': 'balance >= :amount'  # ← Important!
    }
}

# ❌ Bad: No validation
{
    'Update': {
        'UpdateExpression': 'SET balance = balance - :amount'
        # Could result in negative balance!
    }
}
```

### 4. Use ConditionCheck for Read-Modify-Write

```python
operations = [
    {
        'ConditionCheck': {  # Verify state before modifying
            'Key': {'pk': 'user#1', 'sk': 'user#1'},
            'ConditionExpression': '#status = :active'
        }
    },
    {
        'Update': {  # Only runs if check passes
            'Key': {'pk': 'order#1', 'sk': 'order#1'},
            'UpdateExpression': 'SET user_id = :uid'
        }
    }
]
```

### 5. Log Transaction Details

```python
import logging

logger = logging.getLogger(__name__)

try:
    logger.info(f"Starting transaction with {len(operations)} operations")
    response = db.transact_write_items(operations=operations)
    logger.info("Transaction committed successfully")
except Exception as e:
    logger.error(f"Transaction failed: {e}", extra={'operations': operations})
    raise
```

## Summary

**Key Takeaways:**

1. ✅ **Transactions provide ACID guarantees** - all succeed or all fail
2. ✅ **Four operation types**: Put, Update, Delete, ConditionCheck
3. ✅ **Maximum 100 operations** per transaction
4. ✅ **Strongly consistent** - always up-to-date data
5. ⚠️ **Costs 2x** compared to regular operations
6. ⚠️ **Cannot target same item twice** in one transaction
7. ⚠️ **Cannot mix get and write** in same transaction

**When to Use:**
- Money transfers
- Inventory management
- User registration with uniqueness
- Any operation requiring data consistency
- Optimistic locking patterns

**When to Avoid:**
- Independent operations
- Bulk data imports
- Logging/metrics
- When eventual consistency is acceptable

## Related Guides

- [Batch Operations](7-guide-batch-operations.md) - When you don't need atomicity
- [Creating Service Layers](3-guide-service-layers.md) - Use transactions in services
- [Testing with Moto](4-guide-testing-with-moto.md) - Test transactions locally

## Example Code

Complete working examples:
- [`examples/dynamodb/transactions_example.py`](../../../examples/dynamodb/transactions_example.py)
- [`tests/unit/dynamodb_tests/dynamodb_transactions_test.py`](../../../tests/unit/dynamodb_tests/dynamodb_transactions_test.py)
