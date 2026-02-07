"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Example demonstrating update expressions with boto3-assist.

This example shows:
- SET: Setting and updating attributes
- ADD: Atomic counters and sets
- REMOVE: Deleting attributes
- DELETE: Removing items from sets
- Combining operations
- Conditional updates
"""

from boto3_assist.dynamodb.dynamodb import DynamoDB


def example_set_operation():
    """Example: SET operation for updating attributes"""
    db = DynamoDB()
    table_name = "app-table"

    # Update single attribute
    db.update_item(
        table_name=table_name,
        key={"pk": "user#001", "sk": "user#001"},
        update_expression="SET email = :email",
        expression_attribute_values={":email": "newemail@example.com"},
    )
    print("✅ Updated email")

    # Update multiple attributes
    db.update_item(
        table_name=table_name,
        key={"pk": "user#001", "sk": "user#001"},
        update_expression="SET email = :email, phone = :phone, city = :city",
        expression_attribute_values={
            ":email": "user@example.com",
            ":phone": "555-1234",
            ":city": "San Francisco",
        },
    )
    print("✅ Updated multiple attributes")


def example_set_with_reserved_words():
    """Example: SET operation with reserved keywords"""
    db = DynamoDB()
    table_name = "app-table"

    # Update attributes that are reserved words
    db.update_item(
        table_name=table_name,
        key={"pk": "order#001", "sk": "order#001"},
        update_expression="SET #status = :status, #comment = :comment",
        expression_attribute_names={
            "#status": "status",  # 'status' is reserved
            "#comment": "comment",  # 'comment' is reserved
        },
        expression_attribute_values={":status": "shipped", ":comment": "Express shipping"},
    )
    print("✅ Updated reserved keywords")


def example_set_with_math():
    """Example: SET operation with mathematical expressions"""
    db = DynamoDB()
    table_name = "app-table"

    # Increment/decrement numbers
    db.update_item(
        table_name=table_name,
        key={"pk": "counter#001", "sk": "counter#001"},
        update_expression="SET count = count + :inc, price = price - :discount",
        expression_attribute_values={":inc": 5, ":discount": 10.50},
    )
    print("✅ Applied math operations")


def example_atomic_counter():
    """Example: ADD operation for atomic counters"""
    db = DynamoDB()
    table_name = "app-table"

    # Increment view count atomically (race-condition safe!)
    db.update_item(
        table_name=table_name,
        key={"pk": "post#post-123", "sk": "post#post-123"},
        update_expression="ADD views :inc",
        expression_attribute_values={":inc": 1},
    )
    print("✅ Incremented view count")

    # Can also decrement
    db.update_item(
        table_name=table_name,
        key={"pk": "post#post-123", "sk": "post#post-123"},
        update_expression="ADD views :dec",
        expression_attribute_values={":dec": -1},
    )
    print("✅ Decremented view count")


def example_atomic_counters_multiple():
    """Example: Multiple atomic counters"""
    db = DynamoDB()
    table_name = "app-table"

    # Track multiple metrics atomically
    db.update_item(
        table_name=table_name,
        key={"pk": "analytics#daily", "sk": "2024-10-15"},
        update_expression="ADD page_views :pv, unique_visitors :uv, clicks :clicks",
        expression_attribute_values={":pv": 1, ":uv": 1, ":clicks": 3},
    )
    print("✅ Updated multiple counters")


def example_add_to_set():
    """Example: ADD operation for adding to sets"""
    db = DynamoDB()
    table_name = "app-table"

    # Add tags to a user (set automatically prevents duplicates)
    db.update_item(
        table_name=table_name,
        key={"pk": "user#user-001", "sk": "user#user-001"},
        update_expression="ADD tags :new_tags",
        expression_attribute_values={":new_tags": {"premium", "verified", "admin"}},
    )
    print("✅ Added tags to set")


def example_remove_attribute():
    """Example: REMOVE operation to delete attributes"""
    db = DynamoDB()
    table_name = "app-table"

    # Remove single attribute
    db.update_item(
        table_name=table_name,
        key={"pk": "user#001", "sk": "user#001"},
        update_expression="REMOVE temp_field",
    )
    print("✅ Removed attribute")

    # Remove multiple attributes
    db.update_item(
        table_name=table_name,
        key={"pk": "user#001", "sk": "user#001"},
        update_expression="REMOVE temp1, temp2, temp3",
    )
    print("✅ Removed multiple attributes")


def example_complex_update():
    """Example: Combining SET, ADD, and REMOVE"""
    db = DynamoDB()
    table_name = "app-table"

    # Update multiple aspects of a blog post
    db.update_item(
        table_name=table_name,
        key={"pk": "post#post-456", "sk": "post#post-456"},
        update_expression=(
            "SET #status = :status, updated_at = :now, author_note = :note "
            "ADD views :inc, likes :like_inc "
            "REMOVE draft_field, temp_data"
        ),
        expression_attribute_names={"#status": "status"},
        expression_attribute_values={
            ":status": "published",
            ":now": "2024-10-15T20:00:00Z",
            ":note": "Updated content",
            ":inc": 1,
            ":like_inc": 5,
        },
    )
    print("✅ Performed complex update")


def example_conditional_update():
    """Example: Update only if condition is met"""
    db = DynamoDB()
    table_name = "app-table"

    try:
        # Ship order only if status is 'pending'
        db.update_item(
            table_name=table_name,
            key={"pk": "order#order-789", "sk": "order#order-789"},
            update_expression="SET #status = :shipped, shipped_at = :now",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={
                ":shipped": "shipped",
                ":now": "2024-10-15T20:00:00Z",
                ":pending": "pending",
            },
            condition_expression="#status = :pending",
        )
        print("✅ Order shipped")
    except RuntimeError:
        print("❌ Order cannot be shipped - status is not 'pending'")


def example_inventory_decrement():
    """Example: Decrement inventory with stock check"""
    db = DynamoDB()
    table_name = "app-table"

    quantity_to_reserve = 5

    try:
        # Decrement stock only if sufficient quantity available
        response = db.update_item(
            table_name=table_name,
            key={"pk": "product#prod-001", "sk": "product#prod-001"},
            update_expression="SET stock = stock - :qty",
            expression_attribute_values={":qty": quantity_to_reserve},
            condition_expression="stock >= :qty",
            return_values="ALL_NEW",
        )

        remaining_stock = response["Attributes"]["stock"]
        print(f"✅ Reserved {quantity_to_reserve} units. {remaining_stock} remaining")

    except RuntimeError:
        print(f"❌ Insufficient stock to reserve {quantity_to_reserve} units")


def example_return_values():
    """Example: Using return_values to get updated item"""
    db = DynamoDB()
    table_name = "app-table"

    # Get updated values after update
    response = db.update_item(
        table_name=table_name,
        key={"pk": "user#user-999", "sk": "user#user-999"},
        update_expression="SET last_login = :now ADD login_count :inc",
        expression_attribute_values={":now": "2024-10-15T20:00:00Z", ":inc": 1},
        return_values="ALL_NEW",
    )

    # Access updated item directly
    updated_user = response["Attributes"]
    print(f"✅ User logged in. Total logins: {updated_user['login_count']}")


def example_list_operations():
    """Example: Working with list attributes"""
    db = DynamoDB()
    table_name = "app-table"

    # Append to list
    db.update_item(
        table_name=table_name,
        key={"pk": "doc#doc-001", "sk": "doc#doc-001"},
        update_expression="SET #history = list_append(#history, :new_entry)",
        expression_attribute_names={"#history": "history"},
        expression_attribute_values={
            ":new_entry": [
                {"action": "updated", "timestamp": "2024-10-15T20:00:00Z", "user": "user-123"}
            ]
        },
    )
    print("✅ Appended to list")

    # Prepend to list
    db.update_item(
        table_name=table_name,
        key={"pk": "doc#doc-001", "sk": "doc#doc-001"},
        update_expression="SET #history = list_append(:new_entry, #history)",
        expression_attribute_names={"#history": "history"},
        expression_attribute_values={
            ":new_entry": [{"action": "created", "timestamp": "2024-10-14T10:00:00Z"}]
        },
    )
    print("✅ Prepended to list")


def example_nested_attribute_update():
    """Example: Updating nested attributes"""
    db = DynamoDB()
    table_name = "app-table"

    # Update nested map attribute
    db.update_item(
        table_name=table_name,
        key={"pk": "user#user-001", "sk": "user#user-001"},
        update_expression="SET settings.notifications = :enabled, settings.theme = :theme",
        expression_attribute_values={":enabled": True, ":theme": "dark"},
    )
    print("✅ Updated nested attributes")


def example_if_not_exists():
    """Example: SET if attribute doesn't exist"""
    db = DynamoDB()
    table_name = "app-table"

    # Set default value only if attribute doesn't exist
    db.update_item(
        table_name=table_name,
        key={"pk": "user#user-002", "sk": "user#user-002"},
        update_expression="SET login_count = if_not_exists(login_count, :default)",
        expression_attribute_values={":default": 0},
    )
    print("✅ Set default value if not exists")


def example_increment_version():
    """Example: Increment version for optimistic locking"""
    db = DynamoDB()
    table_name = "app-table"

    # Update with version increment
    try:
        response = db.update_item(
            table_name=table_name,
            key={"pk": "doc#doc-999", "sk": "doc#doc-999"},
            update_expression="SET content = :content, version = version + :inc",
            expression_attribute_values={
                ":content": "Updated content",
                ":inc": 1,
                ":expected_version": 5,
            },
            condition_expression="version = :expected_version",
            return_values="ALL_NEW",
        )

        new_version = response["Attributes"]["version"]
        print(f"✅ Document updated to version {new_version}")

    except RuntimeError:
        print("❌ Version conflict - document was modified by another user")


if __name__ == "__main__":
    print("=" * 60)
    print("Update Expressions Examples")
    print("=" * 60)

    # Note: These examples assume the table and items exist
    # Uncomment the examples you want to run

    # example_set_operation()
    # example_set_with_reserved_words()
    # example_set_with_math()
    # example_atomic_counter()
    # example_atomic_counters_multiple()
    # example_add_to_set()
    # example_remove_attribute()
    # example_complex_update()
    # example_conditional_update()
    # example_inventory_decrement()
    # example_return_values()
    # example_list_operations()
    # example_nested_attribute_update()
    # example_if_not_exists()
    # example_increment_version()

    print("\n✅ Examples complete!")
