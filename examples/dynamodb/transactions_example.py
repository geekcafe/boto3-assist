"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Example demonstrating transaction operations with boto3-assist.

This example shows:
- transact_write_items: Atomic multi-item writes
- transact_get_items: Consistent multi-item reads
- Real-world use cases (money transfers, inventory, etc.)
"""

from boto3_assist.dynamodb.dynamodb import DynamoDB


def example_money_transfer():
    """Example: Transfer money between accounts atomically"""
    db = DynamoDB()
    table_name = "app-table"

    # Transfer $100 from account A to account B
    # Both operations must succeed or both fail
    operations = [
        {
            "Update": {
                "TableName": table_name,
                "Key": {"pk": "account#A", "sk": "account#A"},
                "UpdateExpression": "SET balance = balance - :amount",
                "ConditionExpression": "balance >= :amount",  # Don't overdraft!
                "ExpressionAttributeValues": {":amount": 100},
            }
        },
        {
            "Update": {
                "TableName": table_name,
                "Key": {"pk": "account#B", "sk": "account#B"},
                "UpdateExpression": "SET balance = balance + :amount",
                "ExpressionAttributeValues": {":amount": 100},
            }
        },
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "pk": "transaction#tx-001",
                    "sk": "transaction#tx-001",
                    "from_account": "A",
                    "to_account": "B",
                    "amount": 100,
                    "timestamp": "2024-10-15T20:00:00Z",
                },
            }
        },
    ]

    try:
        response = db.transact_write_items(operations=operations)
        print("✅ Transfer successful!")
        print(f"Transaction ID: tx-001")
        return True
    except Exception as e:
        print(f"❌ Transfer failed: {e}")
        print("All operations rolled back - accounts unchanged")
        return False


def example_inventory_reservation():
    """Example: Reserve inventory items atomically"""
    db = DynamoDB()
    table_name = "app-table"

    # Reserve multiple items for an order
    # All items must be available or order fails
    order_id = "order-12345"
    items_to_reserve = [
        ("product-001", 2),  # Product ID, Quantity
        ("product-002", 1),
        ("product-003", 5),
    ]

    operations = []

    # Decrement inventory for each product
    for product_id, quantity in items_to_reserve:
        operations.append(
            {
                "Update": {
                    "TableName": table_name,
                    "Key": {"pk": f"product#{product_id}", "sk": f"product#{product_id}"},
                    "UpdateExpression": "SET inventory = inventory - :qty",
                    "ConditionExpression": "inventory >= :qty",  # Must have stock!
                    "ExpressionAttributeValues": {":qty": quantity},
                }
            }
        )

    # Create order record
    operations.append(
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "pk": f"order#{order_id}",
                    "sk": f"order#{order_id}",
                    "status": "reserved",
                    "items": [
                        {"product_id": pid, "quantity": qty} for pid, qty in items_to_reserve
                    ],
                },
            }
        }
    )

    try:
        response = db.transact_write_items(operations=operations)
        print(f"✅ Order {order_id} reserved successfully")
        return True
    except Exception as e:
        print(f"❌ Reservation failed: {e}")
        print("Insufficient inventory - order not created")
        return False


def example_user_registration():
    """Example: Create user with validation checks"""
    db = DynamoDB()
    table_name = "app-table"

    user_id = "user-42"
    email = "user42@example.com"

    operations = [
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "pk": f"user#{user_id}",
                    "sk": f"user#{user_id}",
                    "id": user_id,
                    "email": email,
                    "status": "active",
                },
                "ConditionExpression": "attribute_not_exists(pk)",  # User must not exist
            }
        },
        {
            "Put": {
                "TableName": table_name,
                "Item": {"pk": "emails#", "sk": f"email#{email}", "user_id": user_id},
                "ConditionExpression": "attribute_not_exists(sk)",  # Email must be unique
            }
        },
    ]

    try:
        response = db.transact_write_items(operations=operations)
        print(f"✅ User {user_id} registered successfully")
        return True
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        print("User ID or email already exists")
        return False


def example_shopping_cart_checkout():
    """Example: Process cart checkout with inventory checks"""
    db = DynamoDB()
    table_name = "app-table"

    cart_items = [
        {"product_id": "prod-100", "quantity": 2, "price": 29.99},
        {"product_id": "prod-200", "quantity": 1, "price": 49.99},
    ]

    operations = []
    total = 0

    # Update inventory for each item
    for item in cart_items:
        operations.append(
            {
                "Update": {
                    "TableName": table_name,
                    "Key": {
                        "pk": f'product#{item["product_id"]}',
                        "sk": f'product#{item["product_id"]}',
                    },
                    "UpdateExpression": "SET stock = stock - :qty",
                    "ConditionExpression": "stock >= :qty AND #status = :available",
                    "ExpressionAttributeNames": {"#status": "status"},
                    "ExpressionAttributeValues": {
                        ":qty": item["quantity"],
                        ":available": "available",
                    },
                }
            }
        )
        total += item["price"] * item["quantity"]

    # Create order
    operations.append(
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "pk": "order#new-order",
                    "sk": "order#new-order",
                    "items": cart_items,
                    "total": total,
                    "status": "confirmed",
                },
            }
        }
    )

    try:
        response = db.transact_write_items(operations=operations)
        print(f"✅ Checkout successful! Total: ${total:.2f}")
        return True
    except Exception as e:
        print(f"❌ Checkout failed: {e}")
        return False


def example_consistent_snapshot_read():
    """Example: Read multiple related items with consistency"""
    db = DynamoDB()
    table_name = "app-table"

    # Get user and all their accounts in a consistent snapshot
    keys = [
        {"Key": {"pk": "user#user-123", "sk": "user#user-123"}, "TableName": table_name},
        {"Key": {"pk": "account#checking", "sk": "user#user-123"}, "TableName": table_name},
        {"Key": {"pk": "account#savings", "sk": "user#user-123"}, "TableName": table_name},
    ]

    response = db.transact_get_items(keys=keys)

    print(f"Retrieved {response['Count']} items")
    print("Consistent snapshot across all items:")

    for item in response["Items"]:
        if "user#" in item["pk"]:
            print(f"  User: {item.get('name')}")
        elif "account#" in item["pk"]:
            print(f"  Account: {item.get('type')} - Balance: ${item.get('balance')}")

    return response["Items"]


def example_optimistic_locking():
    """Example: Optimistic locking with version numbers"""
    db = DynamoDB()
    table_name = "app-table"

    document_id = "doc-001"

    # First, read current document with version
    response = db.get(
        key={"pk": f"document#{document_id}", "sk": f"document#{document_id}"},
        table_name=table_name,
    )

    if "Item" not in response:
        print("Document not found")
        return False

    current_version = response["Item"].get("version", 0)

    # Update with version check (optimistic lock)
    operations = [
        {
            "Update": {
                "TableName": table_name,
                "Key": {"pk": f"document#{document_id}", "sk": f"document#{document_id}"},
                "UpdateExpression": "SET content = :new_content, version = :new_version",
                "ConditionExpression": "version = :expected_version",
                "ExpressionAttributeValues": {
                    ":new_content": "Updated content",
                    ":new_version": current_version + 1,
                    ":expected_version": current_version,
                },
            }
        }
    ]

    try:
        response = db.transact_write_items(operations=operations)
        print(f"✅ Document updated (version {current_version} → {current_version + 1})")
        return True
    except Exception as e:
        print(f"❌ Update failed: {e}")
        print("Document was modified by another process - version conflict")
        return False


def example_audit_trail():
    """Example: Create item with audit trail atomically"""
    db = DynamoDB()
    table_name = "app-table"

    import datetime

    timestamp = datetime.datetime.utcnow().isoformat()

    operations = [
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "pk": "record#rec-001",
                    "sk": "record#rec-001",
                    "data": "Important data",
                    "created_at": timestamp,
                },
            }
        },
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "pk": "audit#rec-001",
                    "sk": f"audit#{timestamp}",
                    "action": "CREATE",
                    "record_id": "rec-001",
                    "timestamp": timestamp,
                    "user": "system",
                },
            }
        },
    ]

    try:
        response = db.transact_write_items(operations=operations)
        print("✅ Record created with audit trail")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def example_compare_batch_vs_transaction():
    """Compare batch operations vs transactions"""
    db = DynamoDB()
    table_name = "app-table"

    print("\n=== Batch Operations (No Atomicity) ===")
    print("✓ Fast (single API call)")
    print("✓ No conditional logic")
    print("✗ No atomicity - can partially fail")
    print("✗ No conditional expressions")
    print("Use case: Bulk data import where failures are acceptable")

    print("\n=== Transactions (Atomic) ===")
    print("✓ All-or-nothing guarantee")
    print("✓ Conditional expressions supported")
    print("✓ Data consistency guaranteed")
    print("✗ Slower than batch")
    print("✗ More expensive (2x WCUs)")
    print("Use case: Financial operations, inventory, user registration")


def example_error_handling():
    """Example: Proper error handling for transactions"""
    db = DynamoDB()
    table_name = "app-table"

    operations = [
        {
            "Update": {
                "TableName": table_name,
                "Key": {"pk": "account#test", "sk": "account#test"},
                "UpdateExpression": "SET balance = balance - :amount",
                "ConditionExpression": "balance >= :amount",
                "ExpressionAttributeValues": {":amount": 1000},
            }
        }
    ]

    try:
        response = db.transact_write_items(operations=operations)
        print("✅ Transaction successful")

    except RuntimeError as e:
        # Transaction cancelled (condition failed)
        print(f"⚠️ Transaction cancelled: {e}")
        # Could retry with different parameters

    except ValueError as e:
        # Invalid parameters
        print(f"❌ Invalid request: {e}")

    except Exception as e:
        # Other errors (throttling, service error, etc.)
        print(f"❌ Unexpected error: {e}")
        # Could implement retry logic with backoff


if __name__ == "__main__":
    print("=" * 60)
    print("Transaction Operations Examples")
    print("=" * 60)

    # Note: These examples assume the table and data exist
    # Uncomment the examples you want to run

    # example_money_transfer()
    # example_inventory_reservation()
    # example_user_registration()
    # example_shopping_cart_checkout()
    # example_consistent_snapshot_read()
    # example_optimistic_locking()
    # example_audit_trail()
    example_compare_batch_vs_transaction()
    # example_error_handling()

    print("\n✅ Examples complete!")
