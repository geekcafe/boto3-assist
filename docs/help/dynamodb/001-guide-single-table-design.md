# Understanding Single Table Design with boto3-assist

## Introduction

Single Table Design is a DynamoDB best practice where you store all your application's data in a single table rather than creating separate tables for each entity type. While this may seem counterintuitive to those familiar with relational databases, it's the recommended approach for DynamoDB and offers significant benefits in terms of performance, cost, and scalability.

This guide will help you understand the fundamentals of single table design and how boto3-assist makes it easy to implement this pattern in your applications.

## Why Single Table Design?

### Benefits

- **Performance**: All related data can be retrieved in a single query, reducing the number of round trips to the database
- **Cost**: Fewer tables mean fewer provisioned resources and lower costs
- **Simplicity**: One table to manage instead of many
- **Atomic Transactions**: You can perform transactions across multiple entity types within the same table
- **Better Data Modeling**: Forces you to think about access patterns upfront

### Traditional vs. Single Table

**Traditional Multi-Table Approach:**
```
Users Table:     user_id, name, email
Orders Table:    order_id, user_id, total
Products Table:  product_id, name, price
```

**Single Table Design:**
```
AppTable:  pk, sk, ... (all entity attributes)
```

All your users, orders, and products live in one table, differentiated by their partition and sort keys.

## The Foundation: Partition Keys (pk) and Sort Keys (sk)

In single table design, the `pk` (partition key) and `sk` (sort key) are the secret sauce. They determine:
- **Where** your data is stored (partition key)
- **How** your data is organized within that partition (sort key)
- **What** query patterns you can support

### Anatomy of a Key

Keys in boto3-assist follow a structured pattern:

```
entityType#entityId
```

For example:
- `user#123` - Represents user with ID 123
- `product#abc-456` - Represents product with ID abc-456
- `order#xyz-789` - Represents order with ID xyz-789

The `#` delimiter separates the entity type from the identifier, making keys readable and queryable.

## Simple Entity Storage

Let's start with the simplest case: storing a single entity type.

### Example: Product Entity

```python
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey

class Product(DynamoDBModelBase):
    def __init__(self, id=None, name=None, price=0.0):
        super().__init__()
        self.id = id
        self.name = name
        self.price = price
        self._setup_indexes()
    
    def _setup_indexes(self):
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        self.indexes.add_primary(primary)
```

**What gets stored:**
```json
{
  "pk": "product#abc-123",
  "sk": "product#abc-123",
  "id": "abc-123",
  "name": "Widget",
  "price": 29.99
}
```

**Access pattern:** Get product by ID
- Query: `pk = "product#abc-123" AND sk = "product#abc-123"`
- Returns: The specific product

## One-to-Many Relationships: The Power of pk/sk

This is where single table design really shines. By cleverly using partition and sort keys, you can model one-to-many relationships without joins.

### The Pattern

**For a one-to-many relationship:**
- **Parent entity**: `pk = parent_type#parent_id`, `sk = parent_type#parent_id`
- **Child entities**: `pk = parent_type#parent_id`, `sk = child_type#child_id`

Notice that child items share the **same partition key** as their parent but have **different sort keys**.

### Example: Order → Order Items (1:Many)

An order can have many order items. Let's see how this works:

```python
class Order(DynamoDBModelBase):
    def __init__(self, id=None):
        super().__init__()
        self.id = id
        self.user_id = None
        self.total = 0.0
        self._setup_indexes()
    
    def _setup_indexes(self):
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("order", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("order", self.id))
        self.indexes.add_primary(primary)

class OrderItem(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.order_id = None  # Parent order's ID
        self.product_id = None
        self.quantity = 0
        self._setup_indexes()
    
    def _setup_indexes(self):
        primary = DynamoDBIndex()
        # Same partition key as the parent order
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("order", self.order_id))
        # Different sort key for this item
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("item", self.id))
        self.indexes.add_primary(primary)
```

**What gets stored:**

```json
// Order (parent)
{
  "pk": "order#xyz-789",
  "sk": "order#xyz-789",
  "id": "xyz-789",
  "user_id": "user-123",
  "total": 99.99
}

// Order Item 1 (child)
{
  "pk": "order#xyz-789",
  "sk": "item#item-001",
  "id": "item-001",
  "order_id": "xyz-789",
  "product_id": "prod-456",
  "quantity": 2
}

// Order Item 2 (child)
{
  "pk": "order#xyz-789",
  "sk": "item#item-002",
  "id": "item-002",
  "order_id": "xyz-789",
  "product_id": "prod-789",
  "quantity": 1
}
```

**Access patterns enabled:**

1. **Get order only:**
   - Query: `pk = "order#xyz-789" AND sk = "order#xyz-789"`
   - Returns: Just the order

2. **Get order with all items:**
   - Query: `pk = "order#xyz-789"` (partition key only, no sort key filter)
   - Returns: Order + all order items in a single query!

3. **Get items only:**
   - Query: `pk = "order#xyz-789" AND sk begins_with "item#"`
   - Returns: Only the order items (no order)

This is the magic of single table design. Because all related items share the same partition key, DynamoDB returns them together efficiently.

### Why This Works

1. **Same Partition**: The order and its items are stored in the same partition (`pk = "order#xyz-789"`)
2. **Sort Key Differentiation**: Each item type has a unique sort key pattern
   - Order: `sk = "order#xyz-789"`
   - Items: `sk = "item#item-001"`, `sk = "item#item-002"`, etc.
3. **Flexible Querying**: The sort key is **optional** in queries
   - Omit it → get everything with that partition key
   - Specify it exactly → get one specific item
   - Use `begins_with` → get items matching a pattern

### Important: Sort Key is Optional in Queries

**This is a critical concept many developers miss:**

In DynamoDB:
- The **partition key is REQUIRED** for all queries
- The **sort key is OPTIONAL** for queries (but required when defining the table)

```python
# Pattern 1: Get with both pk and sk (using db.get())
model = Order(id="xyz-789")
response = db.get(model=model, table_name=table_name)
# Uses: pk="order#xyz-789" AND sk="order#xyz-789"
# Returns: Just the order

# Pattern 2: Query with pk only (using db.query())
model = Order(id="xyz-789")
key = model.indexes.primary.key(include_sort_key=False)
response = db.query(key=key, table_name=table_name)
# Uses: pk="order#xyz-789" (no sk filter)
# Returns: Order + all items (everything with that pk)

# Pattern 3: Query with pk + sk condition (using db.query())
from boto3.dynamodb.conditions import Key
key = Key("pk").eq("order#xyz-789") & Key("sk").begins_with("item#")
response = db.query(key=key, table_name=table_name)
# Uses: pk="order#xyz-789" AND sk starts with "item#"
# Returns: Only the items
```

**Real-World Service Code:**

```python
class OrderService:
    def get_order(self, order_id: str, include_items: bool = False):
        model = Order(id=order_id)
        
        if include_items:
            # Query with pk only - gets order + items
            key = model.indexes.primary.key(include_sort_key=False)
            response = self.db.query(key=key, table_name=self.table_name)
            # Returns: {'Items': [order, item1, item2, ...]}
        else:
            # Get with pk + sk - gets just the order
            response = self.db.get(model=model, table_name=self.table_name)
            # Returns: {'Item': order}
        
        return response
```

See the complete working example in [tests/unit/examples_test/order_service_test.py](../tests/unit/examples_test/order_service_test.py) which demonstrates all three patterns.

## Another Example: User → Posts (1:Many)

Let's look at another common pattern:

```python
class User(DynamoDBModelBase):
    def __init__(self, id=None):
        super().__init__()
        self.id = id
        self.name = None
        self._setup_indexes()
    
    def _setup_indexes(self):
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        self.indexes.add_primary(primary)

class Post(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id = None
        self.user_id = None  # Parent user's ID
        self.title = None
        self.content = None
        self.created_at = None
        self._setup_indexes()
    
    def _setup_indexes(self):
        primary = DynamoDBIndex()
        # Share partition key with user
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.user_id))
        # Unique sort key for posts
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("post", self.id))
        self.indexes.add_primary(primary)
```

**Storage:**

```json
// User
{
  "pk": "user#alice",
  "sk": "user#alice",
  "id": "alice",
  "name": "Alice Johnson"
}

// Post 1
{
  "pk": "user#alice",
  "sk": "post#post-001",
  "id": "post-001",
  "user_id": "alice",
  "title": "My First Post"
}

// Post 2
{
  "pk": "user#alice",
  "sk": "post#post-002",
  "id": "post-002",
  "user_id": "alice",
  "title": "Another Great Post"
}
```

**Query all of Alice's posts:**
```python
# Query with partition key only
key = Key('pk').eq('user#alice')
# Returns: User record + all posts
```

## Advanced: Hierarchical Relationships

You can even model deeper hierarchies using sort key patterns.

### Example: Category → Product → Reviews

```python
# Category
pk = "category#electronics"
sk = "category#electronics"

# Product in category
pk = "category#electronics"
sk = "product#laptop-001"

# Review for product
pk = "category#electronics"
sk = "product#laptop-001#review#review-001"
```

This allows queries like:
- All items in a category: `pk = "category#electronics"`
- All products: `pk = "category#electronics" AND sk begins_with "product#"`
- All reviews for a product: `pk = "category#electronics" AND sk begins_with "product#laptop-001#review#"`

## Global Secondary Indexes (GSIs): Alternative Access Patterns

While pk/sk handle one-to-many relationships, GSIs let you query data in different ways.

### Example: Query All Products by Name

```python
class Product(DynamoDBModelBase):
    def _setup_indexes(self):
        # Primary index (same as before)
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        self.indexes.add_primary(primary)
        
        # GSI to query all products
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value=lambda: "products"  # Static value
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: DynamoDBKey.build_key(("name", self.name))
                )
            )
        )
```

**Access pattern:**
- Query all products sorted by name: `gsi0_pk = "products"` on GSI0

## Key Principles of Single Table Design

1. **Know Your Access Patterns First**: Design your keys based on how you'll query the data
2. **Partition Key for Item Collection**: Items you want to retrieve together share a partition key
3. **Sort Key for Differentiation**: Sort key differentiates items within a partition
4. **One-to-Many via pk/sk**: Parent and children share `pk`, differ in `sk`
5. **GSIs for Alternative Queries**: Add GSIs for query patterns that don't fit your primary key structure

## Common Patterns Summary

| Pattern | Partition Key | Sort Key | Use Case |
|---------|--------------|----------|----------|
| **Single Item** | `entity#id` | `entity#id` | Get specific entity |
| **One-to-Many** | `parent#id` | `child#id` | Get parent with children |
| **Hierarchical** | `root#id` | `level1#id#level2#id` | Multi-level relationships |
| **All Items** | Static value (via GSI) | `entity#attribute` | List all of entity type |

## Best Practices

1. **Use Lambda Functions**: Always use `lambda` for key values so they're evaluated at runtime
2. **Consistent Delimiters**: Stick with `#` as your delimiter
3. **Descriptive Prefixes**: Use entity type names (`user#`, `order#`) for clarity
4. **GSIs for Flexibility**: Add GSIs for access patterns that don't fit your primary keys
5. **Think in Collections**: Design partition keys around how you want to group and retrieve data

## Next Steps

Now that you understand single table design, you're ready to:
- [Define Models](2-guide-defining-models.md) - Learn how to create model classes
- [Create Service Layers](3-guide-service-layers.md) - Build services to interact with your models
- [Test with Moto](4-guide-testing-with-moto.md) - Set up local testing

## Real-World Example

Let's put it all together with an e-commerce system:

```
Primary Table Access Patterns:
1. pk="product#123", sk="product#123"          → Get product
2. pk="order#456", sk="order#456"               → Get order header
3. pk="order#456", sk begins_with "item#"       → Get all order items
4. pk="order#456"                               → Get order + items (single query!)
5. pk="user#alice", sk="user#alice"             → Get user
6. pk="user#alice", sk begins_with "order#"     → Get user's orders

GSI Access Patterns:
1. gsi0: All products sorted by name
2. gsi1: All orders for a user sorted by date
3. gsi2: All orders on a specific date
```

All of this in **one table**!

## Conclusion

Single table design is a paradigm shift from relational databases, but it's optimized for DynamoDB's strengths. By cleverly using partition and sort keys, especially for one-to-many relationships, you can build highly performant applications that retrieve all related data in a single query.

The key insight: **Items that are queried together should be stored together**, and boto3-assist makes implementing this pattern straightforward and maintainable.
