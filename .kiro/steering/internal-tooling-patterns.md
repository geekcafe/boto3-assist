# Internal Tooling & Object Patterns

## Priority: HIGH

## Rule

Always use the project's existing internal objects, patterns, and tooling rather than creating custom alternatives. Read existing code before writing new code to understand established conventions.

## DynamoDB Model Patterns

### Use `.map()` for Object Conversion

All DynamoDB models inherit from `DynamoDBModelBase` which provides a `.map(item)` method for populating model instances from dictionaries or other model objects.

```python
# CORRECT — use .map() to create/populate model instances
user = User().map(dynamo_item)
user = User().map(user_dict)
product = Product().map(product_data)
```

```python
# WRONG — don't create custom factory methods like from_*
user = User.from_dict(data)  # Don't do this
user = User.from_response(response)  # Don't do this
```

### Use `.prep_for_save()` Before Saving

Always call `prep_for_save()` before saving a model. This recomputes GSI keys and sets timestamps.

```python
# CORRECT — prepare model before saving
user = User()
user.id = "user-123"
user.name = "John Doe"
user.prep_for_save()
db.save(item=user, table_name="users")
```

### Use `.to_resource_dictionary()` for Serialization

Use the built-in serialization method rather than manually building dicts.

```python
# CORRECT — use built-in serialization
user_dict = user.to_resource_dictionary()
user_dict_no_none = user.to_resource_dictionary(include_none=False)
user_dict_no_indexes = user.to_resource_dictionary(include_indexes=False)
```

```python
# WRONG — don't manually build dicts
user_dict = {
    "id": user.id,
    "name": user.name,
    "email": user.email,
}
```

### Use `.merge()` for Partial Updates

Use the `.merge()` method to populate only specific fields from a dictionary or another model instance.

```python
# CORRECT — use merge() to update specific fields
existing_user = User().map(db_response)
existing_user.merge({"name": "Jane Doe", "status": "active"})
response = db.update_item_partial(item=existing_user, table_name="users")
```

### Use `db.update_item_partial()` for Selective Updates

Use the `DynamoDB.update_item_partial()` method to update only populated fields without replacing the entire item. Models are DTOs only and should not perform database actions directly.

```python
# CORRECT — use db.update_item_partial() for selective updates
db = DynamoDB()
user = User()
user.id = "user-123"
user.name = "Jane Doe"
user.email = "jane@example.com"
# Only name and email are updated (id is primary key)
response = db.update_item_partial(item=user, table_name="users")
```

```python
# WRONG — don't call database methods on models
response = user.save_partial(table_name="users")  # Don't do this
```

## Testing Patterns

### Use Moto for In-Memory DynamoDB Testing

All tests should use `moto` for in-memory DynamoDB simulation. This provides a real DynamoDB-like environment without external dependencies or magic mocks.

```python
# CORRECT — use @mock_aws decorator for in-memory testing
from moto import mock_aws
import boto3
from boto3_assist.dynamodb.dynamodb import DynamoDB

@mock_aws
class TestUserOperations(unittest.TestCase):
    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"

        # Create test table
        self.db.dynamodb_resource.create_table(
            TableName=self.table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

    def test_save_and_retrieve_user(self):
        """Test saving and retrieving a user"""
        user = User()
        user.id = "user-123"
        user.name = "John Doe"
        user.email = "john@example.com"
        user.prep_for_save()

        # Save to mock DynamoDB
        self.db.save(item=user, table_name=self.table_name)

        # Retrieve and verify
        response = self.db.get(
            key={"pk": user.pk, "sk": user.sk},
            table_name=self.table_name
        )
        retrieved_user = User().map(response["Item"])
        self.assertEqual(retrieved_user.name, "John Doe")
```

### NO Magic Mocks

Do NOT use magic mocks (unittest.mock.patch, MagicMock, etc.) for DynamoDB operations. Use moto instead.

```python
# WRONG — don't use magic mocks for DynamoDB
from unittest.mock import patch, MagicMock

@patch("boto3_assist.dynamodb.dynamodb.DynamoDB.save")
def test_user_save(mock_save):
    mock_save.return_value = {"Item": {...}}
    # This doesn't test real DynamoDB behavior!
```

```python
# CORRECT — use moto for real DynamoDB simulation
@mock_aws
def test_user_save():
    db = DynamoDB()
    db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
    # Create table, save, and verify with real DynamoDB-like behavior
```

### Test Organization

Organize tests by functionality:

```
tests/
├── unit/
│   ├── dynamodb_tests/
│   │   ├── test_save_operations.py
│   │   ├── test_query_operations.py
│   │   ├── test_batch_operations.py
│   │   ├── test_partial_updates.py
│   │   └── test_reserved_keywords.py
│   └── utilities/
│       ├── test_decimal_conversion.py
│       └── test_serialization.py
└── integration/
    └── dynamodb_tests/
        ├── test_partial_update_integration.py
        └── test_connection_pool.py
```

### Test Fixtures and Helpers

Create reusable test fixtures and helper functions:

```python
# CORRECT — create helper functions for common test setup
def create_test_table(dynamodb_resource, table_name):
    """Create a test DynamoDB table"""
    return dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

@mock_aws
class TestUserOperations(unittest.TestCase):
    def setUp(self):
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)
```

## Code Organization Patterns

### Single Source of Truth

Keep canonical implementations in one place:

```python
# CORRECT — define once, import everywhere
# src/boto3_assist/dynamodb/reserved_words.py
class DynamoDBReservedWords:
    """Canonical list of DynamoDB reserved keywords"""
    def is_reserved_word(self, word: str) -> bool:
        ...

# src/boto3_assist/dynamodb/partial_update_builder.py
from boto3_assist.dynamodb.reserved_words import DynamoDBReservedWords

class PartialUpdateBuilder:
    def __init__(self):
        self.reserved_words = DynamoDBReservedWords()
```

```python
# WRONG — don't duplicate reserved words list
class PartialUpdateBuilder:
    RESERVED_WORDS = {"status", "type", "name", ...}  # Duplicated!
```

### Reuse Existing Utilities

Always check for existing utility functions before writing new ones:

```python
# CORRECT — use existing decimal conversion utility
from boto3_assist.utilities.decimal_conversion_utility import DecimalConversionUtility

response = db.get(key=key, table_name=table_name)
item = DecimalConversionUtility.convert_decimals_to_native_types(response["Item"])
```

### Consistent Error Handling

Follow the project's error handling patterns:

```python
# CORRECT — use consistent error handling
try:
    response = db.update_item(...)
except ValueError as e:
    logger.warning({"error": str(e), "metric_filter": "update_item"})
    raise
except ClientError as e:
    logger.exception({"error": str(e), "metric_filter": "update_item"})
    raise
```

## Development Workflow

### Read Existing Code First

Before writing new code, read similar existing code to understand patterns:

1. Look for similar functionality in the codebase
2. Study how it's implemented
3. Follow the same patterns and conventions
4. Ask questions if patterns are unclear

### Type Hints

Always include type hints for better IDE support and code clarity:

```python
# CORRECT — include type hints
def update_item_partial(
    self,
    item: Union[Dict[str, Any], DynamoDBModelBase],
    table_name: str,
    fields_to_clear: Optional[Set[str]] = None,
    return_values: str = "NONE",
) -> Dict[str, Any]:
    """Update only populated fields in DynamoDB"""
    ...
```

### Documentation

Include docstrings with examples:

```python
# CORRECT — include comprehensive docstrings
def update_item_partial(
    self,
    item: Union[Dict[str, Any], DynamoDBModelBase],
    table_name: str,
    fields_to_clear: Optional[Set[str]] = None,
    return_values: str = "NONE",
) -> Dict[str, Any]:
    """
    Perform a partial update on an item in DynamoDB using only populated fields.

    Args:
        item: Item to update (dict or DynamoDBModelBase instance)
        table_name: The DynamoDB table name
        fields_to_clear: Optional set of field names to remove
        return_values: What to return ("NONE", "ALL_NEW", "UPDATED_NEW", etc.)

    Returns:
        DynamoDB response dict with optional Attributes

    Examples:
        >>> db = DynamoDB()
        >>> user = User()
        >>> user.id = "user-123"
        >>> user.name = "John Doe"
        >>> response = db.update_item_partial(item=user, table_name="users")
    """
    ...
```
