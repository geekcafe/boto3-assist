# Defining Services for DynamoDB Operations

This guide explains how to create a service layer to handle business logic and interact with DynamoDB using `boto3-assist`. The service layer is responsible for all Create, Read, Update, Delete, and List (CRUDL) operations.

## 1. The Role of the Service Layer

The service layer acts as an intermediary between your application's handlers (e.g., API endpoints) and the database. Its primary responsibilities are:

-   **Encapsulating Business Logic**: All logic related to data manipulation resides here.
-   **Interacting with the Database**: Services are the only part of your application that should directly call the `DynamoDB` class.
-   **Using Models**: Services use the `DynamoDBModelBase` models to pass data to and from the database.
-   **Error Handling**: Managing database exceptions and returning consistent responses.

By centralizing database interactions in a service layer, you create a clear separation of concerns, making your application easier to maintain, test, and scale.

## 2. Creating a Basic Service

A service is a Python class that initializes an instance of the `boto3_assist.dynamodb.DynamoDB` class. It also needs the name of the DynamoDB table it will be interacting with, which is typically stored in an environment variable.

Here is a basic `ProductService`:

```python
import os
from typing import Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from ..models.product_model import Product

class ProductService:
    def __init__(self, db: Optional[DynamoDB] = None):
        self.db = db or DynamoDB()
        self.table_name = os.environ.get("APP_TABLE_NAME", "products-table")

    # CRUDL methods will go here
```

-   **Initialization**: The constructor accepts an optional `DynamoDB` instance, which is useful for dependency injection during testing. If one isn't provided, it creates a new instance.
-   **Table Name**: The service gets the table name from an environment variable, providing a sensible default.

## 3. Implementing CRUDL Operations

Here’s how to implement the standard CRUDL operations in your service.

### Create

The `create` method uses the `db.save()` method to persist a new item to the database. It takes a model instance, converts it to a dictionary, and saves it.

```python
def create_product(self, product_data: dict) -> Product:
    """Creates a new product."""
    product = Product().map(product_data)
    
    # The to_resource_dictionary() method includes the pk, sk, and any GSI keys
    item_to_save = product.to_resource_dictionary()
    
    self.db.save(item=item_to_save, table_name=self.table_name)
    
    return product
```

### Read (Get by ID)

The `get` method retrieves a single item by its primary key. You create a model instance, set its ID, and pass it to the `db.get()` method.

```python
def get_product_by_id(self, product_id: str) -> Optional[Product]:
    """Retrieves a product by its ID."""
    # Create a model with the ID to identify the key
    model_to_find = Product(id=product_id)
    
    response = self.db.get(model=model_to_find, table_name=self.table_name)
    
    item = response.get("Item")
    if not item:
        return None
        
    return Product().map(item)
```

### Update

Updates are typically handled using a "get-then-save" pattern. You first retrieve the existing item, map the updates to it, and then save it back to the database. This ensures you don't accidentally overwrite data.

```python
def update_product(self, product_id: str, updates: dict) -> Optional[Product]:
    """Updates an existing product."""
    # 1. Get the existing product
    existing_product = self.get_product_by_id(product_id)
    if not existing_product:
        return None
        
    # 2. Map the updates to the model
    existing_product.map(updates)
    
    # 3. Save it back to the database
    item_to_save = existing_product.to_resource_dictionary()
    self.db.save(item=item_to_save, table_name=self.table_name)
    
    return existing_product
```

### Delete

The `delete` method removes an item from the database using its primary key. Similar to the `get` method, you pass a model instance with the ID set.

```python
def delete_product(self, product_id: str) -> bool:
    """Deletes a product by its ID."""
    product_to_delete = Product(id=product_id)
    
    try:
        self.db.delete(model=product_to_delete, table_name=self.table_name)
        return True
    except Exception as e:
        # Log the error
        print(f"Error deleting product {product_id}: {e}")
        return False
```

### List (Query)

To list items, you typically query a Global Secondary Index (GSI). The `db.query()` method is used for this. You need to provide the index name and a `KeyConditionExpression`.

Here’s how to list all products, sorted by name, using the `gsi0` we defined in the model documentation:

```python
from boto3.dynamodb.conditions import Key

def list_all_products(self):
    """Lists all products, sorted by name."""
    # This key queries for all items where the GSI partition key is 'products'.
    # This is based on the GSI we defined in the Product model.
    key_condition = Key('gsi0_pk').eq(Product().get_key('gsi0').partition_key.value())

    response = self.db.query(
        key=key_condition,
        index_name="gsi0",
        table_name=self.table_name,
        ascending=True
    )
    
    items = response.get("Items", [])
    return [Product().map(item) for item in items]
```

## 4. Best Practices

-   **Dependency Injection**: Always allow the `DynamoDB` instance to be injected into your service's constructor. This is critical for testing.
-   **Environment Variables**: Load sensitive information like table names from environment variables, not hardcoded strings.
-   **Use Models**: Leverage your `DynamoDBModelBase` models for all data interactions. This ensures your keys are generated correctly and your data is properly serialized.
-   **Separation of Concerns**: Keep business logic inside the service. API handlers should only be responsible for parsing requests and formatting responses.
