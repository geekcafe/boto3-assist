"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Example demonstrating conditional writes and optimistic locking with boto3-assist.

This example shows:
- Preventing duplicate records
- Optimistic locking with version numbers
- Conditional updates based on attribute values
- Complex conditional logic
"""

from boto3_assist.dynamodb.dynamodb import DynamoDB


def example_prevent_duplicates():
    """Example: Prevent creating duplicate records"""
    db = DynamoDB()
    table_name = "app-table"

    user = {
        "pk": "user#unique-001",
        "sk": "user#unique-001",
        "id": "unique-001",
        "email": "user@example.com",
        "status": "active",
    }

    try:
        # First save succeeds
        db.save(item=user, table_name=table_name, fail_if_exists=True)
        print("✅ User created successfully")

        # Second save fails
        db.save(item=user, table_name=table_name, fail_if_exists=True)
        print("This won't print")

    except RuntimeError as e:
        print(f"❌ Duplicate prevented: {e}")


def example_optimistic_locking():
    """Example: Optimistic locking with version numbers"""
    db = DynamoDB()
    table_name = "app-table"

    doc_id = "doc-001"

    # Create document with initial version
    doc = {
        "pk": f"document#{doc_id}",
        "sk": f"document#{doc_id}",
        "id": doc_id,
        "title": "My Document",
        "content": "Initial content",
        "version": 1,
    }
    db.save(item=doc, table_name=table_name)
    print(f"✅ Document created with version {doc['version']}")

    # Read current version
    response = db.get(
        key={"pk": f"document#{doc_id}", "sk": f"document#{doc_id}"}, table_name=table_name
    )
    current_version = response["Item"]["version"]

    # Update with version check
    updated_doc = {
        "pk": f"document#{doc_id}",
        "sk": f"document#{doc_id}",
        "id": doc_id,
        "title": "My Document",
        "content": "Updated content",
        "version": current_version + 1,
    }

    try:
        db.save(
            item=updated_doc,
            table_name=table_name,
            condition_expression="#version = :expected_version",
            expression_attribute_names={"#version": "version"},
            expression_attribute_values={":expected_version": current_version},
        )
        print(f"✅ Document updated to version {updated_doc['version']}")
    except RuntimeError as e:
        print(f"❌ Version conflict: {e}")
        print("Document was modified by someone else - refresh and retry")


def example_concurrent_update_detection():
    """Example: Detect concurrent modifications"""
    db = DynamoDB()
    table_name = "app-table"

    doc_id = "doc-002"

    # Create document
    doc = {
        "pk": f"document#{doc_id}",
        "sk": f"document#{doc_id}",
        "id": doc_id,
        "content": "Original content",
        "version": 1,
    }
    db.save(item=doc, table_name=table_name)

    # Simulate two users reading the same document
    user_a_response = db.get(
        key={"pk": f"document#{doc_id}", "sk": f"document#{doc_id}"}, table_name=table_name
    )
    user_a_version = user_a_response["Item"]["version"]

    user_b_response = db.get(
        key={"pk": f"document#{doc_id}", "sk": f"document#{doc_id}"}, table_name=table_name
    )
    user_b_version = user_b_response["Item"]["version"]

    # User A updates first (succeeds)
    user_a_doc = {
        "pk": f"document#{doc_id}",
        "sk": f"document#{doc_id}",
        "id": doc_id,
        "content": "Updated by User A",
        "version": user_a_version + 1,
    }

    db.save(
        item=user_a_doc,
        table_name=table_name,
        condition_expression="#version = :expected_version",
        expression_attribute_names={"#version": "version"},
        expression_attribute_values={":expected_version": user_a_version},
    )
    print("✅ User A's update succeeded")

    # User B tries to update (fails due to version conflict)
    user_b_doc = {
        "pk": f"document#{doc_id}",
        "sk": f"document#{doc_id}",
        "id": doc_id,
        "content": "Updated by User B",
        "version": user_b_version + 1,
    }

    try:
        db.save(
            item=user_b_doc,
            table_name=table_name,
            condition_expression="#version = :expected_version",
            expression_attribute_names={"#version": "version"},
            expression_attribute_values={":expected_version": user_b_version},
        )
        print("This won't print")
    except RuntimeError:
        print("❌ User B's update failed - version conflict detected")
        print("→ User B should refresh and retry with latest version")


def example_conditional_update_status():
    """Example: Only update if status matches"""
    db = DynamoDB()
    table_name = "app-table"

    order = {
        "pk": "order#order-001",
        "sk": "order#order-001",
        "id": "order-001",
        "status": "pending",
        "total": 100.00,
    }
    db.save(item=order, table_name=table_name)

    # Ship order only if status is "pending"
    shipped_order = {
        "pk": "order#order-001",
        "sk": "order#order-001",
        "id": "order-001",
        "status": "shipped",
        "total": 100.00,
    }

    try:
        db.save(
            item=shipped_order,
            table_name=table_name,
            condition_expression="#status = :pending",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":pending": "pending"},
        )
        print("✅ Order shipped successfully")
    except RuntimeError:
        print("❌ Order cannot be shipped - status is not 'pending'")


def example_conditional_update_with_comparison():
    """Example: Update only if value meets criteria"""
    db = DynamoDB()
    table_name = "app-table"

    account = {"pk": "account#acc-001", "sk": "account#acc-001", "id": "acc-001", "balance": 500.00}
    db.save(item=account, table_name=table_name)

    # Withdraw only if balance is sufficient
    withdrawal_amount = 200.00

    updated_account = {
        "pk": "account#acc-001",
        "sk": "account#acc-001",
        "id": "acc-001",
        "balance": 300.00,  # 500 - 200
    }

    try:
        db.save(
            item=updated_account,
            table_name=table_name,
            condition_expression="balance >= :amount",
            expression_attribute_values={":amount": withdrawal_amount},
        )
        print(f"✅ Withdrawal of ${withdrawal_amount} successful")
    except RuntimeError:
        print(f"❌ Insufficient funds for ${withdrawal_amount} withdrawal")


def example_update_only_if_exists():
    """Example: Update only existing items"""
    db = DynamoDB()
    table_name = "app-table"

    user = {"pk": "user#user-999", "sk": "user#user-999", "id": "user-999", "name": "Updated Name"}

    try:
        # This will fail if user doesn't exist
        db.save(item=user, table_name=table_name, condition_expression="attribute_exists(pk)")
        print("✅ User updated")
    except RuntimeError:
        print("❌ User doesn't exist - cannot update")


def example_complex_conditions():
    """Example: Complex conditional logic (AND/OR)"""
    db = DynamoDB()
    table_name = "app-table"

    item = {
        "pk": "item#item-001",
        "sk": "item#item-001",
        "id": "item-001",
        "status": "active",
        "stock": 10,
        "price": 29.99,
    }
    db.save(item=item, table_name=table_name)

    # Update only if: status=active AND stock > 0 AND price < 50
    updated_item = {
        "pk": "item#item-001",
        "sk": "item#item-001",
        "id": "item-001",
        "status": "active",
        "stock": 9,  # Decremented
        "price": 29.99,
    }

    try:
        db.save(
            item=updated_item,
            table_name=table_name,
            condition_expression=(
                "#status = :active AND " "stock > :min_stock AND " "price < :max_price"
            ),
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":active": "active", ":min_stock": 0, ":max_price": 50.00},
        )
        print("✅ Item updated - all conditions met")
    except RuntimeError:
        print("❌ Item update failed - conditions not met")


def example_retry_on_version_conflict():
    """Example: Retry pattern for version conflicts"""
    db = DynamoDB()
    table_name = "app-table"

    doc_id = "doc-003"
    max_retries = 3

    # Create document
    doc = {
        "pk": f"document#{doc_id}",
        "sk": f"document#{doc_id}",
        "id": doc_id,
        "content": "Initial",
        "version": 1,
    }
    db.save(item=doc, table_name=table_name)

    # Retry loop for optimistic locking
    for attempt in range(max_retries):
        try:
            # Read current version
            response = db.get(
                key={"pk": f"document#{doc_id}", "sk": f"document#{doc_id}"}, table_name=table_name
            )
            current_version = response["Item"]["version"]

            # Prepare update
            updated_doc = {
                "pk": f"document#{doc_id}",
                "sk": f"document#{doc_id}",
                "id": doc_id,
                "content": "Updated content",
                "version": current_version + 1,
            }

            # Attempt update with version check
            db.save(
                item=updated_doc,
                table_name=table_name,
                condition_expression="#version = :expected_version",
                expression_attribute_names={"#version": "version"},
                expression_attribute_values={":expected_version": current_version},
            )

            print(f"✅ Update succeeded on attempt {attempt + 1}")
            break

        except RuntimeError:
            if attempt < max_retries - 1:
                print(f"⚠️ Version conflict on attempt {attempt + 1}, retrying...")
            else:
                print(f"❌ Update failed after {max_retries} attempts")


if __name__ == "__main__":
    print("=" * 60)
    print("Conditional Writes & Optimistic Locking Examples")
    print("=" * 60)

    # Note: These examples assume the table exists
    # Uncomment the examples you want to run

    # example_prevent_duplicates()
    # example_optimistic_locking()
    # example_concurrent_update_detection()
    # example_conditional_update_status()
    # example_conditional_update_with_comparison()
    # example_update_only_if_exists()
    # example_complex_conditions()
    # example_retry_on_version_conflict()

    print("\n✅ Examples complete!")
