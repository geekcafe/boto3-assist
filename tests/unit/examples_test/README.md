# Example Service Tests

This directory contains comprehensive tests demonstrating boto3-assist patterns using Moto for local testing.

## Running Tests

### Using the Virtual Environment

From the project root:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run all example tests
python -m unittest discover -s tests/unit/examples_test

# Run specific test file
python -m unittest tests.unit.examples_test.order_service_test

# Run specific test
python -m unittest tests.unit.examples_test.order_service_test.OrderServiceTest.test_pattern_2_get_order_with_all_items
```

### Using pytest (alternative)

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run all example tests
pytest tests/unit/examples_test/

# Run with verbose output
pytest tests/unit/examples_test/ -v

# Run specific test file
pytest tests/unit/examples_test/order_service_test.py

# Run specific test
pytest tests/unit/examples_test/order_service_test.py::OrderServiceTest::test_pattern_2_get_order_with_all_items
```

## Test Files

### order_service_test.py

Demonstrates **one-to-many relationship** query patterns (Order → OrderItems).

**Key patterns demonstrated:**

1. **Pattern 1: Get only parent**
   - `test_pattern_1_get_order_only()`
   - Query: `pk = "order#123" AND sk = "order#123"`
   - Returns: Just the order

2. **Pattern 2: Get parent + all children**
   - `test_pattern_2_get_order_with_all_items()`
   - Query: `pk = "order#123"` (no sort key)
   - Returns: Order + all items in ONE query

3. **Pattern 3: Get only children**
   - `test_pattern_3_get_only_items()`
   - Query: `pk = "order#123" AND sk begins_with "item#"`
   - Returns: Only the order items

**Additional tests:**
- Key structure verification
- Multiple order isolation
- Empty order handling

### user_service_test.py

Basic CRUD operations for user service.

## What These Tests Demonstrate

✅ **Moto Integration**: All tests use `@mock_aws` - no real AWS connection needed

✅ **Local Testing**: Tests run completely offline using mocked DynamoDB

✅ **Single Table Design**: Shows how pk/sk patterns enable 1:many relationships

✅ **Best Practices**: Follows boto3-assist patterns for services and models

✅ **Real-World Patterns**: Based on actual service implementations in `examples/dynamodb/services/`

## Requirements

Install test dependencies:

```bash
pip install moto[dynamodb] boto3 boto3-assist
```

Or use the requirements file:

```bash
pip install -r requirements-dev.txt
```

## Understanding the Tests

The tests in `order_service_test.py` are specifically designed to demonstrate the **critical concept** that the sort key is **optional** in DynamoDB queries:

- **Partition key**: ALWAYS required
- **Sort key**: Optional - you can omit it, specify it exactly, or use conditions like `begins_with`

This flexibility enables the powerful one-to-many pattern where:
- Parent and children share the same **partition key**
- Parent and children differ in **sort key**
- Querying by partition key alone returns **everything** in that partition

See the [Single Table Design Guide](../../../docs/guide-single-table-design.md) for more details.
