# Quick Reference: Runtime DynamoDB Key Debugging

## Problem
When debugging DynamoDB queries at runtime, you need to see the actual partition key and sort key values being used in the query condition expression.

## Old Way ❌ (Not Recommended)

```python
key = index.key(query_key=True, condition="begins_with")

# Accessing private attributes - fragile!
pk_value = key._values[0]._values[1]
sk_value = key._values[1]._values[1]
operator = key._values[1].expression_operator
format_str = key._values[1].expression_format
```

**Problems:**
- Accesses private/internal attributes
- May break if boto3 changes implementation
- Hard to read and maintain
- No IDE autocomplete support

## New Way ✅ (Recommended)

```python
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex

# Build your query key
index = model.indexes.get("gsi1")
key_expression = index.key(query_key=True, condition="begins_with")

# Extract values cleanly - optionally include the index
debug_info = DynamoDBIndex.extract_key_values(key_expression, index)

# Access the values
index_name = debug_info.get('index_name')  # 'gsi1' (if passed)
pk_value = debug_info['partition_key']['value']
pk_attr = debug_info['partition_key']['attribute']

sk_value = debug_info['sort_key']['value']
sk_attr = debug_info['sort_key']['attribute']
operator = debug_info['sort_key']['operator']
format_str = debug_info['sort_key']['format']
```

### Include Index Name (Optional)

You can optionally include the index name in the results three ways:

```python
# Option 1: Pass the DynamoDBIndex object
debug = DynamoDBIndex.extract_key_values(key_expression, index)
print(debug['index_name'])  # 'gsi1'

# Option 2: Pass just the index name as a string
debug = DynamoDBIndex.extract_key_values(key_expression, "gsi1")
print(debug['index_name'])  # 'gsi1'

# Option 3: Don't pass anything (no index_name in results)
debug = DynamoDBIndex.extract_key_values(key_expression)
print(debug.get('index_name'))  # None
```

**Benefits:**
- ✅ Clean, documented API
- ✅ IDE autocomplete support
- ✅ Handles different condition types (begins_with, eq, gt, between, etc.)
- ✅ Safe from boto3 internal changes
- ✅ Easy to read and maintain

## Common Use Cases

### 1. Log Query Keys Before Execution

```python
def query_tickets(category: str, status: str):
    ticket = SupportTicket()
    ticket.category = category
    ticket.status = status
    
    index = ticket.indexes.get("gsi1")
    key_expr = index.key(query_key=True, condition="begins_with")
    
    # Debug: See exactly what you're querying (with index name)
    debug = DynamoDBIndex.extract_key_values(key_expr, index)
    logger.debug(f"Querying {debug['index_name']}")
    logger.debug(f"  PK={debug['partition_key']['value']}")
    logger.debug(f"  SK={debug['sort_key']['value']}")
    logger.debug(f"  Condition: {debug['sort_key']['operator']}")
    
    return db.query(table_name="tickets", index_name="gsi1", key=key_expr)
```

### 2. Troubleshoot Query Issues

```python
# Your query isn't returning results...
key_expr = model.indexes.get("gsi1").key(query_key=True, condition="begins_with")
debug = DynamoDBIndex.extract_key_values(key_expr)

print(f"Expected PK format: 'category#electronics'")
print(f"Actual PK value: '{debug['partition_key']['value']}'")
print(f"Expected SK prefix: 'product#'")
print(f"Actual SK value: '{debug['sort_key']['value']}'")
print(f"Condition: {debug['sort_key']['operator']}")

# Now you can see if there's a mismatch!
```

### 3. Unit Testing Key Generation

```python
def test_query_key_format():
    ticket = SupportTicket()
    ticket.category = "support"
    ticket.status = "open"
    
    key_expr = ticket.indexes.get("gsi1").key(query_key=True)
    debug = DynamoDBIndex.extract_key_values(key_expr)
    
    # Assert the key format is correct
    assert debug['partition_key']['value'] == "inbox#support#status#open"
    assert debug['sort_key']['attribute'] == "gsi1_sk"
    assert debug['sort_key']['operator'] == "begins_with"
```

### 4. Inspect 'between' Queries

```python
key_expr = index.key(
    query_key=True,
    condition="between",
    low_value="2024-01-01",
    high_value="2024-12-31"
)

debug = DynamoDBIndex.extract_key_values(key_expr)

print(f"Range: {debug['sort_key']['value_low']} to {debug['sort_key']['value_high']}")
print(f"Operator: {debug['sort_key']['operator']}")  # 'BETWEEN'
```

## Output Format

The `extract_key_values()` method returns a dictionary with this structure:

```python
{
    'index_name': 'gsi1',                 # Only present if index param provided
    'partition_key': {
        'attribute': 'gsi1_pk',           # The attribute name (e.g., pk, gsi1_pk)
        'value': 'inbox#support#status#open'  # The actual value
    },
    'sort_key': {                         # Only present if sort key is used
        'attribute': 'gsi1_sk',           # The attribute name (e.g., sk, gsi1_sk)
        'value': 'priority#medium#ts',    # The actual value
        'operator': 'begins_with',        # The condition operator
        'format': '{operator}({0}, {1})'  # The expression format
    }
}
```

For **between** queries:
```python
{
    'index_name': 'gsi1',                 # If provided
    'partition_key': { ... },
    'sort_key': {
        'attribute': 'gsi1_sk',
        'value_low': 'ts#2024-01-01',     # Low value
        'value_high': 'ts#2024-12-31',    # High value
        'operator': 'BETWEEN',
        'format': '{0} {operator} {1} AND {2}'
    }
}
```

## Examples

See the complete examples in:
- `examples/dynamodb/runtime_key_debugging_example.py`

## Summary

**Instead of:**
```python
key._values[0]._values[1]  # ❌
```

**Use:**
```python
debug = DynamoDBIndex.extract_key_values(key)
debug['partition_key']['value']  # ✅
```

This provides a clean, maintainable way to inspect DynamoDB query keys at runtime for debugging and troubleshooting!
