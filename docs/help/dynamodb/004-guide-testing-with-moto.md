# Testing DynamoDB Locally with Moto

## Introduction

One of the biggest challenges in developing DynamoDB applications is testing. You don't want to test against a live DynamoDB table for several reasons:
- **Cost**: Every operation costs money
- **Speed**: Network latency slows down tests
- **Safety**: Risk of corrupting production data
- **Isolation**: Tests should be independent and repeatable

Enter **Moto** - a library that mocks AWS services, including DynamoDB, allowing you to test your code locally without touching AWS at all.

This guide shows you how to use Moto with boto3-assist to create fast, reliable, offline tests.

## What is Moto?

Moto is a Python library that creates mock implementations of AWS services. When you use the `@mock_aws` decorator, all boto3 calls are intercepted and handled by Moto's in-memory mock instead of hitting real AWS.

**Key Benefits:**
- ✅ **No AWS Account Needed**: Tests run completely offline
- ✅ **Fast**: No network calls, instant responses
- ✅ **Free**: No AWS costs
- ✅ **Isolated**: Each test gets a fresh mock environment
- ✅ **Repeatable**: Same test always produces same results
- ✅ **CI/CD Friendly**: Works in any environment

## Installation

Add Moto to your development dependencies:

```bash
pip install moto[dynamodb]
```

Or in your `requirements-dev.txt`:
```
moto[dynamodb]==5.0.0
boto3-assist
pytest  # or unittest
```

## Basic Test Structure

Here's the fundamental pattern for testing with Moto:

```python
import unittest
from moto import mock_aws
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.services.product_service import ProductService
from your_app.models.product_model import Product

@mock_aws  # This decorator mocks all AWS services
class TestProductService(unittest.TestCase):

    def setUp(self):
        """Run before each test"""
        # DynamoDB is now mocked - no real AWS connection
        self.db = DynamoDB()
        self.table_name = "test-products"

        # Create a mock table
        self._create_test_table()

        # Create service
        self.service = ProductService(db=self.db, table_name=self.table_name)

    def _create_test_table(self):
        """Create a mock DynamoDB table"""
        self.db.client.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},
                {'AttributeName': 'sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi0_pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi0_sk', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'gsi0',
                    'KeySchema': [
                        {'AttributeName': 'gsi0_pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi0_sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

    def test_create_product(self):
        """Test creating a product"""
        product = self.service.create_product({
            "id": "prod-123",
            "name": "Widget",
            "price": 29.99
        })

        self.assertEqual(product.id, "prod-123")
        self.assertEqual(product.name, "Widget")
        self.assertEqual(product.price, 29.99)

    def test_get_product(self):
        """Test retrieving a product"""
        # Create a product
        self.service.create_product({
            "id": "prod-456",
            "name": "Gadget",
            "price": 19.99
        })

        # Retrieve it
        product = self.service.get_product("prod-456")

        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Gadget")

    def test_get_nonexistent_product(self):
        """Test getting a product that doesn't exist"""
        product = self.service.get_product("does-not-exist")
        self.assertIsNone(product)
```

**Key Points:**
1. **`@mock_aws` decorator**: Applied to the test class
2. **`setUp()` method**: Creates fresh mock resources before each test
3. **Table creation**: Must create mock tables manually
4. **Dependency injection**: Pass mocked `db` to services

## Understanding the @mock_aws Decorator

The `@mock_aws` decorator can be used at class or method level:

### Class-Level (Recommended)

```python
@mock_aws
class TestProductService(unittest.TestCase):
    # All test methods automatically use mock

    def test_one(self):
        # AWS is mocked
        pass

    def test_two(self):
        # AWS is mocked
        pass
```

### Method-Level

```python
class TestProductService(unittest.TestCase):

    @mock_aws
    def test_with_mock(self):
        # AWS is mocked only in this test
        pass

    def test_without_mock(self):
        # AWS is NOT mocked (would hit real AWS)
        pass
```

**Recommendation**: Use class-level for consistency and convenience.

## Creating Mock Tables

You need to create tables in your mock environment. Here's a reusable helper:

### Simple Table Helper

```python
def create_simple_table(client, table_name: str):
    """Create a basic table with pk/sk and one GSI"""
    client.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi0_pk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi0_sk', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'gsi0',
                'KeySchema': [
                    {'AttributeName': 'gsi0_pk', 'KeyType': 'HASH'},
                    {'AttributeName': 'gsi0_sk', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
```

### Comprehensive Table Helper

```python
class TableHelper:
    @staticmethod
    def create_table_with_gsis(client, table_name: str, gsi_count: int = 4):
        """Create table with multiple GSIs"""

        # Build attribute definitions
        attributes = [
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'}
        ]

        # Add GSI attributes
        for i in range(gsi_count):
            attributes.append({'AttributeName': f'gsi{i}_pk', 'AttributeType': 'S'})
            attributes.append({'AttributeName': f'gsi{i}_sk', 'AttributeType': 'S'})

        # Build GSIs
        gsis = []
        for i in range(gsi_count):
            gsis.append({
                'IndexName': f'gsi{i}',
                'KeySchema': [
                    {'AttributeName': f'gsi{i}_pk', 'KeyType': 'HASH'},
                    {'AttributeName': f'gsi{i}_sk', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            })

        # Create table
        client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=attributes,
            GlobalSecondaryIndexes=gsis,
            BillingMode='PAY_PER_REQUEST'
        )
```

### Using the Table Service

boto3-assist includes a `DynamoDBTableService` example:

```python
from examples.dynamodb.services.table_service import DynamoDBTableService

@mock_aws
class TestUserService(unittest.TestCase):
    def setUp(self):
        self.db = DynamoDB()
        self.table_name = "test-users"

        # Use the table service
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)

        self.service = UserService(db=self.db, table_name=self.table_name)
```

## Complete Test Example

```python
import unittest
from moto import mock_aws
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.services.user_service import UserService
from your_app.models.user_model import User

@mock_aws
class TestUserService(unittest.TestCase):
    """Comprehensive user service tests"""

    def setUp(self):
        """Initialize test environment"""
        self.db = DynamoDB()
        self.table_name = "test-users"
        self._create_table()
        self.service = UserService(db=self.db, table_name=self.table_name)

    def _create_table(self):
        """Create mock table"""
        self.db.client.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},
                {'AttributeName': 'sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi0_pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi0_sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1_pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1_sk', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'gsi0',
                    'KeySchema': [
                        {'AttributeName': 'gsi0_pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi0_sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'gsi1',
                    'KeySchema': [
                        {'AttributeName': 'gsi1_pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi1_sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

    def test_create_user(self):
        """Test user creation"""
        user = self.service.create_user({
            "id": "user-001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })

        # Verify user was created correctly
        self.assertEqual(user.id, "user-001")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.status, "active")  # Default value

    def test_get_user_by_id(self):
        """Test retrieving user by ID"""
        # Create user
        self.service.create_user({
            "id": "user-002",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com"
        })

        # Retrieve user
        user = self.service.get_user("user-002")

        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")

    def test_get_nonexistent_user(self):
        """Test getting user that doesn't exist"""
        user = self.service.get_user("does-not-exist")
        self.assertIsNone(user)

    def test_update_user(self):
        """Test updating a user"""
        # Create user
        self.service.create_user({
            "id": "user-003",
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com"
        })

        # Update user
        updated = self.service.update_user("user-003", {
            "first_name": "Robert"
        })

        self.assertIsNotNone(updated)
        self.assertEqual(updated.first_name, "Robert")
        self.assertEqual(updated.last_name, "Jones")  # Unchanged

    def test_list_users(self):
        """Test listing all users"""
        # Create multiple users
        for i in range(5):
            self.service.create_user({
                "id": f"user-{i}",
                "first_name": f"User{i}",
                "last_name": "Test",
                "email": f"user{i}@example.com"
            })

        # List all users
        users = self.service.list_users()

        self.assertEqual(len(users), 5)

    def test_search_by_name(self):
        """Test searching users by name"""
        # Create users with different names
        self.service.create_user({
            "id": "user-smith-1",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com"
        })
        self.service.create_user({
            "id": "user-smith-2",
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com"
        })
        self.service.create_user({
            "id": "user-jones",
            "first_name": "Charlie",
            "last_name": "Jones",
            "email": "charlie@example.com"
        })

        # Search for Smiths
        smiths = self.service.search_by_name("Smith")

        self.assertEqual(len(smiths), 2)
        for user in smiths:
            self.assertEqual(user.last_name, "Smith")

    def test_delete_user(self):
        """Test deleting a user"""
        # Create user
        self.service.create_user({
            "id": "user-delete",
            "first_name": "Delete",
            "last_name": "Me",
            "email": "delete@example.com"
        })

        # Verify it exists
        user = self.service.get_user("user-delete")
        self.assertIsNotNone(user)

        # Delete it
        result = self.service.delete_user("user-delete")
        self.assertTrue(result)

        # Verify it's gone
        user = self.service.get_user("user-delete")
        self.assertIsNone(user)


if __name__ == '__main__':
    unittest.main()
```

## Testing One-to-Many Relationships

```python
@mock_aws
class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.db = DynamoDB()
        self.table_name = "test-orders"
        self._create_table()
        self.service = OrderService(db=self.db, table_name=self.table_name)

    def test_get_order_with_items(self):
        """Test retrieving order with all its items"""
        # Create order
        order = Order(id="order-001")
        order.user_id = "user-123"
        order.total = 100.00
        self.db.save(
            item=order.to_resource_dictionary(),
            table_name=self.table_name
        )

        # Create order items
        for i in range(3):
            item = OrderItem()
            item.id = f"item-{i}"
            item.order_id = "order-001"
            item.quantity = i + 1
            self.db.save(
                item=item.to_resource_dictionary(),
                table_name=self.table_name
            )

        # Get order with items
        response = self.service.get(
            order_id="order-001",
            include_order_items=True
        )

        # Separate order from items
        order = None
        order_items = []
        for item in response['Items']:
            if item['sk'].startswith('order#'):
                order = Order().map(item)
            elif item['sk'].startswith('item#'):
                order_items.append(OrderItem().map(item))

        self.assertIsNotNone(order)
        self.assertEqual(len(order_items), 3)
        self.assertEqual(order.id, "order-001")
```

## Testing with Pytest

If you prefer pytest over unittest:

```python
import pytest
from moto import mock_aws
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.services.product_service import ProductService

@pytest.fixture
@mock_aws
def mock_dynamodb():
    """Fixture to create mock DynamoDB"""
    db = DynamoDB()
    table_name = "test-products"

    # Create table
    db.client.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    return db, table_name

def test_create_product(mock_dynamodb):
    """Test creating a product"""
    db, table_name = mock_dynamodb
    service = ProductService(db=db, table_name=table_name)

    product = service.create_product({
        "id": "prod-123",
        "name": "Widget",
        "price": 29.99
    })

    assert product.id == "prod-123"
    assert product.name == "Widget"
    assert product.price == 29.99
```

## Best Practices

### 1. Always Use Dependency Injection

```python
# ✅ Service accepts DynamoDB instance
class ProductService:
    def __init__(self, db: Optional[DynamoDB] = None):
        self.db = db or DynamoDB()

# This allows testing:
mock_db = DynamoDB()  # Will be mocked by @mock_aws
service = ProductService(db=mock_db)
```

### 2. Use setUp for Common Setup

```python
@mock_aws
class TestService(unittest.TestCase):
    def setUp(self):
        """Run before EACH test"""
        # Create fresh environment
        self.db = DynamoDB()
        self._create_table()
        self.service = MyService(db=self.db)

    def test_one(self):
        # Fresh environment
        pass

    def test_two(self):
        # Fresh environment (setUp ran again)
        pass
```

### 3. Create Helper Methods

```python
class TestUserService(unittest.TestCase):
    def _create_test_user(self, user_id: str) -> User:
        """Helper to create a test user"""
        return self.service.create_user({
            "id": user_id,
            "first_name": "Test",
            "last_name": "User",
            "email": f"{user_id}@example.com"
        })

    def test_something(self):
        user = self._create_test_user("user-001")
        # Now test something with this user
```

### 4. Test Edge Cases

```python
def test_get_with_empty_id(self):
    """Test behavior with empty ID"""
    product = self.service.get_product("")
    self.assertIsNone(product)

def test_update_nonexistent_item(self):
    """Test updating item that doesn't exist"""
    result = self.service.update_product("fake-id", {"name": "New"})
    self.assertIsNone(result)

def test_create_with_missing_required_fields(self):
    """Test creating with missing fields"""
    with self.assertRaises(ValueError):
        self.service.create_product({})
```

### 5. Test Query Results

```python
def test_list_returns_correct_count(self):
    """Verify list returns expected number of items"""
    # Create 10 products
    for i in range(10):
        self._create_test_product(f"prod-{i}")

    # List all
    products = self.service.list_all_products()

    self.assertEqual(len(products), 10)

def test_list_returns_sorted_results(self):
    """Verify list returns items in correct order"""
    # Create products with specific names
    self._create_test_product("prod-1", name="Zebra")
    self._create_test_product("prod-2", name="Apple")
    self._create_test_product("prod-3", name="Mango")

    # List ascending
    products = self.service.list_all_products(ascending=True)

    self.assertEqual(products[0].name, "Apple")
    self.assertEqual(products[1].name, "Mango")
    self.assertEqual(products[2].name, "Zebra")
```

## Common Pitfalls

### ❌ Forgetting @mock_aws

```python
# This will try to connect to real AWS!
class TestService(unittest.TestCase):
    def test_something(self):
        service = MyService()  # ERROR: No AWS credentials
```

### ❌ Not Creating Tables

```python
@mock_aws
class TestService(unittest.TestCase):
    def test_something(self):
        db = DynamoDB()
        # ERROR: Table doesn't exist
        db.save(item={}, table_name="my-table")
```

### ❌ Hardcoding Table Names in Services

```python
# Service
class MyService:
    def __init__(self):
        self.table_name = "production-table"  # ❌ Can't change for tests

# ✅ Better:
class MyService:
    def __init__(self, table_name: str):
        self.table_name = table_name  # ✅ Can inject test table name
```

## Running Tests

### Using unittest

```bash
# Run all tests
python -m unittest discover -s tests

# Run specific test file
python -m unittest tests.test_user_service

# Run specific test
python -m unittest tests.test_user_service.TestUserService.test_create_user
```

### Using pytest

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_user_service.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_user_service.py::test_create_product
```

## Integration with CI/CD

Moto works perfectly in CI/CD pipelines:

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ -v
```

No AWS credentials needed!

## Advanced: Testing Error Conditions

```python
from botocore.exceptions import ClientError

@mock_aws
class TestErrorHandling(unittest.TestCase):
    def test_handles_missing_table(self):
        """Test handling of missing table"""
        db = DynamoDB()
        # Don't create table

        with self.assertRaises(ClientError) as context:
            db.save(item={}, table_name="nonexistent-table")

        self.assertEqual(
            context.exception.response['Error']['Code'],
            'ResourceNotFoundException'
        )
```

## Testing with Projections

### Quick Note on Projections

When testing DynamoDB operations, you'll often want to verify **key structure** (pk, sk, GSI keys). However, if your services use projection expressions to filter returned attributes, these keys won't be in the response!

**The solution**: Design your services to optionally disable projections for testing.

```python
class OrderService:
    def get(self, order_id: str, include_order_items: bool = False,
            do_projections: bool = True):
        """
        Args:
            do_projections: If False, returns ALL fields (useful for testing keys)
        """
        # Only apply projection if do_projections=True
        projection = model.projection_expression if do_projections else None
        # ... rest of implementation
```

**In tests:**

```python
def test_verify_key_structure(self):
    # Turn OFF projections to see pk/sk keys
    result = self.service.get(
        order_id="order-001",
        do_projections=False  # ← Get ALL fields including keys
    )

    # Now we can verify key structure
    self.assertEqual(result["Item"]["pk"], "order#order-001")
    self.assertEqual(result["Item"]["sk"], "order#order-001")
```

**See the complete example** in [`tests/unit/examples_test/order_service_test.py`](../../../tests/unit/examples_test/order_service_test.py).

**For a comprehensive guide** on projection expressions and DynamoDB reserved keywords, see [Projection Expressions Guide](5-guide-projections-and-reserved-keywords.md).

## Summary

Testing with Moto gives you:
- ✅ **Fast tests** (no network calls)
- ✅ **Free tests** (no AWS costs)
- ✅ **Reliable tests** (consistent, repeatable)
- ✅ **Isolated tests** (no shared state)
- ✅ **Offline tests** (work anywhere)

**The pattern is simple:**
1. Add `@mock_aws` decorator
2. Create mock tables in `setUp()`
3. Inject mocked `DynamoDB` into services
4. Write tests as normal

## Example Test Files

See complete examples in the repository:
- [`tests/unit/examples_test/user_service_test.py`](../tests/unit/examples_test/user_service_test.py)
- [`tests/unit/dynamodb_tests/dynamodb_primary_key_get_test.py`](../tests/unit/dynamodb_tests/dynamodb_primary_key_get_test.py)
- [`tests/unit/common/db_test_helpers.py`](../tests/unit/common/db_test_helpers.py)

## Next Steps

Now you have everything you need to build and test DynamoDB applications with boto3-assist:
1. [Understanding Single Table Design](1-guide-single-table-design.md)
2. [Defining Models](2-guide-defining-models.md)
3. [Creating Service Layers](3-guide-service-layers.md)
4. Testing with Moto (this guide)

Start building with confidence knowing you can test everything locally!
