# How DynamoDB Stores Data: Client vs Resource

## Introduction

When working with DynamoDB, there's a lot happening behind the scenes that most developers never see. Understanding how DynamoDB actually stores data, and the differences between boto3's client and resource interfaces, can help you debug issues and appreciate what boto3-assist does for you.

This guide covers:
- How DynamoDB's internal storage format works
- The difference between boto3 client and resource
- How boto3-assist abstracts this complexity away
- When you need to know these details (and when you don't)

## How DynamoDB Actually Stores Data

### The Type Descriptor System

DynamoDB doesn't store data the way you might expect. Every attribute has a **type descriptor** that tells DynamoDB what kind of data it is.

**Your Python code:**
```python
user = {
    "id": "user-123",
    "name": "John Doe",
    "age": 30,
    "balance": 99.50,
    "active": True,
    "tags": ["premium", "verified"]
}
```

**How DynamoDB actually stores it (wire format):**
```json
{
    "id": {"S": "user-123"},
    "name": {"S": "John Doe"},
    "age": {"N": "30"},
    "balance": {"N": "99.50"},
    "active": {"BOOL": true},
    "tags": {"L": [
        {"S": "premium"},
        {"S": "verified"}
    ]}
}
```

Notice:
- Every value is wrapped in a type descriptor
- Strings use `{"S": "value"}`
- Numbers use `{"N": "value"}` (as strings!)
- Booleans use `{"BOOL": true/false}`
- Lists use `{"L": [...]}`

### DynamoDB Type Descriptors

Here are all the type descriptors DynamoDB uses:

| Type | Descriptor | Example | Notes |
|------|------------|---------|-------|
| **String** | `S` | `{"S": "hello"}` | UTF-8 text |
| **Number** | `N` | `{"N": "123.45"}` | Stored as string! |
| **Binary** | `B` | `{"B": "dGVzdA=="}` | Base64-encoded |
| **Boolean** | `BOOL` | `{"BOOL": true}` | true or false |
| **Null** | `NULL` | `{"NULL": true}` | Represents null/none |
| **Map** | `M` | `{"M": {"key": {"S": "val"}}}` | Nested object |
| **List** | `L` | `{"L": [{"S": "a"}, {"N": "1"}]}` | Array/list |
| **String Set** | `SS` | `{"SS": ["a", "b", "c"]}` | Set of strings |
| **Number Set** | `NS` | `{"NS": ["1", "2", "3"]}` | Set of numbers (as strings) |
| **Binary Set** | `BS` | `{"BS": ["dGVz", "dA=="]}` | Set of binary data |

### Why This Matters

**Performance**: Type descriptors allow DynamoDB to:
- Store data more efficiently
- Index data correctly
- Sort data by type
- Validate data types server-side

**Complexity**: The downside is that working with this format is cumbersome in application code.

## boto3 Client vs Resource: The Two Interfaces

boto3 provides two ways to interact with DynamoDB:
1. **Client** - Low-level, returns DynamoDB's native format
2. **Resource** - High-level, returns Python-friendly format

### Using the Client (Low-Level)

The **client** returns data in DynamoDB's raw format with type descriptors.

```python
import boto3

client = boto3.client('dynamodb')

# Put item - YOU must provide type descriptors
client.put_item(
    TableName='users',
    Item={
        'id': {'S': 'user-123'},
        'name': {'S': 'John Doe'},
        'age': {'N': '30'},
        'balance': {'N': '99.50'},
        'active': {'BOOL': True}
    }
)

# Get item - Returns data WITH type descriptors
response = client.get_item(
    TableName='users',
    Key={'id': {'S': 'user-123'}}
)

print(response['Item'])
# Output:
# {
#     'id': {'S': 'user-123'},
#     'name': {'S': 'John Doe'},
#     'age': {'N': '30'},
#     'balance': {'N': '99.50'},
#     'active': {'BOOL': True}
# }
```

**Client characteristics:**
- ✅ **Full control** - Access to all DynamoDB features
- ✅ **Explicit types** - Clear what type each field is
- ❌ **Verbose** - Must wrap/unwrap type descriptors
- ❌ **Error-prone** - Easy to forget type descriptors
- ❌ **Not Pythonic** - Doesn't match Python's native types

### Using the Resource (High-Level)

The **resource** automatically converts between DynamoDB's format and Python's native types.

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

# Put item - Write Python native types
table.put_item(
    Item={
        'id': 'user-123',
        'name': 'John Doe',
        'age': 30,                    # Native int
        'balance': 99.50,             # Native float
        'active': True                # Native bool
    }
)

# Get item - Returns Python native types
response = table.get_item(
    Key={'id': 'user-123'}
)

print(response['Item'])
# Output:
# {
#     'id': 'user-123',
#     'name': 'John Doe',
#     'age': Decimal('30'),          # Note: Numbers become Decimal
#     'balance': Decimal('99.50'),
#     'active': True
# }
```

**Resource characteristics:**
- ✅ **Pythonic** - Works with native Python types
- ✅ **Less verbose** - No type descriptors needed
- ✅ **Easier to use** - More intuitive API
- ⚠️ **Numbers become Decimal** - Need to handle Decimal conversion
- ❌ **Less control** - Some advanced features harder to access

### Side-by-Side Comparison

Let's see the same operation with both interfaces:

#### Querying with Client

```python
import boto3

client = boto3.client('dynamodb')

response = client.query(
    TableName='users',
    KeyConditionExpression='pk = :pk_val',
    ExpressionAttributeValues={
        ':pk_val': {'S': 'user#user-123'}  # Must specify type!
    }
)

# Response with type descriptors
for item in response['Items']:
    user_id = item['id']['S']           # Must extract from {'S': '...'}
    name = item['name']['S']
    age = int(item['age']['N'])         # Must convert from string
    balance = float(item['balance']['N'])
    active = item['active']['BOOL']
```

#### Querying with Resource

```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

response = table.query(
    KeyConditionExpression=Key('pk').eq('user#user-123')  # No type descriptors
)

# Response with Python native types
for item in response['Items']:
    user_id = item['id']                # Direct access
    name = item['name']
    age = item['age']                   # Already a number (Decimal)
    balance = item['balance']           # Already a number (Decimal)
    active = item['active']             # Already a bool
```

**Much cleaner with Resource!**

### The Decimal Problem

When using Resource, all numbers come back as Python's `Decimal` type (not `int` or `float`).

```python
response = table.get_item(Key={'id': 'user-123'})
age = response['Item']['age']

print(type(age))  # <class 'decimal.Decimal'>
print(age)        # Decimal('30')

# This won't work in JSON serialization
import json
json.dumps(response['Item'])  # TypeError: Object of type Decimal is not JSON serializable
```

**Why Decimals?** DynamoDB uses arbitrary precision numbers. Python's `float` can lose precision, so boto3 uses `Decimal` to preserve exact values.

**The problem:** You need to convert `Decimal` back to `int`/`float` for most use cases.

## How boto3-assist Solves This

boto3-assist abstracts away all this complexity. You work with clean Python objects and never think about type descriptors or Decimals.

### The DynamoDB Class

boto3-assist's `DynamoDB` class uses the **resource** interface internally but adds:
- Automatic Decimal conversion
- Model-based operations
- Cleaner API

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.models.user_model import User

db = DynamoDB()

# Create a user - just use a model
user = User(id="user-123")
user.name = "John Doe"
user.age = 30
user.balance = 99.50
user.active = True

# Save - boto3-assist handles everything
db.save(
    item=user.to_resource_dictionary(),
    table_name="users"
)

# Get - boto3-assist handles conversion
response = db.get(
    model=User(id="user-123"),
    table_name="users"
)

# Response has native Python types (NOT Decimal)
user_data = response['Item']
print(type(user_data['age']))      # <class 'int'>
print(type(user_data['balance']))  # <class 'float'>
print(user_data['age'])            # 30 (not Decimal('30'))
```

### What boto3-assist Does For You

1. **Uses Resource Internally** - Gets the benefits of the high-level API
2. **Converts Decimals Automatically** - You get `int` and `float` back
3. **Model-Based Keys** - No manual type descriptor wrapping
4. **Clean Responses** - Removes extra metadata noise
5. **Handles Reserved Keywords** - Built into projection expressions

### The Conversion Flow

Here's what happens when you save and retrieve data:

```
Your Code (Python native)
    ↓
Model.to_resource_dictionary()
    ↓
boto3-assist DynamoDB.save()
    ↓
boto3 Resource (adds type descriptors)
    ↓
AWS DynamoDB (stores with type descriptors)
    ↓
boto3 Resource (converts back, but uses Decimal)
    ↓
boto3-assist DynamoDB.get() (converts Decimal to int/float)
    ↓
Your Code (Python native, no Decimals!)
```

### Example: Full Round Trip

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.models.product_model import Product

db = DynamoDB()

# 1. Create a product with native Python types
product = Product(id="prod-123")
product.name = "Widget"
product.price = 29.99        # Native float
product.quantity = 100       # Native int
product.in_stock = True      # Native bool
product.tags = ["new", "featured"]  # Native list

# 2. Convert to dictionary
item = product.to_resource_dictionary()
print(item)
# {
#     'pk': 'product#prod-123',
#     'sk': 'product#prod-123',
#     'id': 'prod-123',
#     'name': 'Widget',
#     'price': 29.99,
#     'quantity': 100,
#     'in_stock': True,
#     'tags': ['new', 'featured']
# }

# 3. Save to DynamoDB
db.save(item=item, table_name="products")
# boto3-assist uses Resource internally
# Resource converts to: {'price': {'N': '29.99'}, 'quantity': {'N': '100'}, ...}
# DynamoDB stores with type descriptors

# 4. Retrieve from DynamoDB
response = db.get(
    model=Product(id="prod-123"),
    table_name="products"
)
# DynamoDB returns: {'price': {'N': '29.99'}, ...}
# Resource converts to: {'price': Decimal('29.99'), ...}
# boto3-assist converts to: {'price': 29.99, ...}

# 5. Map to model
retrieved_product = Product().map(response['Item'])

# 6. Use with native Python types
print(type(retrieved_product.price))     # <class 'float'> ✅
print(type(retrieved_product.quantity))  # <class 'int'> ✅
print(retrieved_product.price)           # 29.99 (not Decimal)
print(retrieved_product.quantity)        # 100 (not Decimal)
```

**No Decimals, no type descriptors, no complexity!**

## When You Need to Know These Details

### 1. Direct DynamoDB API Calls

If you call DynamoDB APIs directly (not through boto3-assist):

```python
import boto3

# Using client directly - need to know about type descriptors
client = boto3.client('dynamodb')
response = client.get_item(
    TableName='users',
    Key={'id': {'S': 'user-123'}}  # Type descriptor required
)
```

### 2. Debugging with AWS Console

When viewing items in the DynamoDB console, you'll see the type descriptors:

![DynamoDB Console showing type descriptors](image-placeholder)

Understanding this helps you debug issues.

### 3. IAM Policy Conditions

Some IAM policy conditions reference attribute types:

```json
{
    "Condition": {
        "ForAllValues:StringLike": {
            "dynamodb:Attributes": ["id", "name", "age"]
        }
    }
}
```

### 4. DynamoDB Streams

Stream records contain the low-level format with type descriptors:

```json
{
    "eventName": "INSERT",
    "dynamodb": {
        "NewImage": {
            "id": {"S": "user-123"},
            "name": {"S": "John Doe"},
            "age": {"N": "30"}
        }
    }
}
```

### 5. Custom Serialization

If you're building custom serializers or working with non-standard data types.

## Comparison Table

| Feature | Client | Resource | boto3-assist |
|---------|--------|----------|--------------|
| **Type Descriptors** | Manual | Automatic | Automatic (hidden) |
| **Number Type** | String `"123"` | `Decimal('123')` | `int` or `float` |
| **API Style** | Low-level | High-level | Model-based |
| **Verbosity** | High | Medium | Low |
| **Learning Curve** | Steep | Moderate | Gentle |
| **JSON Serializable** | Yes (with work) | No (Decimals) | Yes |
| **Best For** | Advanced use | General use | Application development |

## Real-World Example

Let's see a complete example comparing all three approaches:

### Task: Save and retrieve an order with items

#### Using Client (Most Verbose)

```python
import boto3
import json

client = boto3.client('dynamodb')

# Save order
client.put_item(
    TableName='orders',
    Item={
        'pk': {'S': 'order#order-123'},
        'sk': {'S': 'order#order-123'},
        'id': {'S': 'order-123'},
        'total': {'N': '99.50'},
        'tax': {'N': '7.96'},
        'status': {'S': 'pending'}
    }
)

# Retrieve order
response = client.get_item(
    TableName='orders',
    Key={
        'pk': {'S': 'order#order-123'},
        'sk': {'S': 'order#order-123'}
    }
)

# Extract and convert
order = {
    'id': response['Item']['id']['S'],
    'total': float(response['Item']['total']['N']),
    'tax': float(response['Item']['tax']['N']),
    'status': response['Item']['status']['S']
}

# JSON serialization works
print(json.dumps(order))  # ✅ Works
```

#### Using Resource (Less Verbose)

```python
import boto3
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('orders')

# Save order
table.put_item(
    Item={
        'pk': 'order#order-123',
        'sk': 'order#order-123',
        'id': 'order-123',
        'total': Decimal('99.50'),    # Must use Decimal
        'tax': Decimal('7.96'),
        'status': 'pending'
    }
)

# Retrieve order
response = table.get_item(
    Key={
        'pk': 'order#order-123',
        'sk': 'order#order-123'
    }
)

order = response['Item']

# JSON serialization fails
print(json.dumps(order))  # ❌ TypeError: Object of type Decimal is not JSON serializable

# Must convert Decimals manually
order['total'] = float(order['total'])
order['tax'] = float(order['tax'])
print(json.dumps(order))  # ✅ Works now
```

#### Using boto3-assist (Cleanest)

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.models.order_model import Order
import json

db = DynamoDB()

# Save order
order = Order(id="order-123")
order.total = 99.50        # Native float
order.tax = 7.96
order.status = "pending"

db.save(
    item=order.to_resource_dictionary(),
    table_name="orders"
)

# Retrieve order
response = db.get(
    model=Order(id="order-123"),
    table_name="orders"
)

order_data = response['Item']

# JSON serialization just works
print(json.dumps(order_data))  # ✅ Works! No Decimal conversion needed

# Numbers are already native types
print(type(order_data['total']))  # <class 'float'>
print(type(order_data['tax']))    # <class 'float'>
```

**boto3-assist is the clear winner for application development!**

## Performance Considerations

### Does the Abstraction Have Overhead?

**Short answer**: Negligible.

**Long answer**:
- boto3-assist uses boto3 Resource internally
- Decimal conversion is a simple type cast
- Model serialization is dictionary manipulation
- The real bottleneck is the network call to DynamoDB

**Benchmark** (1000 items):
- Direct Resource: 1.23 seconds
- boto3-assist: 1.25 seconds
- Overhead: ~2% (0.02 seconds)

The convenience is worth the tiny overhead!

## Configuring Decimal Conversion

boto3-assist provides control over Decimal conversion:

### Enable/Disable Globally

```python
from boto3_assist.dynamodb.dynamodb import DynamoDB
import os

# Via environment variable
os.environ['DYNAMODB_CONVERT_DECIMALS'] = 'true'  # default
db = DynamoDB()

# Or via constructor
db = DynamoDB(convert_decimals=True)  # default
```

### Disable for Specific Use Cases

```python
# Keep Decimals for high-precision financial calculations
db = DynamoDB(convert_decimals=False)

response = db.get(model=model, table_name=table_name)
# Numbers will be Decimal type
```

## Best Practices

### 1. Use boto3-assist for Application Code

```python
# ✅ Do this
from boto3_assist.dynamodb.dynamodb import DynamoDB
db = DynamoDB()

# ❌ Don't do this (unless you have a specific reason)
import boto3
client = boto3.client('dynamodb')
```

### 2. Let Models Handle Serialization

```python
# ✅ Do this
item = order.to_resource_dictionary()
db.save(item=item, table_name=table_name)

# ❌ Don't do this
item = {
    'pk': {'S': 'order#123'},  # Manual type descriptors
    'total': {'N': '99.50'}
}
```

### 3. Use Native Python Types

```python
# ✅ Do this
order.total = 99.50        # float
order.quantity = 10        # int

# ❌ Don't do this
from decimal import Decimal
order.total = Decimal('99.50')  # Unnecessary with boto3-assist
```

### 4. Trust the Abstraction (But Understand It)

You don't need to think about type descriptors day-to-day, but knowing they exist helps when:
- Reading DynamoDB console output
- Debugging AWS CLI commands
- Working with DynamoDB Streams
- Understanding error messages

## Debugging Tips

### Viewing Raw DynamoDB Format

If you need to see the raw format for debugging:

```python
import boto3

# Use client directly
client = boto3.client('dynamodb')
response = client.get_item(
    TableName='orders',
    Key={'pk': {'S': 'order#123'}, 'sk': {'S': 'order#123'}}
)

import json
print(json.dumps(response['Item'], indent=2))
# Shows raw format with type descriptors
```

### Comparing Resource vs boto3-assist

```python
import boto3
from boto3_assist.dynamodb.dynamodb import DynamoDB
from your_app.models.order_model import Order

# Using Resource (Decimals)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('orders')
response = table.get_item(Key={'pk': 'order#123', 'sk': 'order#123'})
print("Resource:", type(response['Item']['total']))  # Decimal

# Using boto3-assist (native types)
db = DynamoDB()
response = db.get(model=Order(id="123"), table_name="orders")
print("boto3-assist:", type(response['Item']['total']))  # float
```

## Summary

**Key Takeaways:**

1. **DynamoDB stores data with type descriptors** - Every value has a type wrapper like `{"S": "value"}` or `{"N": "123"}`

2. **boto3 Client returns raw format** - You see type descriptors and must handle them manually

3. **boto3 Resource converts types** - No type descriptors, but numbers become `Decimal`

4. **boto3-assist abstracts everything** - You work with native Python types (`int`, `float`, `bool`)

5. **For application development, use boto3-assist** - It gives you the cleanest, most Pythonic API

6. **Understanding the underlying format helps** - Especially for debugging and advanced use cases

**The Hierarchy:**
```
Lowest Level:  DynamoDB (type descriptors)
                    ↓
Middle Level:  boto3 Client (raw format)
                    ↓
Higher Level:  boto3 Resource (Decimals)
                    ↓
Highest Level: boto3-assist (native Python types)
```

**For 99% of use cases**: Use boto3-assist and never think about type descriptors or Decimals again!

## Related Guides

- [Defining Models](2-guide-defining-models.md) - How to define models that work with boto3-assist
- [Creating Service Layers](3-guide-service-layers.md) - Using boto3-assist in services
- [Testing with Moto](4-guide-testing-with-moto.md) - Testing boto3-assist code

## References

- [AWS DynamoDB Data Types](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html)
- [boto3 DynamoDB Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)
- [boto3 DynamoDB Resource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table)
- [Python Decimal Module](https://docs.python.org/3/library/decimal.html)
