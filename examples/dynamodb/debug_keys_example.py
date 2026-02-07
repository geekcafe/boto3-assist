"""
Example demonstrating how to use to_dict() for debugging DynamoDB keys

This is particularly useful when:
- Debugging key generation logic
- Logging DynamoDB operations
- Verifying composite key structure
- Testing before making actual DynamoDB calls
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class Product(DynamoDBModelBase):
    """Example product model with indexes"""

    def __init__(self):
        super().__init__()
        self.id: str = ""
        self.name: str = ""
        self.category: str = ""
        self.price: float = 0.0
        self.__setup_indexes()

    def __setup_indexes(self):
        """Setup primary and secondary indexes"""

        # Primary index
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        self.indexes.add_primary(primary)

        # GSI for category queries
        gsi1 = DynamoDBIndex(index_name="gsi1")
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(("category", self.category))
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        self.indexes.add_secondary(gsi1)


def example_basic_key_debugging():
    """Example: Debug a single key"""
    print("\n=== Example 1: Basic Key Debugging ===")

    key = DynamoDBKey(attribute_name="pk", value=lambda: "user#123")

    print(f"Key dictionary: {key.to_dict()}")
    # Output: Key dictionary: {'pk': 'user#123'}


def example_index_debugging():
    """Example: Debug primary index keys"""
    print("\n=== Example 2: Index Debugging ===")

    product = Product()
    product.id = "prod_456"
    product.name = "Widget"
    product.category = "electronics"

    # Get primary key for debugging
    primary_key = product.indexes.primary.to_dict()
    print(f"Primary key: {primary_key}")
    # Output: Primary key: {'pk': 'product#prod_456', 'sk': 'product#prod_456'}

    # Get GSI key for debugging
    gsi1_key = product.indexes.get("gsi1").to_dict()
    print(f"GSI1 key: {gsi1_key}")
    # Output: GSI1 key: {'gsi1_pk': 'category#electronics', 'gsi1_sk': 'product#prod_456'}


def example_partition_key_only():
    """Example: Get just the partition key"""
    print("\n=== Example 3: Partition Key Only ===")

    product = Product()
    product.id = "prod_789"
    product.category = "books"

    # For begins_with queries, you might only need partition key
    gsi_pk_only = product.indexes.get("gsi1").to_dict(include_sort_key=False)
    print(f"GSI partition key only: {gsi_pk_only}")
    # Output: GSI partition key only: {'gsi1_pk': 'category#books'}


def example_logging_before_save():
    """Example: Log keys before saving to DynamoDB"""
    print("\n=== Example 4: Logging Before Database Operations ===")

    product = Product()
    product.id = "prod_999"
    product.name = "Gadget"
    product.category = "gadgets"
    product.price = 29.99

    # Before saving, log the key for debugging
    key = product.indexes.primary.to_dict()
    print(f"[DEBUG] About to save product with key: {key}")
    print(f"[DEBUG] Product data: {product.to_dictionary()}")

    # Now you can see exactly what key will be used
    # db.save(item=product, table_name="products")


def example_composite_key_verification():
    """Example: Verify complex composite keys"""
    print("\n=== Example 5: Verify Composite Key Structure ===")

    tenant_id = "tenant_001"
    user_id = "user_555"

    # Create a complex multi-tenant key
    index = DynamoDBIndex()
    index.partition_key.attribute_name = "pk"
    index.partition_key.value = lambda: DynamoDBKey.build_key(
        ("tenant", tenant_id), ("user", user_id)
    )
    index.sort_key.attribute_name = "sk"
    index.sort_key.value = lambda: DynamoDBKey.build_key(("tenant", tenant_id), ("user", user_id))

    key_dict = index.to_dict()
    print(f"Multi-tenant key: {key_dict}")
    # Output: Multi-tenant key: {'pk': 'tenant#tenant_001#user#user_555',
    #                             'sk': 'tenant#tenant_001#user#user_555'}

    # Verify the structure is correct
    assert "tenant#tenant_001" in key_dict["pk"]
    assert "user#user_555" in key_dict["pk"]
    print("✓ Key structure verified!")


def example_dynamic_key_changes():
    """Example: See how keys change dynamically"""
    print("\n=== Example 6: Dynamic Key Changes ===")

    product = Product()
    product.id = "prod_100"
    product.category = "toys"

    # Check initial keys
    print(f"Initial primary key: {product.indexes.primary.to_dict()}")
    print(f"Initial GSI key: {product.indexes.get('gsi1').to_dict()}")

    # Change product ID
    product.id = "prod_200"
    product.category = "games"

    # Keys automatically reflect the changes (because they use lambdas)
    print(f"Updated primary key: {product.indexes.primary.to_dict()}")
    print(f"Updated GSI key: {product.indexes.get('gsi1').to_dict()}")
    # The keys dynamically update based on current attribute values!


def example_troubleshooting_query():
    """Example: Troubleshoot a query that isn't working"""
    print("\n=== Example 7: Troubleshooting Query Issues ===")

    # You want to query all products in the "electronics" category
    category = "electronics"

    # Create the query key
    gsi = DynamoDBIndex(index_name="gsi1")
    gsi.partition_key.attribute_name = "gsi1_pk"
    gsi.partition_key.value = lambda: DynamoDBKey.build_key(("category", category))

    # Debug: What key will be used in the query?
    query_key = gsi.to_dict(include_sort_key=False)
    print(f"[DEBUG] Querying GSI1 with key: {query_key}")
    # Output: [DEBUG] Querying GSI1 with key: {'gsi1_pk': 'category#electronics'}

    # Now you can see if the key format matches what's in DynamoDB
    # This helps identify issues like:
    # - Wrong delimiter (should be '#' not '-')
    # - Missing prefix (should be 'category#' not just 'electronics')
    # - Wrong attribute name (should be 'gsi1_pk' not 'pk')


def example_unit_testing_keys():
    """Example: Use in unit tests"""
    print("\n=== Example 8: Unit Testing Key Generation ===")

    product = Product()
    product.id = "test_001"
    product.category = "test"

    # In a unit test, you can verify key generation
    primary_key = product.indexes.primary.to_dict()

    # Assert key structure
    assert "pk" in primary_key
    assert "sk" in primary_key
    assert primary_key["pk"] == "product#test_001"
    assert primary_key["sk"] == "product#test_001"

    print("✓ All key assertions passed!")
    print(f"  Primary key validated: {primary_key}")


def example_debug_info_with_conditions():
    """Example: See what condition is being used"""
    print("\n=== Example 9: Debug Query Conditions ===")

    product = Product()
    product.id = "prod_555"
    product.category = "electronics"

    # Debug with begins_with (default)
    debug = product.indexes.get("gsi1").debug_info(condition="begins_with")
    print(f"Query condition: {debug['sort_key']['condition']}")
    print(f"Sort key value: {debug['sort_key']['value']}")
    print(f"Full debug info:")
    import json

    print(json.dumps(debug, indent=2))

    # Now try with 'eq' condition
    debug_eq = product.indexes.get("gsi1").debug_info(condition="eq")
    print(f"\nWith 'eq' condition: {debug_eq['sort_key']['condition']}")


def example_debug_between_condition():
    """Example: Debug 'between' queries"""
    print("\n=== Example 10: Debug 'between' Condition ===")

    # Simulating a price range query
    from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
    from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey

    price_index = DynamoDBIndex(index_name="gsi_price")
    price_index.partition_key.attribute_name = "gsi_price_pk"
    price_index.partition_key.value = lambda: "products#"
    price_index.sort_key.attribute_name = "gsi_price_sk"
    price_index.sort_key.value = lambda: "price#"

    # Debug a between query
    debug = price_index.debug_info(condition="between", low_value="10.00", high_value="50.00")

    print(f"Condition: {debug['sort_key']['condition']}")
    print(f"Low value: {debug['sort_key']['low_value']}")
    print(f"High value: {debug['sort_key']['high_value']}")
    print(f"Full range: {debug['sort_key']['full_range']}")
    # Output shows: {'low': 'price#10.00', 'high': 'price#50.00'}


def example_troubleshoot_wrong_condition():
    """Example: Troubleshoot why a query isn't working"""
    print("\n=== Example 11: Troubleshoot Query Issues ===")

    product = Product()
    product.id = "prod_999"
    product.category = "gadgets"

    # You're trying to query but it's not working...
    # Let's check what condition is being used
    gsi = product.indexes.get("gsi1")

    # Check if you're using the right condition
    debug = gsi.debug_info(condition="begins_with")
    print(f"[DEBUG] Index: {debug['index_name']}")
    print(f"[DEBUG] Query type: {debug['query_type']}")
    print(f"[DEBUG] Partition key: {debug['partition_key']}")
    print(f"[DEBUG] Sort key condition: {debug['sort_key']['condition']}")

    # Ah! Maybe you meant to use 'eq' instead?
    debug_eq = gsi.debug_info(condition="eq")
    print(f"\n[DEBUG] Trying with 'eq': {debug_eq['sort_key']['condition']}")

    # This helps you understand what condition your query will use!


def example_compare_conditions():
    """Example: Compare different conditions"""
    print("\n=== Example 12: Compare Different Conditions ===")

    product = Product()
    product.id = "prod_123"
    product.category = "books"

    gsi = product.indexes.get("gsi1")

    conditions = ["begins_with", "eq", "gt", "gte", "lt"]

    print("Comparing conditions for same key:")
    for condition in conditions:
        debug = gsi.debug_info(condition=condition)
        print(f"  - {condition:12s}: sort_key value = '{debug['sort_key']['value']}'")

    print("\nThis helps you choose the right condition for your query!")


def main():
    """Run all examples"""
    print("=" * 60)
    print("DynamoDB Key Debugging Examples")
    print("=" * 60)

    example_basic_key_debugging()
    example_index_debugging()
    example_partition_key_only()
    example_logging_before_save()
    example_composite_key_verification()
    example_dynamic_key_changes()
    example_troubleshooting_query()
    example_unit_testing_keys()
    example_debug_info_with_conditions()
    example_debug_between_condition()
    example_troubleshoot_wrong_condition()
    example_compare_conditions()

    print("\n" + "=" * 60)
    print("Summary:")
    print("  - Use key.to_dict() to debug single keys")
    print("  - Use index.to_dict() to get full key dictionary")
    print("  - Use index.debug_info() to see conditions and full query info")
    print("  - Use include_sort_key=False for partition key only")
    print("  - Perfect for logging, debugging, and testing!")
    print("=" * 60)


if __name__ == "__main__":
    main()
