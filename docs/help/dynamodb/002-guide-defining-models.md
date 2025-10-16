# Defining DynamoDB Models with boto3-assist

## Introduction

In boto3-assist, models are **data transfer objects (DTOs)** that represent your business entities. They are responsible for:
- Defining the structure of your data
- Managing primary keys and GSI (Global Secondary Index) keys
- Serializing data to/from DynamoDB format
- Providing type safety and structure

**Important**: Models do NOT interact with the database directly. That's what service layers are for. Models are pure data structures with serialization logic.

This guide will walk you through creating effective DynamoDB models using boto3-assist.

## The Foundation: DynamoDBModelBase

All models inherit from `DynamoDBModelBase`, which provides:
- Automatic serialization/deserialization
- Index management (primary and GSI keys)
- Helper methods for working with DynamoDB
- Decimal conversion utilities

### Basic Model Structure

```python
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey

class Product(DynamoDBModelBase):
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        price: float = 0.0,
        description: Optional[str] = None
    ):
        # Always call super().__init__() first
        super().__init__()
        
        # Define your attributes
        self.id = id
        self.name = name
        self.price = price
        self.description = description
        
        # Setup indexes last
        self._setup_indexes()
    
    def _setup_indexes(self):
        # Index definitions go here
        pass
```

**Key Points:**
1. Inherit from `DynamoDBModelBase`
2. Call `super().__init__()` first in constructor
3. Define all attributes with type hints
4. Call `_setup_indexes()` at the end of `__init__`

## Defining Primary Keys

Every model must define a primary key. The primary key consists of:
- **Partition Key (pk)**: Determines which partition stores the item
- **Sort Key (sk)**: Orders items within the partition

### Simple Primary Key

For entities that stand alone (not in a one-to-many relationship):

```python
def _setup_indexes(self):
    primary = DynamoDBIndex()
    primary.partition_key.attribute_name = "pk"
    primary.partition_key.value = lambda: DynamoDBKey.build_key(
        ("product", self.id)
    )
    primary.sort_key.attribute_name = "sk"
    primary.sort_key.value = lambda: DynamoDBKey.build_key(
        ("product", self.id)
    )
    self.indexes.add_primary(primary)
```

**Result in DynamoDB:**
```json
{
  "pk": "product#abc-123",
  "sk": "product#abc-123",
  "id": "abc-123",
  "name": "Widget",
  "price": 29.99
}
```

### One-to-Many Primary Keys

For child entities in a one-to-many relationship, the partition key comes from the parent:

```python
class OrderItem(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.order_id = None  # Parent order ID
        self.product_id = None
        self.quantity = 0
        self._setup_indexes()
    
    def _setup_indexes(self):
        primary = DynamoDBIndex()
        # Partition key from PARENT (order)
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("order", self.order_id)
        )
        # Sort key from THIS item
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("item", self.id)
        )
        self.indexes.add_primary(primary)
```

**Result:**
```json
{
  "pk": "order#xyz-789",
  "sk": "item#item-001",
  "id": "item-001",
  "order_id": "xyz-789",
  "product_id": "prod-456",
  "quantity": 2
}
```

This allows querying all items for an order: `pk = "order#xyz-789"`

## Understanding Lambda Functions for Keys

**Critical**: Always use `lambda` functions for key values!

### ❌ Wrong - Value Set at Instantiation

```python
# DON'T DO THIS
primary.partition_key.value = DynamoDBKey.build_key(("product", self.id))
```

If `self.id` is `None` when the object is created, the key will be `"product#None"` forever, even if you change `self.id` later.

### ✅ Correct - Value Evaluated at Runtime

```python
# DO THIS
primary.partition_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
```

The lambda ensures the key is generated using the **current** value of `self.id` when you serialize the model.

### Why This Matters

```python
# Create empty product
product = Product()
print(product.indexes.primary.to_dict())
# Output: {'pk': 'product#None', 'sk': 'product#None'}

# Now set the ID
product.id = "abc-123"
print(product.indexes.primary.to_dict())
# Output: {'pk': 'product#abc-123', 'sk': 'product#abc-123'}
# ✓ Key updated automatically because we used lambda!
```

## Building Composite Keys

Use `DynamoDBKey.build_key()` to create composite keys with multiple parts:

```python
# Single part
DynamoDBKey.build_key(("user", "alice"))
# Result: "user#alice"

# Multiple parts
DynamoDBKey.build_key(("tenant", "acme-corp"), ("user", "alice"))
# Result: "tenant#acme-corp#user#alice"

# With empty values
DynamoDBKey.build_key(("products", ""))
# Result: "products"
```

**Pattern:**
- Each tuple is `(prefix, value)`
- Parts are joined with `#`
- Empty values omit the trailing `#`

## Global Secondary Indexes (GSIs)

GSIs allow you to query data using different keys than your primary key.

### Basic GSI

```python
def _setup_indexes(self):
    # ... primary key setup ...
    
    # GSI to query all products sorted by name
    self.indexes.add_secondary(
        DynamoDBIndex(
            index_name="gsi0",
            partition_key=DynamoDBKey(
                attribute_name="gsi0_pk",
                value=lambda: "products"  # Static partition key
            ),
            sort_key=DynamoDBKey(
                attribute_name="gsi0_sk",
                value=lambda: DynamoDBKey.build_key(("name", self.name))
            )
        )
    )
```

**Use case:** Query all products: `gsi0_pk = "products"` on index `gsi0`

### GSI with Category

```python
# GSI to query products by category
self.indexes.add_secondary(
    DynamoDBIndex(
        index_name="gsi1",
        partition_key=DynamoDBKey(
            attribute_name="gsi1_pk",
            value=lambda: DynamoDBKey.build_key(("category", self.category))
        ),
        sort_key=DynamoDBKey(
            attribute_name="gsi1_sk",
            value=lambda: DynamoDBKey.build_key(("product", self.id))
        )
    )
)
```

**Use case:** Query all products in "electronics" category: `gsi1_pk = "category#electronics"`

### Composite Sort Keys for Multi-Level Sorting

```python
class User(DynamoDBModelBase):
    def _setup_indexes(self):
        # ... primary key ...
        
        # GSI to query all users sorted by last name, then first name
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi1",
                partition_key=DynamoDBKey(
                    attribute_name="gsi1_pk",
                    value=lambda: "users"  # All users
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi1_sk",
                    value=lambda: DynamoDBKey.build_key(
                        ("lastname", self.last_name),
                        ("firstname", self.first_name)
                    )
                )
            )
        )
```

**Result:** Users sorted alphabetically by last name, then first name.

## Advanced: Dynamic Sort Keys

Sometimes you need conditional logic in your keys:

```python
class User(DynamoDBModelBase):
    def _setup_indexes(self):
        # ... primary key ...
        
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi2",
                partition_key=DynamoDBKey(
                    attribute_name="gsi2_pk",
                    value=lambda: "users"
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi2_sk",
                    value=self._get_gsi2_sk  # Method reference
                )
            )
        )
    
    def _get_gsi2_sk(self) -> str:
        """Custom logic for sort key"""
        if self.last_name:
            return f"lastname#{self.last_name}#firstname#{self.first_name or ''}"
        return f"firstname#{self.first_name or ''}"
```

This allows complex conditional key generation.

## Working with Timestamps

For sort keys with timestamps or numeric values, you often want to omit the prefix:

```python
class Order(DynamoDBModelBase):
    def get_completed_utc_ts(self) -> float:
        """Get Unix timestamp of completion"""
        if self.completed_utc is None:
            return 0.0
        return self.completed_utc.timestamp()
    
    def _setup_indexes(self):
        # GSI to query orders by completion date
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value=lambda: "orders"
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    # Use empty string for prefix to get pure numeric sort
                    value=lambda: DynamoDBKey.build_key(
                        ("", self.get_completed_utc_ts())
                    )
                )
            )
        )
```

**Result:** `gsi0_sk = "1678901234.567"` (pure timestamp, no prefix)

## Complete Example: User Model

```python
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey

class User(DynamoDBModelBase):
    def __init__(
        self,
        id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None
    ):
        super().__init__()
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.status = None
        self._setup_indexes()
    
    def _setup_indexes(self):
        # PRIMARY: Get user by ID
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        self.indexes.add_primary(primary)
        
        # GSI0: List all users
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value=lambda: "users"
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: DynamoDBKey.build_key(("user", self.id))
                )
            )
        )
        
        # GSI1: Search users by last name, then first name
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi1",
                partition_key=DynamoDBKey(
                    attribute_name="gsi1_pk",
                    value=lambda: "users"
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi1_sk",
                    value=lambda: DynamoDBKey.build_key(
                        ("lastname", self.last_name or ""),
                        ("firstname", self.first_name or "")
                    )
                )
            )
        )
        
        # GSI2: Find users by status and email
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi2",
                partition_key=DynamoDBKey(
                    attribute_name="gsi2_pk",
                    value=lambda: DynamoDBKey.build_key(("status", self.status))
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi2_sk",
                    value=lambda: DynamoDBKey.build_key(("email", self.email))
                )
            )
        )
```

**Access Patterns Enabled:**
1. Get user by ID → Primary key
2. List all users → GSI0
3. Find users by last name → GSI1
4. Find active users → GSI2 with `gsi2_pk = "status#active"`

## Serialization Methods

Models provide several methods to convert to dictionaries:

### to_dictionary()

Returns a simple dictionary of model attributes (excludes key attributes):

```python
product = Product(id="123", name="Widget", price=29.99)
simple_dict = product.to_dictionary()
# {'id': '123', 'name': 'Widget', 'price': 29.99}
```

### to_resource_dictionary()

Returns a dictionary for the DynamoDB Resource API (includes all keys):

```python
resource_dict = product.to_resource_dictionary()
# {
#   'pk': 'product#123',
#   'sk': 'product#123',
#   'gsi0_pk': 'products',
#   'gsi0_sk': 'name#Widget',
#   'id': '123',
#   'name': 'Widget',
#   'price': 29.99
# }
```

Use this when saving with `db.save()`.

### to_client_dictionary()

Returns a dictionary for the DynamoDB Client API (with type descriptors):

```python
client_dict = product.to_client_dictionary()
# {
#   'pk': {'S': 'product#123'},
#   'sk': {'S': 'product#123'},
#   'id': {'S': '123'},
#   'name': {'S': 'Widget'},
#   'price': {'N': '29.99'}
# }
```

## Deserialization: The map() Method

The `map()` method populates a model from a dictionary:

```python
# From DynamoDB response
dynamodb_item = {
    'id': 'abc-123',
    'name': 'Widget',
    'price': 29.99
}

product = Product().map(dynamodb_item)
print(product.name)  # "Widget"
print(product.price)  # 29.99
```

The `map()` method intelligently handles:
- Full DynamoDB responses: `{'Item': {...}, 'ResponseMetadata': {...}}`
- Item-only responses: `{'Item': {...}}`
- Plain dictionaries
- Automatic decimal conversion

## Debugging Keys

Use `to_dict()` on indexes to see generated keys:

```python
product = Product(id="abc-123", name="Widget")

# Check primary key
print(product.indexes.primary.to_dict())
# {'pk': 'product#abc-123', 'sk': 'product#abc-123'}

# Check GSI key
print(product.indexes.get("gsi0").to_dict())
# {'gsi0_pk': 'products', 'gsi0_sk': 'name#Widget'}

# Partition key only
print(product.indexes.get("gsi0").to_dict(include_sort_key=False))
# {'gsi0_pk': 'products'}
```

See [debug_keys_example.py](../examples/dynamodb/debug_keys_example.py) for comprehensive debugging examples.

## Best Practices

### 1. Models Are DTOs Only

```python
# ❌ DON'T: Add database logic to models
class Product(DynamoDBModelBase):
    def save(self):
        # NO! Models shouldn't know about the database
        db.save(self)

# ✅ DO: Keep models as pure data structures
class Product(DynamoDBModelBase):
    # Just attributes and index definitions
    pass
```

### 2. Always Use Lambda for Keys

```python
# ❌ DON'T
value = DynamoDBKey.build_key(("user", self.id))

# ✅ DO
value = lambda: DynamoDBKey.build_key(("user", self.id))
```

### 3. Consistent Naming

```python
# Primary key attributes: pk, sk
# GSI attributes: gsi0_pk, gsi0_sk, gsi1_pk, gsi1_sk, etc.
```

### 4. Type Hints

```python
# ✅ Use type hints for clarity
self.id: Optional[str] = id
self.price: float = price
self.quantity: int = quantity
```

### 5. Design for Access Patterns

Before creating a model, ask:
- How will I query this data?
- What relationships does it have?
- What sorting do I need?

Then design your primary and GSI keys accordingly.

## Common Patterns

### Standalone Entity

```python
pk = f"{entity_type}#{id}"
sk = f"{entity_type}#{id}"
```

### Child in One-to-Many

```python
pk = f"{parent_type}#{parent_id}"  # From parent
sk = f"{child_type}#{child_id}"     # This entity
```

### List All of Type (GSI)

```python
gsi_pk = f"{entity_type}s"  # Static
gsi_sk = f"{sort_field}#{value}"
```

### Search by Category (GSI)

```python
gsi_pk = f"category#{category_value}"
gsi_sk = f"{entity_type}#{id}"
```

## Next Steps

Now that you understand models, learn how to use them:
- [Creating Service Layers](3-guide-service-layers.md) - Build services to interact with models
- [Testing with Moto](4-guide-testing-with-moto.md) - Test your models locally

## Complete Working Example

See the examples directory for complete implementations:
- [`examples/dynamodb/models/product_model.py`](../examples/dynamodb/models/product_model.py)
- [`examples/dynamodb/models/order_model.py`](../examples/dynamodb/models/order_model.py)
- [`examples/dynamodb/models/user_model.py`](../examples/dynamodb/models/user_model.py)

## Summary

Models in boto3-assist are:
- **Data structures** that represent your business entities
- **Not database-aware** (no direct DB interaction)
- **Responsible for key management** (primary and GSI keys)
- **Serialization/deserialization** to/from DynamoDB format
- **Type-safe** with proper type hints
- **Reusable** across different parts of your application

Remember: Models describe your data structure and how it's keyed. Services use models to interact with DynamoDB.
