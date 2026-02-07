"""
Tests for DynamoDBKey and DynamoDBIndex to_dict() methods
"""

import unittest

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class TestDynamoDBKeyToDict(unittest.TestCase):
    """Test DynamoDBKey.to_dict() method"""

    def test_to_dict_with_string_value(self):
        """Test to_dict with a simple string value"""
        key = DynamoDBKey(attribute_name="pk", value="user#123")

        result = key.to_dict()

        self.assertEqual(result, {"pk": "user#123"})
        self.assertIsInstance(result, dict)

    def test_to_dict_with_lambda_value(self):
        """Test to_dict with a lambda function value"""
        key = DynamoDBKey(attribute_name="pk", value=lambda: "product#456")

        result = key.to_dict()

        self.assertEqual(result, {"pk": "product#456"})

    def test_to_dict_with_build_key(self):
        """Test to_dict with DynamoDBKey.build_key()"""
        user_id = "789"
        key = DynamoDBKey(
            attribute_name="pk", value=lambda: DynamoDBKey.build_key(("user", user_id))
        )

        result = key.to_dict()

        self.assertEqual(result, {"pk": "user#789"})

    def test_to_dict_with_dynamic_value_change(self):
        """Test that to_dict reflects current lambda value"""
        values = {"id": "123"}
        key = DynamoDBKey(attribute_name="pk", value=lambda: f"user#{values['id']}")

        # First call
        result1 = key.to_dict()
        self.assertEqual(result1, {"pk": "user#123"})

        # Change the underlying value
        values["id"] = "456"

        # Second call should reflect new value
        result2 = key.to_dict()
        self.assertEqual(result2, {"pk": "user#456"})


class TestDynamoDBIndexToDict(unittest.TestCase):
    """Test DynamoDBIndex.to_dict() method"""

    def test_to_dict_with_partition_and_sort_keys(self):
        """Test to_dict with both partition and sort keys"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "user#123"
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: "user#123"

        result = index.to_dict()

        self.assertEqual(result, {"pk": "user#123", "sk": "user#123"})

    def test_to_dict_partition_key_only(self):
        """Test to_dict with only partition key"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "user#123"
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: "user#123"

        result = index.to_dict(include_sort_key=False)

        self.assertEqual(result, {"pk": "user#123"})

    def test_to_dict_with_gsi_attributes(self):
        """Test to_dict with GSI attribute names"""
        index = DynamoDBIndex(index_name="gsi1")
        index.partition_key.attribute_name = "gsi1_pk"
        index.partition_key.value = lambda: "users#"
        index.sort_key.attribute_name = "gsi1_sk"
        index.sort_key.value = lambda: "email#test@example.com"

        result = index.to_dict()

        self.assertEqual(result, {"gsi1_pk": "users#", "gsi1_sk": "email#test@example.com"})

    def test_to_dict_with_composite_keys(self):
        """Test to_dict with complex composite keys"""
        tenant_id = "tenant_456"
        user_id = "user_789"

        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", tenant_id), ("user", user_id)
        )
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", tenant_id), ("user", user_id)
        )

        result = index.to_dict()

        self.assertEqual(
            result,
            {"pk": "tenant#tenant_456#user#user_789", "sk": "tenant#tenant_456#user#user_789"},
        )

    def test_to_dict_handles_unset_sort_key(self):
        """Test that to_dict gracefully handles unset sort key value"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "user#123"
        # Sort key attribute name set but value not set
        index.sort_key.attribute_name = "sk"

        # Should not raise an error, just omit the sort key
        result = index.to_dict()

        # Should only have partition key
        self.assertEqual(result, {"pk": "user#123"})

    def test_to_dict_for_debugging_output(self):
        """Test that to_dict produces useful debugging output"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "product#prod_123"
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: "product#prod_123"

        result = index.to_dict()

        # Should be easily readable
        debug_output = f"Querying DynamoDB with key: {result}"
        self.assertIn("pk", debug_output)
        self.assertIn("product#prod_123", debug_output)

        # Should work with print statements
        output = str(result)
        self.assertIn("'pk'", output)
        self.assertIn("'sk'", output)


class TestDynamoDBKeyIntegration(unittest.TestCase):
    """Integration tests for using to_dict in real scenarios"""

    def test_debug_workflow(self):
        """Test a typical debugging workflow"""
        # Simulate a model with indexes
        product_id = "prod_999"

        # Primary index
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("product", product_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("product", product_id))

        # Get dictionary for debugging
        key_dict = primary.to_dict()

        # Verify it's in the format needed for boto3
        self.assertIn("pk", key_dict)
        self.assertIn("sk", key_dict)
        self.assertEqual(key_dict["pk"], "product#prod_999")
        self.assertEqual(key_dict["sk"], "product#prod_999")

        # Could use this directly in a DynamoDB get operation
        # db.get(table_name="my_table", key=key_dict)

    def test_gsi_debug_workflow(self):
        """Test debugging a GSI key"""
        email = "test@example.com"

        gsi = DynamoDBIndex(index_name="gsi1")
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: "users#"
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("email", email))

        # Get just the keys for logging
        key_dict = gsi.to_dict()

        self.assertEqual(key_dict, {"gsi1_pk": "users#", "gsi1_sk": "email#test@example.com"})


class TestDynamoDBIndexDebugInfo(unittest.TestCase):
    """Test DynamoDBIndex.debug_info() method"""

    def test_debug_info_with_begins_with(self):
        """Test debug_info shows begins_with condition"""
        index = DynamoDBIndex(index_name="gsi1")
        index.partition_key.attribute_name = "gsi1_pk"
        index.partition_key.value = lambda: "category#electronics"
        index.sort_key.attribute_name = "gsi1_sk"
        index.sort_key.value = lambda: "product#"

        debug = index.debug_info(condition="begins_with")

        self.assertEqual(debug["index_name"], "gsi1")
        self.assertEqual(debug["query_type"], "GSI/LSI")
        self.assertEqual(debug["partition_key"]["attribute"], "gsi1_pk")
        self.assertEqual(debug["partition_key"]["value"], "category#electronics")
        self.assertEqual(debug["sort_key"]["attribute"], "gsi1_sk")
        self.assertEqual(debug["sort_key"]["value"], "product#")
        self.assertEqual(debug["sort_key"]["condition"], "begins_with")

    def test_debug_info_with_eq(self):
        """Test debug_info shows eq condition"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "user#123"
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: "user#123"

        debug = index.debug_info(condition="eq")

        self.assertEqual(debug["sort_key"]["condition"], "eq")

    def test_debug_info_with_gt(self):
        """Test debug_info shows gt (greater than) condition"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "orders#"
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: "date#2024-01-01"

        debug = index.debug_info(condition="gt")

        self.assertEqual(debug["sort_key"]["condition"], "gt")
        self.assertEqual(debug["sort_key"]["value"], "date#2024-01-01")

    def test_debug_info_with_between(self):
        """Test debug_info shows between condition with range"""
        index = DynamoDBIndex()
        index.partition_key.attribute_name = "pk"
        index.partition_key.value = lambda: "prices#"
        index.sort_key.attribute_name = "sk"
        index.sort_key.value = lambda: "price#"

        debug = index.debug_info(condition="between", low_value="10.00", high_value="50.00")

        self.assertEqual(debug["sort_key"]["condition"], "between")
        self.assertEqual(debug["sort_key"]["low_value"], "10.00")
        self.assertEqual(debug["sort_key"]["high_value"], "50.00")
        self.assertEqual(debug["sort_key"]["full_range"]["low"], "price#10.00")
        self.assertEqual(debug["sort_key"]["full_range"]["high"], "price#50.00")

    def test_debug_info_primary_index(self):
        """Test debug_info identifies primary index"""
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: "user#123"

        debug = primary.debug_info()

        self.assertEqual(debug["query_type"], "Primary")

    def test_debug_info_includes_keys_dict(self):
        """Test debug_info includes convenient keys_dict"""
        index = DynamoDBIndex(index_name="gsi1")
        index.partition_key.attribute_name = "gsi1_pk"
        index.partition_key.value = lambda: "test#value"
        index.sort_key.attribute_name = "gsi1_sk"
        index.sort_key.value = lambda: "sort#value"

        debug = index.debug_info()

        self.assertIn("keys_dict", debug)
        self.assertEqual(debug["keys_dict"], {"gsi1_pk": "test#value", "gsi1_sk": "sort#value"})

    def test_debug_info_partition_key_only(self):
        """Test debug_info with partition key only"""
        index = DynamoDBIndex(index_name="gsi1")
        index.partition_key.attribute_name = "gsi1_pk"
        index.partition_key.value = lambda: "all#items"

        debug = index.debug_info(include_sort_key=False)

        self.assertIn("partition_key", debug)
        self.assertNotIn("sort_key", debug)
        self.assertEqual(debug["keys_dict"], {"gsi1_pk": "all#items"})


if __name__ == "__main__":
    unittest.main()
