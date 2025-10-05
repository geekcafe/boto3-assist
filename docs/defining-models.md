# Defining DynamoDB Models with boto3-assist

This guide explains how to create and define DynamoDB models using the `DynamoDBModelBase` class provided by `boto3-assist`. Following these patterns ensures consistency, scalability, and easy integration with the `boto3-assist` ecosystem.

## 1. Introduction to DynamoDBModelBase

The `DynamoDBModelBase` is the foundation for all DynamoDB models in this framework. It provides a rich set of features out of the box, including:

-   **Automatic Serialization**: Convert model instances to and from DynamoDB-compatible dictionaries.
-   **Index Management**: A structured way to define primary keys and global secondary indexes (GSIs).
-   **Data Mapping**: Easily map raw DynamoDB response data to your model instances.
-   **Helper Utilities**: Access to utility functions for common tasks like timestamp conversion and UUID generation.

## 2. Creating a Basic Model

All models should inherit from `DynamoDBModelBase`. Here is an example of a simple `Product` model:

```python
import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey

class Product(DynamoDBModelBase):
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        price: float = 0.0,
        description: Optional[str] = None,
        sku: Optional[str] = None,
    ):
        super().__init__()

        self.id: Optional[str] = id
        self.name: Optional[str] = name
        self.price: float = price
        self.description: Optional[str] = description
        self.sku: Optional[str] = sku

        # Initialize the indexes
        self._setup_indexes()

    def _setup_indexes(self):
        # Index definitions will go here
        pass
```

**Key Principles**:

-   **Inheritance**: Your model must inherit from `DynamoDBModelBase`.
-   **Constructor**: Define your model's attributes in the `__init__` method. Call `super().__init__()` at the beginning.
-   **Index Setup**: Call a private method (e.g., `_setup_indexes()`) at the end of the constructor to define your keys and indexes.

## 3. Setting Up Indexes

DynamoDB keys and indexes are defined within the `_setup_indexes` method using the `DynamoDBIndex` and `DynamoDBKey` classes.

### Primary Key

Every model must have a primary key. The primary key is defined as a `DynamoDBIndex` and added to the model's `indexes` collection.

```python
def _setup_indexes(self):
    primary = DynamoDBIndex()
    primary.name = "primary"
    primary.partition_key.attribute_name = "pk"
    primary.partition_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
    primary.sort_key.attribute_name = "sk"
    primary.sort_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
    self.indexes.add_primary(primary)
```

-   `DynamoDBIndex()`: Creates a new index definition.
-   `partition_key` and `sort_key`: Define the attributes and values for your keys.
-   `attribute_name`: The name of the attribute in the DynamoDB table (e.g., `pk`, `sk`).
-   `value`: A **lambda function** that dynamically generates the key value. Using a lambda is crucial for ensuring the key is generated with the most current attribute values.
-   `DynamoDBKey.build_key()`: A helper to construct composite keys with a consistent separator.
-   `self.indexes.add_primary()`: Registers the index as the primary key.

### Global Secondary Indexes (GSIs)

You can add GSIs to support additional query patterns. GSIs are also defined as `DynamoDBIndex` objects and added using `add_secondary()`.

Here’s how to add a GSI to query all products by name:

```python
# Inside _setup_indexes method

self.indexes.add_secondary(
    DynamoDBIndex(
        index_name="gsi0",
        partition_key=DynamoDBKey(
            attribute_name="gsi0_pk",
            # Use a static value for the partition key to query all products
            value=lambda: DynamoDBKey.build_key(("products", ""))
        ),
        sort_key=DynamoDBKey(
            attribute_name="gsi0_sk",
            value=lambda: DynamoDBKey.build_key(("name", self.name))
        ),
    )
)
```

-   `index_name`: The name of the GSI in your DynamoDB table (e.g., `gsi0`).
-   `add_secondary()`: Registers the index as a GSI.

### Advanced GSI Patterns

Your models can support more complex query patterns by combining static partition keys with simple or composite sort keys.

#### Querying All Items with a Composite Sort Key

This pattern is useful when you want to retrieve all items of a specific type and sort them by multiple fields. For example, to get all users sorted by `last_name` and then `first_name`.

```python
# Inside _setup_indexes for a UserModel

# GSI to list all users, sorted by last name, then first name
gsi_by_lastname = DynamoDBIndex(
    index_name="gsi2",
    partition_key=DynamoDBKey(
        attribute_name="gsi2_pk",
        # Static partition key to group all users together
        value=lambda: DynamoDBKey.build_key(("users", None))
    ),
    sort_key=DynamoDBKey(
        attribute_name="gsi2_sk",
        # Composite sort key
        value=lambda: DynamoDBKey.build_key(
            ("lastname", self.last_name), ("firstname", self.first_name)
        )
    )
)
self.indexes.add_secondary(gsi_by_lastname)
```

**How it works**:
-   **Static Partition Key**: `DynamoDBKey.build_key(("users", None))` generates a static partition key (e.g., `"users"`). This forces all user items into the same item collection within the GSI, allowing you to query all of them at once.
-   **Composite Sort Key**: `DynamoDBKey.build_key(("lastname", self.last_name), ("firstname", self.first_name))` creates a sort key like `lastname#Smith#firstname#John`. This enables lexicographical sorting, first by last name and then by first name.


### What the Generated Keys Look Like

It's helpful to visualize what these key definitions produce. Given a `Product` instance:

```python
product = Product(id='abc-123', name='Mjolnir')
```

When you serialize this model using `to_resource_dictionary()`, the `boto3-assist` framework will generate the following key attributes based on the `lambda` functions in your index setup:

-   **`pk`**: `product#abc-123`
-   **`sk`**: `product#abc-123`
-   **`gsi0_pk`**: `products`
-   **`gsi0_sk`**: `name#Mjolnir`

Your final item in DynamoDB would look something like this:

```json
{
  "pk": "product#abc-123",
  "sk": "product#abc-123",
  "gsi0_pk": "products",
  "gsi0_sk": "name#Mjolnir",
  "id": "abc-123",
  "name": "Mjolnir",
  "price": 0.0,
  "description": null,
  "sku": null
}
```

This structure allows you to:
-   Fetch the product directly using its `pk` and `sk`.
-   Query all products on `gsi0` (where `gsi0_pk` is `"products"`) and sort them by name (`gsi0_sk`).

## 4. Serialization and Deserialization

`DynamoDBModelBase` provides powerful methods for serialization (Python object to dictionary) and deserialization (dictionary to Python object).

### Deserialization with `map()`

The `map()` method is the primary way to populate a model instance from a dictionary. It intelligently handles various DynamoDB response formats.

```python
# Raw DynamoDB item
dynamodb_item = {
    'pk': {'S': 'product#123'},
    'sk': {'S': 'product#123'},
    'name': {'S': 'Mjolnir'},
    'price': {'N': '9999.99'}
}

# Create an empty model and map the data
product = Product().map(dynamodb_item)

print(product.name)  # Output: Mjolnir
print(product.price) # Output: 9999.99
```

As noted in a previous session, the `map()` method can handle:
-   Full DynamoDB responses: `{'Item': {...}, 'ResponseMetadata': {...}}`
-   Item-only responses: `{'Item': {...}}`
-   Plain dictionaries.

### Serialization

There are several methods to convert a model instance to a dictionary:

-   `to_dictionary()`: Returns a dictionary of the model's attributes, excluding any index attributes. This is useful for general-purpose serialization.
-   `to_resource_dictionary()`: Returns a dictionary suitable for the Boto3 DynamoDB **Resource** API, including index attributes.
-   `to_client_dictionary()`: Returns a dictionary suitable for the Boto3 DynamoDB **Client** API, with values serialized into DynamoDB's type format (e.g., `{'S': 'value'}`).

```python
product = Product(id='456', name='Stormbreaker', price=8500.0)

# Get a simple dictionary of attributes
plain_dict = product.to_dictionary()
# {'id': '456', 'name': 'Stormbreaker', 'price': 8500.0, ...}

# Get a dictionary for the DynamoDB Resource API
resource_dict = product.to_resource_dictionary()
# {'pk': 'product#456', 'sk': 'product#456', 'id': '456', ...}

# Get a dictionary for the DynamoDB Client API
client_dict = product.to_client_dictionary()
# {'pk': {'S': 'product#456'}, 'sk': {'S': 'product#456'}, ...}
```

## 5. Best Practices

-   **Models as Data Transfer Objects (DTOs)**: Models should only contain data and serialization logic. Avoid adding business logic or direct database calls (e.g., a `save()` method). Keep that logic in your service layer.
-   **Use Lambda for Keys**: Always use `lambda` functions for key values to ensure they are generated at the time of serialization.
-   **Consistent Naming**: Follow consistent naming conventions for your indexes and attributes (e.g., `gsi0`, `gsi1_pk`, `gsi1_sk`).
-   **Call `_setup_indexes` in `__init__`**: Ensure your indexes are defined every time a model is instantiated.
