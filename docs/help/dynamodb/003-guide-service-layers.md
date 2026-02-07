# Creating Service Layers with boto3-assist

## Introduction

The service layer is where your application's business logic lives. It's the bridge between your API handlers (Lambda functions, REST endpoints, etc.) and your DynamoDB database. Services use models to interact with data but keep all database operations isolated and testable.

**Key Principle**: Models are just data structures. Services are where you actually save, retrieve, update, and delete data.

This guide will show you how to create clean, maintainable service layers using boto3-assist.

## Why Service Layers?

### Separation of Concerns

```
API Handler → Service Layer → DynamoDB
     ↓              ↓
  Handles      Handles
  HTTP       Business Logic
              & Database
```

**Benefits:**
- **Testability**: Easy to mock database calls
- **Reusability**: Same service used by multiple handlers
- **Maintainability**: Business logic in one place
- **Type Safety**: Clear interfaces and contracts

### Without Service Layer (❌ Don't Do This)

```python
# Lambda handler with embedded database logic
def lambda_handler(event, context):
    db = DynamoDB()
    product = Product(id="123", name="Widget")
    item = product.to_resource_dictionary()
    db.save(item=item, table_name="products")
    # Business logic mixed with infrastructure
```

### With Service Layer (✅ Do This)

```python
# Lambda handler
def lambda_handler(event, context):
    service = ProductService()
    product = service.create_product({"id": "123", "name": "Widget"})
    # Clean separation!

# Service handles the database
class ProductService:
    def create_product(self, data: dict) -> Product:
        product = Product().map(data)
        # Business logic and database interaction here
        item = product.to_resource_dictionary()
        self.db.save(item=item, table_name=self.table_name)
        return product
```

## Basic Service Structure

```python
import os
from typing import Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.models.product_model import Product

class ProductService:
    def __init__(self, db: Optional[DynamoDB] = None):
        """
        Initialize the service.

        Args:
            db: Optional DynamoDB instance (for dependency injection/testing)
        """
        self.db = db or DynamoDB()
        self.table_name = os.environ.get("APP_TABLE_NAME", "app-table")
```

**Key Elements:**
1. **DynamoDB instance**: Injected or created
2. **Table name**: From environment variable
3. **Dependency injection**: Accepts `db` parameter for testing

## CRUD Operations

### Create (Save)

```python
def create_product(self, product_data: dict) -> Product:
    """
    Create a new product.

    Args:
        product_data: Dictionary with product attributes

    Returns:
        Product: The created product model
    """
    # Map data to model
    product = Product().map(product_data)

    # Convert to DynamoDB format (includes all keys)
    item = product.to_resource_dictionary()

    # Save to database
    self.db.save(item=item, table_name=self.table_name)

    return product
```

**Usage:**
```python
service = ProductService()
product = service.create_product({
    "id": "prod-123",
    "name": "Widget",
    "price": 29.99
})
```

### Read (Get by ID)

```python
def get_product(self, product_id: str) -> Optional[Product]:
    """
    Retrieve a product by ID.

    Args:
        product_id: The product ID

    Returns:
        Product if found, None otherwise
    """
    # Create model with ID to identify the key
    model = Product(id=product_id)

    # Get from database using model's primary key
    response = self.db.get(model=model, table_name=self.table_name)

    # Check if item exists
    item = response.get("Item")
    if not item:
        return None

    # Map response to model and return
    return Product().map(item)
```

**Usage:**
```python
product = service.get_product("prod-123")
if product:
    print(f"Found: {product.name}")
else:
    print("Product not found")
```

### Update

```python
def update_product(self, product_id: str, updates: dict) -> Optional[Product]:
    """
    Update an existing product.

    Args:
        product_id: The product ID
        updates: Dictionary of fields to update

    Returns:
        Updated product if found, None otherwise
    """
    # 1. Get existing product
    existing = self.get_product(product_id)
    if not existing:
        return None

    # 2. Apply updates to the model
    existing.map(updates)

    # 3. Save back to database
    item = existing.to_resource_dictionary()
    self.db.save(item=item, table_name=self.table_name)

    return existing
```

**Usage:**
```python
updated = service.update_product("prod-123", {"price": 34.99})
if updated:
    print(f"Updated price: ${updated.price}")
```

### Delete

```python
def delete_product(self, product_id: str) -> bool:
    """
    Delete a product.

    Args:
        product_id: The product ID

    Returns:
        True if deleted successfully, False otherwise
    """
    model = Product(id=product_id)

    try:
        self.db.delete(model=model, table_name=self.table_name)
        return True
    except Exception as e:
        # Log the error (use proper logging in production)
        print(f"Error deleting product {product_id}: {e}")
        return False
```

**Usage:**
```python
if service.delete_product("prod-123"):
    print("Product deleted")
else:
    print("Delete failed")
```

## List Operations (Queries)

### List All Items (Using GSI)

```python
from boto3.dynamodb.conditions import Key

def list_all_products(self, ascending: bool = True) -> list[Product]:
    """
    List all products, sorted by name.

    Args:
        ascending: Sort order

    Returns:
        List of Product models
    """
    # Create a model to get the GSI key
    model = Product()

    # Get the key condition for GSI0 (all products)
    key_condition = model.indexes.get("gsi0").key()

    # Query the GSI
    response = self.db.query(
        key=key_condition,
        index_name="gsi0",
        table_name=self.table_name,
        ascending=ascending
    )

    # Map all items to models
    items = response.get("Items", [])
    return [Product().map(item) for item in items]
```

**Usage:**
```python
products = service.list_all_products()
for product in products:
    print(f"{product.name}: ${product.price}")
```

### List with Filter

```python
def list_products_by_category(self, category: str) -> list[Product]:
    """
    List products in a specific category.

    Assumes Product has a gsi1 with:
    - gsi1_pk = category#<category>
    - gsi1_sk = product#<id>
    """
    model = Product()
    model.category = category

    # Get key condition for this category
    key_condition = model.indexes.get("gsi1").key()

    response = self.db.query(
        key=key_condition,
        index_name="gsi1",
        table_name=self.table_name
    )

    items = response.get("Items", [])
    return [Product().map(item) for item in items]
```

**Usage:**
```python
electronics = service.list_products_by_category("electronics")
```

## Advanced: One-to-Many Relationships

### Get Parent with Children

```python
def get(
    self,
    order_id: str,
    include_order_items: bool = False,
    do_projections: bool = True
) -> dict:
    """
    Get an order, optionally including all its items.

    Args:
        order_id: The order ID
        include_order_items: If True, returns order + items; if False, just order
        do_projections: If True, uses projection expressions; if False, returns all fields

    Returns:
        DynamoDB response dict with 'Item' or 'Items'
    """
    model = Order(id=order_id)

    # Optionally use projections
    projection = model.projection_expression if do_projections else None
    expr_attrs = model.projection_expression_attribute_names if do_projections else None

    if include_order_items:
        # Query by partition key only (gets order + all items)
        key = model.indexes.primary.key(include_sort_key=False)
        response = self.db.query(
            key=key,
            table_name=self.table_name,
            projection_expression=projection,
            expression_attribute_names=expr_attrs
        )
        # Returns: {"Items": [order, item1, item2, ...]}
    else:
        # Get just the order (pk + sk)
        response = self.db.get(
            model=model,
            table_name=self.table_name,
            projection_expression=projection,
            expression_attribute_names=expr_attrs
        )
        # Returns: {"Item": order}

    return response
```

**Usage - Get Order Only:**
```python
response = service.get(order_id="order-123", include_order_items=False)
order = Order().map(response['Item'])
print(f"Order total: ${order.total}")
```

**Usage - Get Order with Items:**
```python
response = service.get(order_id="order-123", include_order_items=True)
items = response['Items']

# Separate order from order items
order = None
order_items = []

for item in items:
    if item['sk'].startswith('order#'):
        order = Order().map(item)
    elif item['sk'].startswith('item#'):
        order_items.append(OrderItem().map(item))

print(f"Order total: ${order.total}")
print(f"Item count: {len(order_items)}")
```

**Pattern Explanation:**
- Service returns raw DynamoDB response
- Caller separates order from items based on `sk` prefix
- This pattern gives flexibility - caller decides how to process results

### List Children Only

```python
def get_order_items(self, order_id: str) -> list[OrderItem]:
    """
    Get all items for an order.
    """
    # Use begins_with on sort key
    model = Order(id=order_id)

    # Create key condition for partition key + sort key begins_with
    from boto3.dynamodb.conditions import Key
    key_condition = (
        Key("pk").eq(f"order#{order_id}") &
        Key("sk").begins_with("item#")
    )

    response = self.db.query(
        key=key_condition,
        table_name=self.table_name
    )

    items = response.get("Items", [])
    return [OrderItem().map(item) for item in items]
```

## Advanced Query Patterns

### Range Queries (between)

```python
from datetime import datetime

def get_orders_in_date_range(
    self,
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[Order]:
    """
    Get user's orders within a date range.

    Assumes Order has gsi1 with:
    - gsi1_pk = user#<user_id>#orders
    - gsi1_sk = <timestamp>
    """
    model = Order()
    model.user_id = user_id

    # Get key with 'between' condition
    key_condition = model.indexes.get("gsi1").key(
        condition="between",
        low_value=start_date.timestamp(),
        high_value=end_date.timestamp()
    )

    response = self.db.query(
        key=key_condition,
        index_name="gsi1",
        table_name=self.table_name
    )

    items = response.get("Items", [])
    return [Order().map(item) for item in items]
```

### Begins With Queries

```python
def search_users_by_last_name(self, last_name_prefix: str) -> list[User]:
    """
    Find users whose last name starts with a prefix.

    Assumes User has gsi1 with sort key: lastname#<last_name>#firstname#<first_name>
    """
    model = User()
    model.last_name = last_name_prefix

    # Use begins_with condition
    key_condition = model.indexes.get("gsi1").key(condition="begins_with")

    response = self.db.query(
        key=key_condition,
        index_name="gsi1",
        table_name=self.table_name
    )

    items = response.get("Items", [])
    return [User().map(item) for item in items]
```

**Usage:**
```python
# Find all users with last name starting with "Smith"
smiths = service.search_users_by_last_name("Smith")
```

## Using Projection Expressions

Reduce data transfer by requesting only specific attributes:

```python
def get_product_summary(self, product_id: str) -> Optional[dict]:
    """
    Get only name and price of a product.
    """
    model = Product(id=product_id)

    response = self.db.get(
        model=model,
        table_name=self.table_name,
        projection_expression="id,#name,price",
        expression_attribute_names={"#name": "name"}  # 'name' is reserved
    )

    return response.get("Item")
```

**Using model's built-in projections:**

```python
class Product(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        # ... attributes ...
        self._setup_indexes()

        # Define projection expression
        self.projection_expression = "id,#name,price,description"
        self.projection_expression_attribute_names = {"#name": "name"}

# In service
def get_product(self, product_id: str) -> Optional[Product]:
    model = Product(id=product_id)

    response = self.db.get(
        model=model,
        table_name=self.table_name,
        projection_expression=model.projection_expression,
        expression_attribute_names=model.projection_expression_attribute_names
    )

    item = response.get("Item")
    return Product().map(item) if item else None
```

## Business Logic in Services

Services are perfect for business rules:

```python
class OrderService:
    def create_order(self, user_id: str, items: list[dict]) -> Order:
        """
        Create an order with business logic.
        """
        # Create order
        order = Order()
        order.id = self._generate_order_id()
        order.user_id = user_id
        order.created_utc = datetime.utcnow()
        order.status = "pending"

        # Calculate totals
        subtotal = 0.0
        tax_total = 0.0

        for item_data in items:
            # Get product to check price
            product = self._product_service.get_product(item_data["product_id"])

            quantity = item_data["quantity"]
            item_total = product.price * quantity
            subtotal += item_total

            if product.is_taxable:
                tax_total += item_total * 0.08  # 8% tax

        order.total = subtotal + tax_total
        order.tax_total = tax_total

        # Save order
        self.db.save(
            item=order.to_resource_dictionary(),
            table_name=self.table_name
        )

        # Create order items (in production, use transactions)
        for item_data in items:
            self._create_order_item(order.id, item_data)

        return order

    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        import uuid
        return f"ord-{uuid.uuid4().hex[:12]}"

    def _create_order_item(self, order_id: str, item_data: dict):
        """Create an order item"""
        # Implementation here
        pass
```

## Error Handling

```python
from botocore.exceptions import ClientError

def get_product(self, product_id: str) -> Optional[Product]:
    """Get product with error handling."""
    try:
        model = Product(id=product_id)
        response = self.db.get(model=model, table_name=self.table_name)

        item = response.get("Item")
        return Product().map(item) if item else None

    except ClientError as e:
        error_code = e.response['Error']['Code']

        if error_code == 'ResourceNotFoundException':
            print(f"Table {self.table_name} not found")
        elif error_code == 'ProvisionedThroughputExceededException':
            print("Request rate too high")
        else:
            print(f"DynamoDB error: {error_code}")

        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Complete Service Example

```python
import os
from typing import Optional
from datetime import datetime
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3.dynamodb.conditions import Key
from your_app.models.user_model import User

class UserService:
    def __init__(self, db: Optional[DynamoDB] = None):
        self.db = db or DynamoDB()
        self.table_name = os.environ.get("APP_TABLE_NAME", "app-table")

    def create_user(self, user_data: dict) -> User:
        """Create a new user."""
        user = User().map(user_data)

        # Set default values
        if not user.status:
            user.status = "active"

        # Business logic: validate email
        if not self._is_valid_email(user.email):
            raise ValueError("Invalid email address")

        # Check if email already exists
        if self.get_user_by_email(user.email):
            raise ValueError("Email already registered")

        # Save user
        item = user.to_resource_dictionary()
        self.db.save(item=item, table_name=self.table_name)

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        model = User(id=user_id)
        response = self.db.get(model=model, table_name=self.table_name)

        item = response.get("Item")
        return User().map(item) if item else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email.
        Assumes gsi2 with: gsi2_pk = emails, gsi2_sk = email#<email>
        """
        model = User()
        model.email = email

        key_condition = model.indexes.get("gsi2").key()

        response = self.db.query(
            key=key_condition,
            index_name="gsi2",
            table_name=self.table_name
        )

        items = response.get("Items", [])
        return User().map(items[0]) if items else None

    def list_users(self, status: Optional[str] = None) -> list[User]:
        """List all users, optionally filtered by status."""
        model = User()

        if status:
            # Use status-specific GSI
            model.status = status
            key_condition = model.indexes.get("gsi3").key()
            index_name = "gsi3"
        else:
            # Use general "all users" GSI
            key_condition = model.indexes.get("gsi0").key()
            index_name = "gsi0"

        response = self.db.query(
            key=key_condition,
            index_name=index_name,
            table_name=self.table_name
        )

        items = response.get("Items", [])
        return [User().map(item) for item in items]

    def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user."""
        user = self.get_user(user_id)
        if not user:
            return None

        # Don't allow changing email if it would conflict
        if "email" in updates and updates["email"] != user.email:
            if self.get_user_by_email(updates["email"]):
                raise ValueError("Email already in use")

        user.map(updates)

        item = user.to_resource_dictionary()
        self.db.save(item=item, table_name=self.table_name)

        return user

    def deactivate_user(self, user_id: str) -> bool:
        """Soft delete by setting status to inactive."""
        user = self.get_user(user_id)
        if not user:
            return False

        user.status = "inactive"

        item = user.to_resource_dictionary()
        self.db.save(item=item, table_name=self.table_name)

        return True

    def search_by_name(self, last_name: str, first_name: Optional[str] = None) -> list[User]:
        """Search users by name."""
        model = User()
        model.last_name = last_name
        if first_name:
            model.first_name = first_name

        key_condition = model.indexes.get("gsi1").key(
            condition="begins_with"
        )

        response = self.db.query(
            key=key_condition,
            index_name="gsi1",
            table_name=self.table_name
        )

        items = response.get("Items", [])
        return [User().map(item) for item in items]

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
```

## Best Practices

### 1. Dependency Injection

```python
# ✅ Allow DynamoDB to be injected
def __init__(self, db: Optional[DynamoDB] = None):
    self.db = db or DynamoDB()

# This enables testing:
mock_db = MockDynamoDB()
service = UserService(db=mock_db)
```

### 2. Environment Variables for Configuration

```python
# ✅ Use environment variables
self.table_name = os.environ.get("APP_TABLE_NAME", "default-table")

# ❌ Don't hardcode
self.table_name = "production-users-table"
```

### 3. Return Models, Not Dictionaries

```python
# ✅ Return typed models
def get_user(self, user_id: str) -> Optional[User]:
    # ...
    return User().map(item) if item else None

# ❌ Less type-safe
def get_user(self, user_id: str) -> Optional[dict]:
    return item
```

### 4. Keep Business Logic in Services

```python
# ✅ Business logic in service
def create_order(self, items):
    # Validate, calculate totals, check inventory, etc.
    pass

# ❌ Business logic in handler
# Lambda handlers should only parse input and format output
```

### 5. Single Responsibility

```python
# ✅ One service per entity/aggregate
class UserService:
    # User operations only
    pass

class OrderService:
    # Order operations only
    pass

# ❌ God object
class ApplicationService:
    # Everything
    pass
```

## Testing Services

See [Testing with Moto](4-guide-testing-with-moto.md) for comprehensive testing patterns.

Quick example:
```python
import unittest
from moto import mock_aws
from your_app.services.user_service import UserService

@mock_aws
class TestUserService(unittest.TestCase):
    def setUp(self):
        # Moto will mock DynamoDB
        self.service = UserService()
        # Create mock table
        # ... setup code ...

    def test_create_user(self):
        user = self.service.create_user({
            "id": "test-1",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })

        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.status, "active")
```

## Summary

Service layers in boto3-assist:
- **Encapsulate** all database operations
- **Use models** for type safety and structure
- **Handle business logic** and validation
- **Support dependency injection** for testing
- **Provide clean APIs** to handlers/controllers

The pattern is simple:
1. Create models to define data structure
2. Create services to handle CRUD + business logic
3. Handlers call services (never database directly)

## Next Steps

- [Testing with Moto](4-guide-testing-with-moto.md) - Learn how to test your services locally
- [Understanding Single Table Design](1-guide-single-table-design.md) - Review the foundations
- See [`examples/dynamodb/services/`](../examples/dynamodb/services/) for complete examples

## Example Code

Complete working examples:
- [`examples/dynamodb/services/user_service.py`](../examples/dynamodb/services/user_service.py)
- [`examples/dynamodb/services/order_service.py`](../examples/dynamodb/services/order_service.py)
- [`examples/dynamodb/services/product_service.py`](../examples/dynamodb/services/product_service.py)
