# Unit Test Patterns for boto3-assist

## Overview

This document outlines testing patterns and best practices for the boto3-assist library. Following these patterns ensures consistent, maintainable, and reliable test coverage.

## Test Structure

### Test Organization

```
tests/
├── unit/
│   ├── dynamodb_tests/          # DynamoDB functionality tests
│   │   ├── db_models/           # Test models
│   │   └── *.py                 # Test files
│   ├── models_tests/            # Model serialization tests
│   ├── utilities/               # Utility function tests
│   ├── lambda_tests/            # Lambda handler tests
│   ├── s3/                      # S3 functionality tests
│   └── session_tests/           # Session management tests
└── integration/                 # Integration tests (if needed)
```

### Test File Naming

- **Pattern**: `test_<feature_name>.py` or `<feature_name>_test.py`
- **Examples**: 
  - `test_decimal_conversion.py`
  - `dynamodb_model_base_test.py`
  - `decimal_backward_compatibility_test.py`

### Test Class Naming

- **Pattern**: `Test<FeatureName>` or `<FeatureName>Test`
- **Examples**:
  - `class TestDecimalConversion(unittest.TestCase):`
  - `class DynamoDBModelUnitTest(unittest.TestCase):`

### Test Method Naming

- **Pattern**: `test_<what_is_being_tested>`
- Be descriptive and specific
- **Examples**:
  - `test_map_with_decimal_conversion()`
  - `test_legacy_pattern_still_works()`
  - `test_arithmetic_operations_no_typeerror()`

## Core Testing Patterns

### 1. Backward Compatibility Testing

When introducing enhancements or changes, always create tests that verify existing behavior is preserved.

```python
def test_legacy_pattern_still_works(self):
    """
    Test that legacy pattern with manual conversion still works
    
    This ensures backward compatibility for existing code.
    """
    # Arrange - Create data in legacy format
    legacy_data = {
        "field": Decimal("4.5")
    }
    
    # Act - Use legacy pattern
    result = LegacyModel().map(legacy_data)
    
    # Assert - Verify behavior unchanged
    self.assertIsInstance(result.field, float)
    self.assertEqual(result.field, 4.5)

def test_new_pattern_works(self):
    """Test that new enhanced pattern works correctly"""
    # Arrange - Create data
    data = {
        "field": Decimal("4.5")
    }
    
    # Act - Use new pattern
    result = ModernModel().map(data)
    
    # Assert - Verify enhancement works
    self.assertIsInstance(result.field, float)
    self.assertEqual(result.field, 4.5)

def test_legacy_and_modern_produce_same_results(self):
    """Verify legacy and modern patterns produce equivalent results"""
    data = {"field": Decimal("4.5")}
    
    legacy = LegacyModel().map(data)
    modern = ModernModel().map(data)
    
    # Both should produce identical results
    self.assertEqual(legacy.field, modern.field)
    self.assertEqual(type(legacy.field), type(modern.field))
```

### 2. Model Mapping Tests

Test that models correctly map from DynamoDB responses to Python objects.

```python
def test_model_map_basic(self):
    """Test basic model mapping"""
    # Arrange
    data = {
        "id": "123",
        "name": "Test",
        "age": 30
    }
    
    # Act
    model = UserModel().map(data)
    
    # Assert
    self.assertEqual(model.id, "123")
    self.assertEqual(model.name, "Test")
    self.assertEqual(model.age, 30)
    self.assertIsInstance(model, UserModel)

def test_model_map_with_dynamodb_response_structure(self):
    """Test mapping with full DynamoDB response"""
    dynamodb_response = {
        "Item": {
            "id": "456",
            "name": "Test"
        },
        "ResponseMetadata": {
            "RequestId": "abc123",
            "HTTPStatusCode": 200
        }
    }
    
    model = UserModel().map(dynamodb_response)
    
    self.assertEqual(model.id, "456")
    self.assertEqual(model.name, "Test")
```

### 3. Type Conversion Tests

Test that type conversions work correctly, especially for numeric types.

```python
def test_decimal_to_float_conversion(self):
    """Test Decimal to float conversion"""
    data = {"price": Decimal("19.99")}
    
    product = ProductModel().map(data)
    
    self.assertIsInstance(product.price, float)
    self.assertEqual(product.price, 19.99)

def test_decimal_whole_number_to_int_conversion(self):
    """Test that whole number Decimals convert to int"""
    data = {"quantity": Decimal("5")}
    
    product = ProductModel().map(data)
    
    self.assertIsInstance(product.quantity, int)
    self.assertEqual(product.quantity, 5)

def test_mixed_types_handled_correctly(self):
    """Test mixed Decimal and native types"""
    data = {
        "price": Decimal("19.99"),  # Decimal
        "quantity": 10,              # Already int
        "weight": 2.5                # Already float
    }
    
    product = ProductModel().map(data)
    
    self.assertIsInstance(product.price, float)
    self.assertIsInstance(product.quantity, int)
    self.assertIsInstance(product.weight, float)
```

### 4. Nested Structure Tests

Test that nested dictionaries and lists are handled correctly.

```python
def test_nested_dict_conversion(self):
    """Test conversion in nested dictionaries"""
    data = {
        "metrics": {
            "revenue": Decimal("99.99"),
            "orders": Decimal("10")
        }
    }
    
    report = ReportModel().map(data)
    
    self.assertIsInstance(report.metrics["revenue"], float)
    self.assertIsInstance(report.metrics["orders"], int)

def test_nested_list_conversion(self):
    """Test conversion in nested lists"""
    data = {
        "scores": [Decimal("1.5"), Decimal("2.0"), Decimal("3")]
    }
    
    metrics = MetricsModel().map(data)
    
    self.assertIsInstance(metrics.scores[0], float)
    self.assertIsInstance(metrics.scores[1], float)
    self.assertIsInstance(metrics.scores[2], int)

def test_complex_nested_structure(self):
    """Test deeply nested structures"""
    data = {
        "data": {
            "items": [
                {"price": Decimal("10.99"), "qty": Decimal("2")},
                {"price": Decimal("20.99"), "qty": Decimal("1")}
            ]
        }
    }
    
    result = Model().map(data)
    
    # Verify all nested values converted
    for item in result.data["items"]:
        self.assertIsInstance(item["price"], float)
        self.assertIsInstance(item["qty"], int)
```

### 5. Edge Case Tests

Test boundary conditions and edge cases.

```python
def test_empty_collections(self):
    """Test empty collections handled correctly"""
    data = {"items": [], "metadata": {}}
    
    model = Model().map(data)
    
    self.assertEqual(model.items, [])
    self.assertEqual(model.metadata, {})

def test_none_values_preserved(self):
    """Test that None values are preserved"""
    data = {"id": "123", "name": None}
    
    model = Model().map(data)
    
    self.assertEqual(model.id, "123")
    self.assertIsNone(model.name)

def test_boolean_values_not_affected(self):
    """Test booleans not affected by numeric conversion"""
    data = {
        "enabled": True,
        "count": Decimal("5")
    }
    
    model = Model().map(data)
    
    self.assertIsInstance(model.enabled, bool)
    self.assertTrue(model.enabled)
    self.assertIsInstance(model.count, int)
```

### 6. Arithmetic Operation Tests

Test that mathematical operations work without type errors.

```python
def test_arithmetic_operations_no_typeerror(self):
    """Test arithmetic operations work after conversion"""
    data = {
        "price": Decimal("19.99"),
        "cost": Decimal("12.50"),
        "quantity": Decimal("10")
    }
    
    product = ProductModel().map(data)
    
    # These should not raise TypeError
    profit = product.price - product.cost
    total = product.price * product.quantity
    
    self.assertAlmostEqual(profit, 7.49, places=2)
    self.assertAlmostEqual(total, 199.9, places=1)

def test_comparison_operations_work(self):
    """Test comparison operations work without conversion"""
    data = {"price": Decimal("19.99")}
    
    product = ProductModel().map(data)
    
    # All comparisons should work
    self.assertTrue(product.price > 10.0)
    self.assertTrue(product.price < 25.0)
    self.assertFalse(product.price == 20.0)
```

### 7. Round-Trip Tests

Test that data can be converted to a model and back to a dictionary.

```python
def test_round_trip_compatibility(self):
    """Test data can round-trip through map and to_dictionary"""
    original_data = {
        "id": "123",
        "name": "Test",
        "price": 24.99
    }
    
    # Map to model
    model = Model().map(original_data)
    
    # Convert back to dictionary
    result_dict = model.to_dictionary()
    
    # Values should match
    self.assertEqual(result_dict["id"], original_data["id"])
    self.assertEqual(result_dict["name"], original_data["name"])
    self.assertEqual(result_dict["price"], original_data["price"])
```

### 8. DynamoDB Index Tests

Test DynamoDB index generation and key handling.

```python
def test_primary_key_generation(self):
    """Test primary key is generated correctly"""
    data = {"id": "123"}
    
    user = UserModel().map(data)
    
    primary = user.indexes.primary
    self.assertEqual(primary.partition_key.value, "user#123")
    self.assertEqual(primary.sort_key.value, "user#123")

def test_gsi_key_generation(self):
    """Test GSI keys are generated correctly"""
    data = {"id": "123", "email": "test@example.com"}
    
    user = UserModel().map(data)
    
    gsi = user.get_key("gsi1")
    key = gsi.key()
    
    self.assertEqual(key["gsi1_pk"], "users#")
    self.assertEqual(key["gsi1_sk"], "email#test@example.com")
```

## Test Fixtures and Setup

### Using setUp and tearDown

```python
class TestMyFeature(unittest.TestCase):
    """Test suite for my feature"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.test_data = {
            "id": "123",
            "name": "Test"
        }
        self.model = MyModel()
    
    def tearDown(self):
        """Clean up after each test"""
        # Reset state if needed
        pass
    
    def test_something(self):
        """Test something"""
        result = self.model.map(self.test_data)
        self.assertEqual(result.id, "123")
```

### Using Mock Objects

```python
from unittest.mock import Mock, patch

class TestDynamoDBOperations(unittest.TestCase):
    """Test DynamoDB operations with mocking"""
    
    @patch('boto3_assist.dynamodb.dynamodb.DynamoDB.dynamodb_resource')
    def test_get_method(self, mock_resource):
        """Test get method with mocked DynamoDB"""
        # Arrange
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': 'test', 'price': Decimal('99.99')}
        }
        
        dynamodb = DynamoDB()
        
        # Act
        result = dynamodb.get(
            key={'id': 'test'},
            table_name='test_table'
        )
        
        # Assert
        self.assertEqual(result['Item']['id'], 'test')
        self.assertIsInstance(result['Item']['price'], float)
```

## Running Tests

### Running All Tests

```bash
# Using pytest (recommended)
.venv/bin/pytest

# Using unittest
.venv/bin/python -m unittest discover -s tests/unit

# Run specific test file
.venv/bin/pytest tests/unit/dynamodb/decimal_backward_compatibility_test.py
```

### Running Specific Tests

```bash
# Run specific test class
.venv/bin/pytest tests/unit/dynamodb/test_file.py::TestClassName

# Run specific test method
.venv/bin/pytest tests/unit/dynamodb/test_file.py::TestClassName::test_method_name

# Run with verbose output
.venv/bin/pytest -v

# Run with coverage
.venv/bin/pytest --cov=src/boto3_assist
```

### Using unittest

```bash
# Run all tests
.venv/bin/python -m unittest discover

# Run specific test file
.venv/bin/python -m unittest tests.unit.dynamodb.decimal_backward_compatibility_test

# Run specific test class
.venv/bin/python -m unittest tests.unit.dynamodb.decimal_backward_compatibility_test.TestDecimalBackwardCompatibility

# Run specific test method
.venv/bin/python -m unittest tests.unit.dynamodb.decimal_backward_compatibility_test.TestDecimalBackwardCompatibility.test_legacy_pattern_still_works
```

## Test Documentation

### Docstring Format

Every test should have a clear docstring explaining what it tests:

```python
def test_feature_behavior(self):
    """
    Test that feature behaves correctly under specific conditions
    
    This test verifies that:
    1. Input data is processed correctly
    2. Output matches expected format
    3. Edge cases are handled properly
    """
    # Test implementation
```

### Test Organization Comments

Use comments to organize complex tests:

```python
def test_complex_scenario(self):
    """Test a complex scenario"""
    # Arrange - Set up test data and conditions
    data = {"id": "123"}
    model = Model()
    
    # Act - Execute the code being tested
    result = model.map(data)
    
    # Assert - Verify the results
    self.assertEqual(result.id, "123")
```

## Test Coverage Goals

- **Unit Tests**: Cover all public methods and key private methods
- **Edge Cases**: Test boundary conditions, empty inputs, None values
- **Type Safety**: Verify type conversions and type hints
- **Backward Compatibility**: Test that changes don't break existing code
- **Error Handling**: Test error conditions and exceptions

## Best Practices

### 1. Test Independence

- Each test should be independent
- Don't rely on test execution order
- Use setUp/tearDown for shared setup

### 2. Clear Assertions

```python
# Good: Specific assertion with clear message
self.assertEqual(result.price, 19.99, "Price should be converted to float")

# Good: Test one thing per test
def test_price_is_float(self):
    """Test that price is converted to float"""
    # ...

# Avoid: Testing multiple unrelated things
def test_everything(self):
    """Test everything about the model"""
    # Tests too many things
```

### 3. Use Appropriate Assertions

```python
# Type checking
self.assertIsInstance(value, float)

# Equality
self.assertEqual(actual, expected)

# Approximate equality for floats
self.assertAlmostEqual(value, 19.99, places=2)

# Boolean checks
self.assertTrue(condition)
self.assertFalse(condition)

# None checks
self.assertIsNone(value)
self.assertIsNotNone(value)

# Container checks
self.assertIn(item, container)
self.assertNotIn(item, container)

# Exception checks
with self.assertRaises(ValueError):
    code_that_should_raise()
```

### 4. Test Data

```python
# Good: Create test data in the test
def test_feature(self):
    test_data = {"id": "123", "name": "Test"}
    result = Model().map(test_data)
    # ...

# Good: Use fixtures for shared data
def setUp(self):
    self.standard_user_data = {
        "id": "123",
        "name": "Test User"
    }
```

### 5. Avoid Test Interdependencies

```python
# Bad: Tests depend on each other
def test_create(self):
    self.user = create_user()  # Sets instance variable

def test_update(self):
    self.user.name = "Updated"  # Depends on previous test

# Good: Each test is independent
def test_create(self):
    user = create_user()
    self.assertIsNotNone(user)

def test_update(self):
    user = create_user()
    user.name = "Updated"
    self.assertEqual(user.name, "Updated")
```

## Example: Complete Test Suite

```python
"""
Complete test suite example for a feature
"""
import unittest
from decimal import Decimal
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class ProductModel(DynamoDBModelBase):
    """Test model for products"""
    def __init__(self):
        super().__init__()
        self.id: str = None
        self.name: str = None
        self.price: float = 0.0
        self.quantity: int = 0


class TestProductModel(unittest.TestCase):
    """Test suite for ProductModel"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_product_data = {
            "id": "prod_123",
            "name": "Test Product",
            "price": Decimal("19.99"),
            "quantity": Decimal("5")
        }
    
    def test_basic_mapping(self):
        """Test basic model mapping"""
        product = ProductModel().map(self.test_product_data)
        
        self.assertEqual(product.id, "prod_123")
        self.assertEqual(product.name, "Test Product")
        self.assertIsInstance(product, ProductModel)
    
    def test_decimal_conversion(self):
        """Test Decimal values are converted correctly"""
        product = ProductModel().map(self.test_product_data)
        
        self.assertIsInstance(product.price, float)
        self.assertEqual(product.price, 19.99)
        self.assertIsInstance(product.quantity, int)
        self.assertEqual(product.quantity, 5)
    
    def test_arithmetic_operations(self):
        """Test arithmetic operations work correctly"""
        product = ProductModel().map(self.test_product_data)
        
        total = product.price * product.quantity
        self.assertAlmostEqual(total, 99.95, places=2)
    
    def test_empty_product(self):
        """Test mapping empty product data"""
        empty_data = {}
        product = ProductModel().map(empty_data)
        
        self.assertIsNone(product.id)
        self.assertIsNone(product.name)


if __name__ == '__main__':
    unittest.main()
```

## Related Documentation

- [Defining Models](defining-models.md) - Model design patterns
- [Design Patterns](design-patterns.md) - Architecture patterns
- [Defining Services](defining-services.md) - Service layer patterns
- [BOTO3_ASSIST_BEFORE_AFTER.md](issues/BOTO3_ASSIST_BEFORE_AFTER.md) - Decimal handling examples

## Summary

Following these test patterns ensures:

- ✅ **Comprehensive Coverage**: All functionality is tested
- ✅ **Backward Compatibility**: Changes don't break existing code
- ✅ **Maintainability**: Tests are clear and easy to update
- ✅ **Reliability**: Code changes are validated automatically
- ✅ **Documentation**: Tests serve as usage examples

Always run the test suite before committing changes and when enhancing functionality to ensure no regressions.
