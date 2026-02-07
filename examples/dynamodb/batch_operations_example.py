"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Example demonstrating batch operations with boto3-assist.

This example shows:
- batch_get_item: Retrieve multiple items efficiently
- batch_write_item: Create or delete multiple items in bulk
- Real-world use cases
"""

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.models.product_model import Product
from examples.dynamodb.models.user_model import User


def example_batch_get():
    """Example: Batch get multiple users"""
    db = DynamoDB()
    table_name = "app-table"

    # Get multiple users by their IDs
    user_ids = ["user-001", "user-002", "user-003", "user-004", "user-005"]

    # Build keys for batch get
    keys = [{"pk": f"user#{user_id}", "sk": f"user#{user_id}"} for user_id in user_ids]

    # Batch get all users in a single request
    print(f"Fetching {len(keys)} users with batch_get_item...")
    response = db.batch_get_item(keys=keys, table_name=table_name)

    print(f"Retrieved {response['Count']} users")

    # Map to User models
    users = [User().map(item) for item in response["Items"]]

    for user in users:
        print(f"  - {user.first_name} {user.last_name} ({user.email})")

    # Check for unprocessed keys
    if response["UnprocessedKeys"]:
        print(f"Warning: {len(response['UnprocessedKeys'])} keys were unprocessed")

    return users


def example_batch_get_with_projection():
    """Example: Batch get with projection to reduce data transfer"""
    db = DynamoDB()
    table_name = "app-table"

    user_ids = ["user-001", "user-002", "user-003"]
    keys = [{"pk": f"user#{user_id}", "sk": f"user#{user_id}"} for user_id in user_ids]

    # Use projection to get only specific fields
    print("Fetching users with projection (id, name, email only)...")
    response = db.batch_get_item(
        keys=keys,
        table_name=table_name,
        projection_expression="id,first_name,last_name,email",
    )

    print(f"Retrieved {response['Count']} users with reduced payload")

    for item in response["Items"]:
        print(f"  - {item.get('first_name')} {item.get('last_name')}")
        # Note: pk, sk, and other fields won't be present

    return response["Items"]


def example_batch_write_create():
    """Example: Batch create multiple users"""
    db = DynamoDB()
    table_name = "app-table"

    # Create multiple users at once
    users = []
    for i in range(10):
        user = User(id=f"batch-user-{i:03d}")
        user.first_name = f"BatchUser{i}"
        user.last_name = "Test"
        user.email = f"batchuser{i}@example.com"
        user.status = "active"
        users.append(user)

    # Convert to dictionaries
    items = [user.to_resource_dictionary() for user in users]

    # Batch write all users
    print(f"Creating {len(items)} users with batch_write_item...")
    response = db.batch_write_item(items=items, table_name=table_name, operation="put")

    print(f"Successfully processed {response['ProcessedCount']} users")
    print(f"Unprocessed: {response['UnprocessedCount']}")

    return response


def example_batch_write_delete():
    """Example: Batch delete multiple users"""
    db = DynamoDB()
    table_name = "app-table"

    # Delete users created in previous example
    user_ids = [f"batch-user-{i:03d}" for i in range(10)]

    # Build keys for deletion
    keys = [{"pk": f"user#{user_id}", "sk": f"user#{user_id}"} for user_id in user_ids]

    # Batch delete
    print(f"Deleting {len(keys)} users with batch_write_item...")
    response = db.batch_write_item(items=keys, table_name=table_name, operation="delete")

    print(f"Successfully deleted {response['ProcessedCount']} users")

    return response


def example_bulk_data_migration():
    """Example: Migrate data in bulk"""
    db = DynamoDB()
    table_name = "app-table"

    # Simulate reading from a CSV or API
    external_data = [
        {"id": "001", "name": "Product A", "price": 10.99},
        {"id": "002", "name": "Product B", "price": 20.99},
        {"id": "003", "name": "Product C", "price": 30.99},
        # ... potentially hundreds more
    ]

    print(f"Migrating {len(external_data)} products...")

    # Convert to DynamoDB items
    items = []
    for data in external_data:
        product = Product(id=data["id"], name=data["name"], price=data["price"])
        items.append(product.to_resource_dictionary())

    # Batch write (automatically chunks if > 25 items)
    response = db.batch_write_item(items=items, table_name=table_name, operation="put")

    print(f"Migration complete: {response['ProcessedCount']} products created")

    if response["UnprocessedCount"] > 0:
        print(f"Warning: {response['UnprocessedCount']} items failed to process")
        # Handle unprocessed items (could retry manually)

    return response


def example_batch_operations_comparison():
    """Compare individual operations vs batch operations"""
    import time

    db = DynamoDB()
    table_name = "app-table"

    # Create test data
    user_ids = [f"perf-test-{i:03d}" for i in range(50)]

    # Method 1: Individual get operations
    print("\n=== Method 1: Individual GET operations ===")
    start = time.time()

    users_individual = []
    for user_id in user_ids:
        response = db.get(
            key={"pk": f"user#{user_id}", "sk": f"user#{user_id}"}, table_name=table_name
        )
        if "Item" in response:
            users_individual.append(response["Item"])

    individual_time = time.time() - start
    print(f"Retrieved {len(users_individual)} users in {individual_time:.3f}s")
    print(f"Average: {individual_time / len(user_ids):.4f}s per item")

    # Method 2: Batch get operation
    print("\n=== Method 2: Batch GET operation ===")
    start = time.time()

    keys = [{"pk": f"user#{user_id}", "sk": f"user#{user_id}"} for user_id in user_ids]

    response = db.batch_get_item(keys=keys, table_name=table_name)
    users_batch = response["Items"]

    batch_time = time.time() - start
    print(f"Retrieved {len(users_batch)} users in {batch_time:.3f}s")
    print(f"Average: {batch_time / len(user_ids):.4f}s per item")

    # Comparison
    print(f"\n=== Performance Improvement ===")
    speedup = individual_time / batch_time
    print(f"Batch operations are {speedup:.1f}x faster!")
    print(f"Time saved: {individual_time - batch_time:.3f}s")


def example_error_handling():
    """Example: Handle errors in batch operations"""
    db = DynamoDB()
    table_name = "app-table"

    # Try to get items from non-existent keys
    keys = [
        {"pk": "nonexistent#1", "sk": "nonexistent#1"},
        {"pk": "nonexistent#2", "sk": "nonexistent#2"},
    ]

    try:
        response = db.batch_get_item(keys=keys, table_name=table_name)

        print(f"Retrieved {response['Count']} items")

        # Check for unprocessed keys (throttling, etc.)
        if response["UnprocessedKeys"]:
            print(f"Unprocessed keys: {len(response['UnprocessedKeys'])}")
            print("These keys should be retried manually if needed")

        # Note: Non-existent keys simply return no items (not an error)
        if response["Count"] == 0:
            print("No items found for the provided keys")

    except Exception as e:
        print(f"Error during batch operation: {e}")
        # Handle error (log, retry, alert, etc.)


if __name__ == "__main__":
    print("=" * 60)
    print("Batch Operations Examples")
    print("=" * 60)

    # Note: These examples assume the table and data exist
    # Uncomment the examples you want to run

    # example_batch_get()
    # example_batch_get_with_projection()
    # example_batch_write_create()
    # example_batch_write_delete()
    # example_bulk_data_migration()
    # example_batch_operations_comparison()
    # example_error_handling()

    print("\n✅ Examples complete!")
