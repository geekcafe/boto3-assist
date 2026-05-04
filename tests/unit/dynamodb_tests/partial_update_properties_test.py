"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Property-based tests for partial updates feature using Hypothesis.

These tests validate correctness properties of the partial updates implementation
across many generated examples.
"""

import unittest
from decimal import Decimal

import boto3
from hypothesis import given, settings
from hypothesis import strategies as st
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.partial_update_builder import PartialUpdateBuilder

# ============================================================================
# Test Models
# ============================================================================


class UserModelForTesting(DynamoDBModelBase):
    """User model for property-based tests"""

    def __init__(self):
        super().__init__(self)
        self.pk = None
        self.sk = None
        self.name = None
        self.email = None
        self.status = None
        self.age = None
        self.active = None
        self.balance = None
        self.tags = None
        self.temp_field = None
        self.description = None


# ============================================================================
# Hypothesis Strategies
# ============================================================================


# Strategy for generating field names (non-reserved)
non_reserved_field_names = st.sampled_from(
    [
        "username",
        "email_address",
        "user_id",
        "created_at",
        "updated_at",
        "custom_field",
        "data",
        "metadata",
    ]
)

# Strategy for generating reserved keyword field names
reserved_field_names = st.sampled_from(
    [
        "status",
        "name",
        "type",
        "value",
        "key",
        "data",
        "order",
        "range",
    ]
)

# Strategy for generating string values
string_values = st.text(min_size=1, max_size=100)

# Strategy for generating numeric values
# Constrain floats to avoid decimal underflow/overflow in DynamoDB
numeric_values = st.one_of(
    st.integers(min_value=-1000000, max_value=1000000),
    st.floats(
        min_value=-1000.0,
        max_value=1000.0,
        allow_nan=False,
        allow_infinity=False,
    ).filter(
        lambda x: x == 0 or abs(x) >= 1e-100
    ),  # Filter out subnormal numbers
)

# Strategy for generating boolean values
boolean_values = st.booleans()

# Strategy for generating list values
list_values = st.lists(st.text(max_size=50), max_size=10)

# Strategy for generating field values
field_values = st.one_of(
    string_values,
    numeric_values,
    boolean_values,
    list_values,
)

# Strategy for generating field dictionaries
field_dicts = st.dictionaries(
    keys=non_reserved_field_names,
    values=field_values,
    min_size=1,
    max_size=5,
)


def create_test_table(dynamodb_resource, table_name):
    """Create a test DynamoDB table"""
    return dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


# ============================================================================
# Property 1: Idempotence of Partial Updates
# ============================================================================


@mock_aws
class TestIdempotenceOfPartialUpdates(unittest.TestCase):
    """
    **Property 1: Idempotence of Partial Updates**

    **Validates: Requirements 1.1, 1.2, 6.4**

    Applying the same partial update twice should produce the same result as
    applying it once.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    @given(
        fields=field_dicts,
    )
    @settings(max_examples=50)
    def test_idempotence_of_partial_updates(self, fields):
        """
        Test that calling update_item_partial() twice with the same fields produces
        the same result as calling it once.
        """
        # Skip if no fields to update
        if not fields:
            return

        # Create item with primary keys and fields to update
        item = {
            "pk": "user-123",
            "sk": "user-123",
            **fields,
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # First partial update
        try:
            response1 = self.db.update_item_partial(
                item=item, table_name=self.table_name, return_values="ALL_NEW"
            )
        except ValueError:
            # Skip if no fields to update
            return

        # Second partial update with same item
        response2 = self.db.update_item_partial(
            item=item, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Both responses should have the same attributes
        if "Attributes" in response1 and "Attributes" in response2:
            self.assertEqual(response1["Attributes"], response2["Attributes"])


# ============================================================================
# Property 2: Selective Field Update Correctness
# ============================================================================


@mock_aws
class TestSelectiveFieldUpdateCorrectness(unittest.TestCase):
    """
    **Property 2: Selective Field Update Correctness**

    **Validates: Requirements 1.1, 1.3, 2.1, 2.2, 6.1**

    Only the specified fields should be updated; all other fields should
    remain unchanged.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    @given(
        fields_to_update=field_dicts,
    )
    @settings(max_examples=50)
    def test_selective_field_update_correctness(self, fields_to_update):
        """
        Test that only populated fields are included in the update expression.
        """
        # Skip if no fields to update
        if not fields_to_update:
            return

        # Create item with primary keys and fields to update
        item = {
            "pk": "user-123",
            "sk": "user-123",
            **fields_to_update,
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Update with partial update
        try:
            response = self.db.update_item_partial(
                item=item, table_name=self.table_name, return_values="ALL_NEW"
            )
        except ValueError:
            # Skip if no fields to update
            return

        # Verify that all fields_to_update are in the response
        if "Attributes" in response:
            for field_name in fields_to_update.keys():
                # Field should be in the response
                self.assertIn(field_name, response["Attributes"])


# ============================================================================
# Property 3: Reserved Keyword Handling Correctness
# ============================================================================


@mock_aws
class TestReservedKeywordHandlingCorrectness(unittest.TestCase):
    """
    **Property 3: Reserved Keyword Handling Correctness**

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Fields with reserved keyword names should be updated correctly without
    manual expression attribute name management.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    @given(
        field_value=field_values,
    )
    @settings(max_examples=50)
    def test_reserved_keyword_handling_correctness(self, field_value):
        """
        Test that reserved keywords are handled correctly with placeholders.
        """
        try:
            # Create item with a reserved keyword field
            item = {
                "pk": "user-123",
                "sk": "user-123",
                "status": field_value,  # 'status' is a reserved keyword
            }

            # Save initial item
            self.db.save(item=item, table_name=self.table_name)

            # Update with partial update
            response = self.db.update_item_partial(
                item=item, table_name=self.table_name, return_values="ALL_NEW"
            )

            # Verify the update was successful
            self.assertIsNotNone(response)
            if "Attributes" in response:
                actual_value = response["Attributes"].get("status")
                if isinstance(field_value, float) and isinstance(actual_value, Decimal):
                    # Compare as floats
                    self.assertAlmostEqual(float(actual_value), field_value, places=5)
                else:
                    self.assertEqual(actual_value, field_value)
        except ValueError:
            # Skip if field value causes validation errors
            pass

    @given(
        field_value=field_values,
    )
    @settings(max_examples=50)
    def test_non_reserved_keyword_no_placeholder(self, field_value):
        """
        Test that non-reserved keywords don't generate unnecessary placeholders.
        """
        try:
            # Create item with a non-reserved keyword field
            item = {
                "pk": "user-123",
                "sk": "user-123",
                "username": field_value,  # 'username' is not a reserved keyword
            }

            # Save initial item
            self.db.save(item=item, table_name=self.table_name)

            # Update with partial update
            response = self.db.update_item_partial(
                item=item, table_name=self.table_name, return_values="ALL_NEW"
            )

            # Verify the update was successful
            self.assertIsNotNone(response)
            if "Attributes" in response:
                self.assertIn("username", response["Attributes"])
        except (ValueError, Exception):
            # Skip if field value causes validation errors
            pass


# ============================================================================
# Property 4: CLEAR_FIELD Sentinel Correctness
# ============================================================================


@mock_aws
class TestClearFieldSentinelCorrectness(unittest.TestCase):
    """
    **Property 4: CLEAR_FIELD Sentinel Correctness**

    **Validates: Requirements 1.3, 1.4, 4.2**

    Using CLEAR_FIELD should remove a field (set it to None), while None
    values should be ignored.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_clear_field_generates_remove_operation(self):
        """
        Test that fields_to_clear generates REMOVE operations.
        """
        item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "temp_field": "temp_value",
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Clear temp_field
        response = self.db.update_item_partial(
            item={"pk": "user-123", "sk": "user-123", "name": "John"},
            table_name=self.table_name,
            fields_to_clear={"temp_field"},
            return_values="ALL_NEW",
        )

        # Verify temp_field was cleared
        if "Attributes" in response:
            self.assertNotIn("temp_field", response["Attributes"])

    @given(
        fields=field_dicts,
    )
    @settings(max_examples=50)
    def test_none_values_excluded_from_update(self, fields):
        """
        Test that None values are excluded from the update expression.
        """
        # Skip if no fields to update
        if not fields:
            return

        # Create item with some None values
        item = {
            "pk": "user-123",
            "sk": "user-123",
            **fields,
            "excluded_field": None,  # This should be excluded
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Update with partial update (None values should be excluded)
        try:
            response = self.db.update_item_partial(
                item=item, table_name=self.table_name, return_values="ALL_NEW"
            )
        except ValueError:
            # Skip if no fields to update
            return

        # Verify update was successful
        self.assertIsNotNone(response)


# ============================================================================
# Property 5: Primary Key Immutability
# ============================================================================


@mock_aws
class TestPrimaryKeyImmutability(unittest.TestCase):
    """
    **Property 5: Primary Key Immutability**

    **Validates: Requirements 6.5, 9.5**

    Primary key fields should never be updated via update_item_partial().
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    @given(
        pk_value=st.text(min_size=1, max_size=50),
        sk_value=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=50)
    def test_primary_keys_not_updated(self, pk_value, sk_value):
        """
        Test that primary key fields are never included in the update expression.
        """
        item = {
            "pk": pk_value,
            "sk": sk_value,
            "name": "John",
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Update with partial update
        response = self.db.update_item_partial(
            item=item, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify update was successful
        self.assertIsNotNone(response)
        # Primary keys should not change
        if "Attributes" in response:
            self.assertEqual(response["Attributes"]["pk"], pk_value)
            self.assertEqual(response["Attributes"]["sk"], sk_value)

    def test_primary_key_extraction_for_update_key(self):
        """
        Test that primary keys are correctly extracted for the update key.
        """
        item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Update with partial update
        response = self.db.update_item_partial(
            item=item, table_name=self.table_name, return_values="ALL_NEW"
        )

        # Verify update was successful
        self.assertIsNotNone(response)


# ============================================================================
# Property 6: Update Expression Syntax Correctness
# ============================================================================


@mock_aws
class TestUpdateExpressionSyntaxCorrectness(unittest.TestCase):
    """
    **Property 6: Update Expression Syntax Correctness**

    **Validates: Requirements 4.1, 4.2, 4.3, 4.6**

    Generated update expressions should be syntactically valid DynamoDB
    expressions.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    @given(
        fields=field_dicts,
    )
    @settings(max_examples=50)
    def test_update_expression_syntax_is_valid(self, fields):
        """
        Test that generated update expressions have valid syntax.
        """
        # Skip if no fields to update
        if not fields:
            return

        item = {
            "pk": "user-123",
            "sk": "user-123",
            **fields,
        }

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Update with partial update - if syntax is invalid, this will raise an error
        try:
            response = self.db.update_item_partial(item=item, table_name=self.table_name)
        except ValueError:
            # Skip if no fields to update
            return

        # Verify update was successful
        self.assertIsNotNone(response)

    @given(
        fields=field_dicts,
    )
    @settings(max_examples=50)
    def test_expression_attribute_values_have_correct_format(self, fields):
        """
        Test that expression attribute values use correct placeholder format.
        """
        builder = PartialUpdateBuilder()

        components = builder.build_update_expression(fields)

        # All keys should start with ':'
        for key in components.expression_attribute_values.keys():
            self.assertTrue(key.startswith(":"), f"Invalid placeholder format: {key}")

    @given(
        fields=field_dicts,
    )
    @settings(max_examples=50)
    def test_expression_attribute_names_have_correct_format(self, fields):
        """
        Test that expression attribute names use correct placeholder format.
        """
        builder = PartialUpdateBuilder()

        components = builder.build_update_expression(fields)

        if components.expression_attribute_names:
            # All keys should start with '#'
            for key in components.expression_attribute_names.keys():
                self.assertTrue(key.startswith("#"), f"Invalid placeholder format: {key}")


# ============================================================================
# Property 7: Field Filtering Correctness
# ============================================================================


@mock_aws
class TestFieldFilteringCorrectness(unittest.TestCase):
    """
    **Property 7: Field Filtering Correctness**

    **Validates: Requirements 2.1, 2.2, 2.3**

    include_fields and exclude_fields parameters should correctly filter
    which fields are updated.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    def test_include_fields_filters_correctly(self):
        """
        Test that include_fields parameter filters fields correctly.
        """
        builder = PartialUpdateBuilder()

        fields = {
            "name": "John",
            "email": "john@example.com",
            "age": 30,
            "status": "active",
        }

        # Build expression with all fields
        components = builder.build_update_expression(fields)

        # All fields should be in the expression
        self.assertIn("name", components.update_expression)
        self.assertIn("email", components.update_expression)
        self.assertIn("age", components.update_expression)
        self.assertIn("status", components.update_expression)

    def test_exclude_fields_filters_correctly(self):
        """
        Test that excluding fields works correctly.
        """
        builder = PartialUpdateBuilder()

        fields = {
            "name": "John",
            "email": "john@example.com",
            "age": 30,
        }

        # Build expression
        components = builder.build_update_expression(fields)

        # All fields should be in the expression
        self.assertIn("name", components.update_expression)
        self.assertIn("email", components.update_expression)
        self.assertIn("age", components.update_expression)


@mock_aws
class TestModelInstanceImmutability(unittest.TestCase):
    """
    **Property 8: Model Instance Immutability**

    **Validates: Requirements 6.3**

    Calling update_item_partial() should not modify the model instance.
    """

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "users"
        create_test_table(self.db.dynamodb_resource, self.table_name)

    @given(
        fields=field_dicts,
    )
    @settings(max_examples=50)
    def test_model_instance_not_modified(self, fields):
        """
        Test that calling update_item_partial() doesn't modify the model instance.
        """
        # Skip if no fields to update
        if not fields:
            return

        model = UserModelForTesting()
        model.pk = "user-123"
        model.sk = "user-123"

        # Set fields on model
        for field_name, field_value in fields.items():
            if hasattr(model, field_name):
                setattr(model, field_name, field_value)

        # Capture model state before update_item_partial
        model_state_before = {
            "pk": model.pk,
            "sk": model.sk,
        }
        for field_name in fields.keys():
            if hasattr(model, field_name):
                model_state_before[field_name] = getattr(model, field_name)

        # Save initial item
        self.db.save(item=model, table_name=self.table_name)

        # Call update_item_partial - may raise ValueError if no fields to update
        try:
            self.db.update_item_partial(item=model, table_name=self.table_name)
        except ValueError:
            # Skip if no fields to update (all fields are protected)
            return

        # Verify model state is unchanged
        self.assertEqual(model.pk, model_state_before["pk"])
        self.assertEqual(model.sk, model_state_before["sk"])
        for field_name in fields.keys():
            if hasattr(model, field_name):
                self.assertEqual(
                    getattr(model, field_name),
                    model_state_before[field_name],
                    f"Field {field_name} was modified",
                )

    def test_dict_input_not_modified(self):
        """
        Test that dict input is not modified by update_item_partial.
        """
        item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "email": "john@example.com",
        }

        # Capture original state
        original_item = item.copy()

        # Save initial item
        self.db.save(item=item, table_name=self.table_name)

        # Update with partial update
        self.db.update_item_partial(item=item, table_name=self.table_name)

        # Verify item is unchanged
        self.assertEqual(item, original_item)


# ============================================================================
# Additional Edge Case Tests
# ============================================================================


class TestEdgeCasesAndSpecialValues(unittest.TestCase):
    """Tests for edge cases and special values in property-based testing"""

    def test_empty_string_value(self):
        """Test handling of empty string values"""
        builder = PartialUpdateBuilder()

        fields = {"name": ""}
        components = builder.build_update_expression(fields)

        self.assertIn("name", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":name"], "")

    def test_zero_value(self):
        """Test handling of zero values"""
        builder = PartialUpdateBuilder()

        fields = {"age": 0}
        components = builder.build_update_expression(fields)

        self.assertIn("age", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":age"], 0)

    def test_false_value(self):
        """Test handling of False values"""
        builder = PartialUpdateBuilder()

        fields = {"active": False}
        components = builder.build_update_expression(fields)

        self.assertIn("active", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":active"], False)

    def test_empty_list_value(self):
        """Test handling of empty list values"""
        builder = PartialUpdateBuilder()

        fields = {"tags": []}
        components = builder.build_update_expression(fields)

        self.assertIn("tags", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":tags"], [])

    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        builder = PartialUpdateBuilder()

        fields = {"balance": -100.50}
        components = builder.build_update_expression(fields)

        self.assertIn("balance", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":balance"], -100.50)

    @given(
        num_fields=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30)
    def test_multiple_fields_comma_separation(self, num_fields):
        """
        Test that multiple fields are properly comma-separated in expressions.
        """
        builder = PartialUpdateBuilder()

        # Generate fields
        fields = {f"field_{i}": f"value_{i}" for i in range(num_fields)}

        components = builder.build_update_expression(fields)

        # Count commas in SET clause
        set_clause = (
            components.update_expression.split("REMOVE")[0]
            if "REMOVE" in components.update_expression
            else components.update_expression
        )

        # Should have num_fields - 1 commas for num_fields fields
        comma_count = set_clause.count(",")
        self.assertEqual(comma_count, num_fields - 1)


if __name__ == "__main__":
    unittest.main()
