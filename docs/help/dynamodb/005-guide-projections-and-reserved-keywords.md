# Projection Expressions and Reserved Keywords

## Introduction

When working with DynamoDB, you'll frequently need to control which attributes are returned in query results. This is where **projection expressions** come in. Additionally, DynamoDB has hundreds of reserved keywords that can trip you up if you're not aware of them.

This guide covers:
- What projection expressions are and why to use them
- DynamoDB's reserved keyword problem
- How to handle reserved keywords with expression attribute names
- boto3-assist patterns for defining projections in models
- Testing strategies with projections

## What are Projection Expressions?

**Projection expressions** control which attributes DynamoDB returns in query results. By default, DynamoDB returns all attributes for each item. Projections let you request only specific attributes, reducing data transfer and improving performance.

### Why Use Projections

- ✅ **Reduce data transfer costs** - Fewer bytes over the network
- ✅ **Improve query performance** - Less data to transfer and parse
- ✅ **Reduce consumed capacity** - Less data means fewer read capacity units
- ✅ **Hide sensitive data** - Don't retrieve fields you don't need
- ✅ **Cleaner code** - Focus on the data you actually use
- ✅ **Better security** - Principle of least privilege applies to data access

### Basic Projection Example

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.models.user_model import User

db = DynamoDB()
user_model = User(id="user-123")

# Without projection - returns ALL attributes
response = db.get(
    model=user_model,
    table_name="users"
)
# Returns: {
#   id, first_name, last_name, email, status, type, company_name,
#   pk, sk, gsi0_pk, gsi0_sk, gsi1_pk, gsi1_sk, created_at, modified_at, ...
# }

# With projection - returns ONLY specified attributes
response = db.get(
    model=user_model,
    table_name="users",
    projection_expression="id,first_name,last_name,email"
)
# Returns: {id, first_name, last_name, email}
```

**Result:**
- Without projection: ~500 bytes transferred
- With projection: ~100 bytes transferred (80% reduction!)

## DynamoDB Reserved Keywords - The Gotcha!

### The Problem

DynamoDB has [over 500 reserved keywords](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html) that cannot be used directly in expressions. These are words DynamoDB uses internally for its query language.

**Common reserved keywords include:**
- `name`
- `status`
- `type`
- `date`
- `time`
- `timestamp`
- `data`
- `value`
- `count`
- `size`
- `metadata`
- `comment`
- `group`
- `user`
- `order`
- And 500+ more...

### What Happens if You Use Them

If you try to use reserved keywords directly in expressions, DynamoDB throws an error:

```python
# ❌ This will FAIL!
projection_expression = "id,name,status,type"

response = db.get(
    model=user_model,
    table_name="users",
    projection_expression=projection_expression
)

# Error: ValidationException
# "Invalid ProjectionExpression: Attribute name is a reserved keyword;
#  reserved keyword: name"
```

This error is frustrating because:
- It's not obvious which word is reserved
- Common attribute names are often reserved
- The error happens at runtime, not compile time

## The Solution: Expression Attribute Names

You must use **expression attribute names** to alias reserved keywords. This is DynamoDB's way of letting you use any attribute name by providing a placeholder.

### How It Works

```python
# ✅ This works!
projection_expression = "id,#name,#status,#type"
expression_attribute_names = {
    "#name": "name",      # Map placeholder to actual attribute
    "#status": "status",
    "#type": "type"
}

response = db.get(
    model=user_model,
    table_name="users",
    projection_expression=projection_expression,
    expression_attribute_names=expression_attribute_names
)
```

**The process:**
1. Use `#placeholder` in your expression (e.g., `#name`, `#status`)
2. Map the placeholder to the actual attribute name in `expression_attribute_names`
3. DynamoDB replaces placeholders with actual names during execution

### Placeholder Naming Conventions

You can name placeholders anything, but common conventions:

```python
# Hash + attribute name (most common)
"#name": "name"
"#status": "status"

# Hash + abbreviated name
"#n": "name"
"#s": "status"

# Hash + descriptive name
"#user_name": "name"
"#order_status": "status"

# Any valid identifier works
"#x": "name"
"#abc123": "status"
```

**Recommendation**: Use `#` + attribute name for clarity (e.g., `#name`, `#status`).

## boto3-assist: Model-Based Projection Patterns

boto3-assist models support defining projection expressions once and reusing them throughout your application.

### Defining Projections in Models

```python
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey

class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.first_name = None
        self.last_name = None
        self.email = None
        self.status = None      # Reserved keyword!
        self.type = None        # Reserved keyword!
        self.company_name = None

        self._setup_indexes()

        # Define projection expression ONCE in the model
        self.projection_expression = (
            "id,first_name,last_name,email,#type,#status,company_name"
        )
        # Handle reserved keywords
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type"
        }

    def _setup_indexes(self):
        # ... index setup code ...
        pass
```

### Using Model Projections in Services

```python
class UserService:
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name

    def get_user(self, user_id: str, include_all_fields: bool = False):
        """
        Get user with optional projection filtering

        Args:
            user_id: The user ID
            include_all_fields: If True, return ALL attributes (no projection)
                               If False, use model's projection (filtered fields)
        """
        model = User(id=user_id)

        if include_all_fields:
            # Get ALL attributes (no projection)
            response = self.db.get(
                model=model,
                table_name=self.table_name
            )
        else:
            # Use model's projection (only specific fields)
            response = self.db.get(
                model=model,
                table_name=self.table_name,
                projection_expression=model.projection_expression,
                expression_attribute_names=model.projection_expression_attribute_names
            )

        return response.get("Item")
```

### Benefits of This Pattern

1. **Define Once, Use Everywhere** - Projection logic centralized in model
2. **Type Safety** - Model defines what attributes exist
3. **Consistency** - Same projection used across all service methods
4. **Easy Updates** - Change projection in one place
5. **Self-Documenting** - Model shows what fields are typically retrieved

## Testing with Projections

### The Testing Challenge

When writing tests, you often want to verify the **key structure** (pk, sk, GSI keys) of your items. However, if projections are enabled, these keys won't be in the response!

```python
# Service uses projection
user = service.get_user("user-001")  # Uses projection

# ❌ This test will FAIL if projection is active
assert user["pk"] == "user#user-001"  # KeyError: 'pk' not in response
```

### Solution: Toggle Projections in Tests

Design your services to optionally disable projections:

```python
class OrderService:
    def get(self, order_id: str, include_order_items: bool = False,
            do_projections: bool = True):
        """
        Get order with optional items

        Args:
            order_id: The order ID
            include_order_items: Include order items in response
            do_projections: Use projection expressions (turn off for testing)
        """
        model = Order(id=order_id)

        # Determine projection based on flag
        projection = None
        attr_names = None
        if do_projections:
            projection = model.projection_expression
            attr_names = model.projection_expression_attribute_names

        if include_order_items:
            key = model.indexes.primary.key(include_sort_key=False)
            response = self.db.query(
                key=key,
                table_name=self.table_name,
                projection_expression=projection,
                expression_attribute_names=attr_names
            )
        else:
            response = self.db.get(
                model=model,
                table_name=self.table_name,
                projection_expression=projection,
                expression_attribute_names=attr_names
            )

        return response
```

### Test Example

```python
import unittest
from moto import mock_aws
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.services.order_service import OrderService

@mock_aws
class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.db = DynamoDB()
        self.table_name = "test-orders"
        # ... create table ...
        self.service = OrderService(self.db, self.table_name)

    def test_verify_key_structure(self):
        """Verify pk/sk structure by turning off projections"""
        # Create order
        self.service.create_order({
            "id": "order-001",
            "user_id": "user-123",
            "total": 100.00
        })

        # Get with ALL fields (do_projections=False)
        result = self.service.get(
            order_id="order-001",
            include_order_items=False,
            do_projections=False  # ← Turns off projection to see keys
        )

        # Now we can verify key structure
        order_data = result["Item"]
        self.assertEqual(order_data["pk"], "order#order-001")
        self.assertEqual(order_data["sk"], "order#order-001")
        self.assertEqual(order_data["id"], "order-001")
        self.assertEqual(order_data["total"], 100.00)

    def test_projection_works(self):
        """Verify projection filters fields correctly"""
        # Create order
        self.service.create_order({
            "id": "order-002",
            "user_id": "user-123",
            "total": 200.00
        })

        # Get with projection (do_projections=True)
        result = self.service.get(
            order_id="order-002",
            include_order_items=False,
            do_projections=True  # ← Uses projection
        )

        order_data = result["Item"]

        # Should have projected fields
        self.assertIn("id", order_data)
        self.assertIn("total", order_data)

        # Should NOT have keys (not in projection)
        self.assertNotIn("pk", order_data)
        self.assertNotIn("sk", order_data)
```

See the complete example in [`tests/unit/examples_test/order_service_test.py`](../../../tests/unit/examples_test/order_service_test.py).

## Common Reserved Keywords Reference

Here are the most frequently encountered reserved keywords:

| Keyword | Category | Alias Example | Notes |
|---------|----------|---------------|-------|
| `name` | Common | `#name` | Very common attribute name |
| `status` | Common | `#status` | Common for state tracking |
| `type` | Common | `#type` | Common for entity types |
| `data` | Common | `#data` | Common for generic data storage |
| `value` | Common | `#value` | Common for key-value patterns |
| `timestamp` | Time | `#timestamp` | Common for time tracking |
| `date` | Time | `#date` | Common for date fields |
| `time` | Time | `#time` | Common for time fields |
| `count` | Numeric | `#count` | Common for counters |
| `size` | Numeric | `#size` | Common for measurements |
| `order` | Business | `#order` | Common entity type |
| `user` | Business | `#user` | Common entity type |
| `group` | Business | `#group` | Common for grouping |
| `comment` | Content | `#comment` | Common for user content |
| `metadata` | System | `#metadata` | Common for additional info |

**Pro Tip**: When in doubt, use a placeholder! It doesn't hurt to alias an attribute even if it's not reserved. Better safe than getting a runtime error in production.

## Projection Expression Syntax

### Simple Attributes

```python
# Basic list of attributes
projection_expression = "id,email,first_name,last_name"
```

### Nested Attributes

Use **dot notation** for nested objects:

```python
# Nested attributes
projection_expression = "id,address.city,address.state,address.zip"

# Multiple levels
projection_expression = "id,profile.contact.email,profile.contact.phone"
```

### List Elements

Use **bracket notation** for list indices:

```python
# Specific list elements
projection_expression = "id,tags[0],tags[1],tags[2]"

# Nested lists
projection_expression = "id,orders[0].total,orders[1].total"
```

### With Reserved Keywords

Use **# prefix** for reserved keywords:

```python
# Reserved keywords
projection_expression = "id,#name,#status,#type"
expression_attribute_names = {
    "#name": "name",
    "#status": "status",
    "#type": "type"
}
```

### Mixed Examples

```python
# Everything together
projection_expression = "id,#name,address.city,tags[0],#status"
expression_attribute_names = {
    "#name": "name",
    "#status": "status"
}

# Complex nested + reserved
projection_expression = "id,profile.#data.#value,orders[0].#status"
expression_attribute_names = {
    "#data": "data",
    "#value": "value",
    "#status": "status"
}
```

## Projection Expressions in Queries

Projections work with all DynamoDB operations:

### Get Item

```python
response = db.get(
    model=model,
    table_name=table_name,
    projection_expression="id,#name,email",
    expression_attribute_names={"#name": "name"}
)
```

### Query

```python
response = db.query(
    key=key_condition,
    table_name=table_name,
    index_name="gsi0",
    projection_expression="id,#name,#status",
    expression_attribute_names={
        "#name": "name",
        "#status": "status"
    }
)
```

### Scan

```python
response = db.scan(
    table_name=table_name,
    projection_expression="id,email,#type",
    expression_attribute_names={"#type": "type"}
)
```

## Best Practices

### 1. Define Projections in Models

```python
# ✅ Good: Centralized in model
class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        # ... attributes ...
        self.projection_expression = "id,#name,email"
        self.projection_expression_attribute_names = {"#name": "name"}

# ❌ Bad: Repeated in every service method
def get_user(self, user_id):
    projection = "id,#name,email"  # Duplicated everywhere
    attr_names = {"#name": "name"}
```

### 2. Handle Reserved Keywords Proactively

```python
# ✅ Good: Add aliases even before hitting errors
self.projection_expression_attribute_names = {
    "#name": "name",
    "#status": "status",
    "#type": "type",
    "#data": "data"
}

# ❌ Bad: Wait until production error
self.projection_expression = "id,name,status,type"  # Will fail!
```

### 3. Provide Toggle for Testing

```python
# ✅ Good: Allow turning off projections
def get_user(self, user_id, use_projection=True):
    if use_projection:
        # Use projection
    else:
        # Get all fields for testing

# ❌ Bad: Always use projection
def get_user(self, user_id):
    # Always uses projection - can't test keys!
```

### 4. Keep Projections Minimal

```python
# ✅ Good: Only fields you need
projection_expression = "id,email,first_name,last_name"

# ❌ Bad: Everything except one field
projection_expression = "id,email,first_name,last_name,address,phone,created_at,..."
# If you need this many fields, don't use projection!
```

### 5. Document Your Projections

```python
class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        # ... attributes ...

        # Projection includes core user fields for list/display operations
        # Excludes: pk, sk, GSI keys, internal metadata
        # Reserved keywords handled: name, status, type
        self.projection_expression = (
            "id,first_name,last_name,email,#type,#status"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type"
        }
```

## Debugging Projections

### Common Issues

**Issue 1: Reserved keyword error**
```
ValidationException: Invalid ProjectionExpression:
Attribute name is a reserved keyword; reserved keyword: name
```

**Solution**: Add expression attribute name
```python
projection_expression = "id,#name"  # Use #name instead of name
expression_attribute_names = {"#name": "name"}
```

---

**Issue 2: Missing attributes in response**
```python
# Expected 'pk' in response but it's not there
```

**Solution**: Either add to projection or turn off projection
```python
# Option 1: Add to projection
projection_expression = "id,pk,sk,#name"

# Option 2: Turn off projection
response = db.get(model=model, table_name=table_name)  # No projection
```

---

**Issue 3: Attribute doesn't exist**
```
ValidationException: The projection expression refers to an attribute
that does not exist in the item
```

**Solution**: Check spelling or make attribute optional
```python
# This is OK - DynamoDB ignores attributes that don't exist
projection_expression = "id,email,optional_field"
```

### Debug Logging

Add logging to see what's being sent:

```python
import json
import logging

logging.basicConfig(level=logging.DEBUG)

projection_expression = "id,#name,#status"
expression_attribute_names = {"#name": "name", "#status": "status"}

print("Projection Expression:", projection_expression)
print("Expression Attribute Names:", json.dumps(expression_attribute_names, indent=2))

response = db.get(
    model=model,
    table_name=table_name,
    projection_expression=projection_expression,
    expression_attribute_names=expression_attribute_names
)

print("Returned fields:", list(response.get("Item", {}).keys()))
print("Full response:", json.dumps(response.get("Item"), indent=2, default=str))
```

## Performance Considerations

### Data Transfer Savings

Real-world example from a user table:

```python
# Full item: ~2 KB
{
    "id": "user-123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "status": "active",
    "type": "premium",
    "company_name": "Acme Corp",
    "pk": "user#user-123",
    "sk": "user#user-123",
    "gsi0_pk": "users#",
    "gsi0_sk": "name#Doe#John",
    "gsi1_pk": "active_users#",
    "gsi1_sk": "user#user-123",
    "created_at": "2024-01-01T00:00:00Z",
    "modified_at": "2024-10-15T00:00:00Z",
    "last_login": "2024-10-15T20:00:00Z",
    # ... more fields
}

# With projection: ~200 bytes
{
    "id": "user-123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
}

# Savings: 90% reduction in data transfer!
```

**At scale:**
- 1,000 queries/sec
- Without projection: 2 MB/sec = 5.2 TB/month
- With projection: 200 KB/sec = 520 GB/month
- **Savings: 4.7 TB/month** (90% cost reduction!)

### When NOT to Use Projections

Don't use projections if:
- You need most/all attributes anyway
- The item is already small (<500 bytes)
- You're doing a one-time data export
- Testing key structure

## Summary

**Key Takeaways:**

1. ✅ **Use projections** to reduce data transfer and improve performance
2. ✅ **Watch for reserved keywords** - DynamoDB has 500+ of them
3. ✅ **Use expression attribute names** with `#placeholder` syntax
4. ✅ **Define projections in models** for reusability
5. ✅ **Toggle projections in tests** to verify key structure
6. ✅ **Document your projections** for maintainability

**Common Patterns:**
- Model defines projection once
- Service uses model's projection by default
- Tests can disable projection with a flag
- Production code always uses projection for efficiency

## Related Guides

- [Testing with Moto](4-guide-testing-with-moto.md) - How to test with projections
- [Defining Models](2-guide-defining-models.md) - Where to define projection expressions
- [Creating Service Layers](3-guide-service-layers.md) - How to use projections in services

## References

- [AWS DynamoDB Reserved Words](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html) - Complete list
- [AWS Projection Expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ProjectionExpressions.html) - Official docs
- [AWS Expression Attribute Names](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ExpressionAttributeNames.html) - Official docs
