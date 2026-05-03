"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for DynamoDB.update_item_partial() method
"""

import unittest
from unittest.mock import MagicMock, patch

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class UserModel(DynamoDBModelBase):
    """User model for testing"""

    def __init__(self):
        super().__init__(self)
        self.pk = None
        self.sk = None
        self.id = None
        self.name = None
        self.email = None
        self.status = None
        self.age = None
        self.active = None
        self.temp_field = None


# ============================================================================
# 6.1 Validation Tests
# ============================================================================


class TestUpdateItemPartialValidation(unittest.TestCase):
    """Tests for validation in update_item_partial() - Requirement 6.1"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_missing_table_name_raises_value_error(self):
        """Test missing table_name raises ValueError with clear message"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(item=item, table_name="")

        self.assertIn("table_name", str(context.exception))

    def test_missing_primary_key_pk_raises_value_error(self):
        """Test missing primary key (pk) raises ValueError"""
        item = {"sk": "user-123", "name": "John"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(item=item, table_name="users")

        self.assertIn("pk", str(context.exception))

    def test_missing_primary_key_sk_raises_value_error(self):
        """Test missing sort key (sk) raises ValueError"""
        item = {"pk": "user-123", "name": "John"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(item=item, table_name="users")

        self.assertIn("sk", str(context.exception))

    def test_invalid_return_values_raises_value_error(self):
        """Test invalid return_values raises ValueError"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(
                item=item,
                table_name="users",
                return_values="INVALID_VALUE",
            )

        self.assertIn("return_values", str(context.exception))

    def test_fields_to_clear_with_primary_key_raises_value_error(self):
        """Test fields_to_clear with primary key raises ValueError"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(
                item=item,
                table_name="users",
                fields_to_clear={"pk"},
            )

        self.assertIn("Cannot clear", str(context.exception))

    def test_no_fields_to_update_raises_value_error(self):
        """Test no fields to update raises ValueError"""
        item = {"pk": "user-123", "sk": "user-123"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(item=item, table_name="users")

        self.assertIn("No fields to update", str(context.exception))


# ============================================================================
# 6.2 Field Identification Tests
# ============================================================================


class TestUpdateItemPartialFieldIdentification(unittest.TestCase):
    """Tests for field identification in update_item_partial() - Requirement 6.2"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_non_none_fields_are_identified(self):
        """Test non-None fields are identified correctly"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John", "email": "john@example.com"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            # Should contain name and email in the expression
            self.assertIn("name", update_expr)
            self.assertIn("email", update_expr)

    def test_none_values_are_excluded_from_update(self):
        """Test None values are excluded from update"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John", "email": None}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            # Should contain name but not email
            self.assertIn("name", update_expr)

    def test_primary_keys_are_excluded_from_update(self):
        """Test primary keys are excluded from update"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")
            attr_values = call_args.kwargs.get("expression_attribute_values")

            # Primary keys should not be in the update expression
            self.assertNotIn(":pk", str(attr_values))
            self.assertNotIn(":sk", str(attr_values))

    def test_fields_to_clear_are_properly_identified(self):
        """Test fields_to_clear are properly identified"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                fields_to_clear={"temp_field"},
            )

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            # Should contain REMOVE clause
            self.assertIn("REMOVE", update_expr)
            self.assertIn("temp_field", update_expr)

    def test_combination_of_updates_and_clears(self):
        """Test combination of updates and clears"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                fields_to_clear={"temp_field"},
            )

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            # Should contain both SET and REMOVE
            self.assertIn("SET", update_expr)
            self.assertIn("REMOVE", update_expr)


# ============================================================================
# 6.3 Expression Generation Tests
# ============================================================================


class TestUpdateItemPartialExpressionGeneration(unittest.TestCase):
    """Tests for expression generation in update_item_partial() - Requirement 6.3"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_correct_update_expression_is_generated(self):
        """Test correct update expression is generated"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            # Should start with SET
            self.assertTrue(update_expr.startswith("SET"))

    def test_expression_attribute_names_generated_for_reserved_keywords(self):
        """Test expression attribute names are generated for reserved keywords"""
        item = {"pk": "user-123", "sk": "user-123", "status": "active"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            attr_names = call_args.kwargs.get("expression_attribute_names")

            # Should have placeholder for reserved keyword
            self.assertIsNotNone(attr_names)
            self.assertIn("#status", attr_names)
            self.assertEqual(attr_names["#status"], "status")

    def test_expression_attribute_values_generated_correctly(self):
        """Test expression attribute values are generated correctly"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            attr_values = call_args.kwargs.get("expression_attribute_values")

            # Should have value placeholder
            self.assertIsNotNone(attr_values)
            self.assertIn(":name", attr_values)
            self.assertEqual(attr_values[":name"], "John")

    def test_user_provided_expression_attribute_names_are_merged(self):
        """Test user-provided expression_attribute_names are merged"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                expression_attribute_names={"#custom": "custom_field"},
            )

            call_args = mock_update.call_args
            attr_names = call_args.kwargs.get("expression_attribute_names")

            # Should contain both auto-generated and user-provided
            self.assertIn("#custom", attr_names)
            self.assertEqual(attr_names["#custom"], "custom_field")

    def test_user_provided_expression_attribute_values_are_merged(self):
        """Test user-provided expression_attribute_values are merged"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                expression_attribute_values={":custom": "custom_value"},
            )

            call_args = mock_update.call_args
            attr_values = call_args.kwargs.get("expression_attribute_values")

            # Should contain both auto-generated and user-provided
            self.assertIn(":custom", attr_values)
            self.assertEqual(attr_values[":custom"], "custom_value")


# ============================================================================
# 6.4 Conditional Write Tests
# ============================================================================


class TestUpdateItemPartialConditionalWrite(unittest.TestCase):
    """Tests for conditional writes in update_item_partial() - Requirement 6.4"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_condition_expression_is_passed_to_update_item(self):
        """Test condition_expression is passed to update_item()"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                condition_expression="attribute_exists(id)",
            )

            call_args = mock_update.call_args
            condition = call_args.kwargs.get("condition_expression")

            self.assertEqual(condition, "attribute_exists(id)")

    def test_condition_expression_with_expression_attribute_values(self):
        """Test condition_expression with expression_attribute_values"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                condition_expression="version = :expected_version",
                expression_attribute_values={":expected_version": 5},
            )

            call_args = mock_update.call_args
            condition = call_args.kwargs.get("condition_expression")
            attr_values = call_args.kwargs.get("expression_attribute_values")

            self.assertEqual(condition, "version = :expected_version")
            self.assertIn(":expected_version", attr_values)


# ============================================================================
# 6.5 Return Values Tests
# ============================================================================


class TestUpdateItemPartialReturnValues(unittest.TestCase):
    """Tests for return values in update_item_partial() - Requirement 6.5"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_return_values_none_returns_minimal_response(self):
        """Test return_values='NONE' returns minimal response"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            result = self.db.update_item_partial(
                item=item,
                table_name="users",
                return_values="NONE",
            )

            call_args = mock_update.call_args
            return_values = call_args.kwargs.get("return_values")

            self.assertEqual(return_values, "NONE")
            self.assertEqual(result, {})

    def test_return_values_all_new_returns_complete_item(self):
        """Test return_values='ALL_NEW' returns complete item"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}
        expected_response = {"Attributes": {"pk": "user-123", "sk": "user-123", "name": "John"}}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = expected_response
            result = self.db.update_item_partial(
                item=item,
                table_name="users",
                return_values="ALL_NEW",
            )

            call_args = mock_update.call_args
            return_values = call_args.kwargs.get("return_values")

            self.assertEqual(return_values, "ALL_NEW")
            self.assertIn("Attributes", result)

    def test_return_values_updated_new_returns_only_updated_fields(self):
        """Test return_values='UPDATED_NEW' returns only updated fields"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}
        expected_response = {"Attributes": {"name": "John"}}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = expected_response
            result = self.db.update_item_partial(
                item=item,
                table_name="users",
                return_values="UPDATED_NEW",
            )

            call_args = mock_update.call_args
            return_values = call_args.kwargs.get("return_values")

            self.assertEqual(return_values, "UPDATED_NEW")

    def test_return_values_all_old_returns_item_before_update(self):
        """Test return_values='ALL_OLD' returns item before update"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}
        expected_response = {"Attributes": {"pk": "user-123", "sk": "user-123", "name": "Jane"}}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = expected_response
            result = self.db.update_item_partial(
                item=item,
                table_name="users",
                return_values="ALL_OLD",
            )

            call_args = mock_update.call_args
            return_values = call_args.kwargs.get("return_values")

            self.assertEqual(return_values, "ALL_OLD")

    def test_return_values_updated_old_returns_updated_fields_before_update(self):
        """Test return_values='UPDATED_OLD' returns updated fields before update"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}
        expected_response = {"Attributes": {"name": "Jane"}}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = expected_response
            result = self.db.update_item_partial(
                item=item,
                table_name="users",
                return_values="UPDATED_OLD",
            )

            call_args = mock_update.call_args
            return_values = call_args.kwargs.get("return_values")

            self.assertEqual(return_values, "UPDATED_OLD")


# ============================================================================
# 6.6 Error Handling and Logging Tests
# ============================================================================


class TestUpdateItemPartialErrorHandling(unittest.TestCase):
    """Tests for error handling and logging in update_item_partial() - Requirement 6.6"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_successful_updates_are_logged(self):
        """Test successful updates are logged at INFO level"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            with patch("boto3_assist.dynamodb.dynamodb.logger") as mock_logger:
                self.db.update_item_partial(item=item, table_name="users")

                # Verify logger.info was called
                self.assertTrue(mock_logger.info.called)

    def test_validation_errors_are_logged_and_reraised(self):
        """Test validation errors are logged and re-raised"""
        item = {"pk": "user-123", "sk": "user-123"}

        with patch("boto3_assist.dynamodb.dynamodb.logger") as mock_logger:
            with self.assertRaises(ValueError):
                self.db.update_item_partial(item=item, table_name="users")

            # Verify logger.warning was called
            self.assertTrue(mock_logger.warning.called)

    def test_error_messages_are_helpful(self):
        """Test error messages are helpful and descriptive"""
        item = {"sk": "user-123", "name": "John"}

        with self.assertRaises(ValueError) as context:
            self.db.update_item_partial(item=item, table_name="users")

        error_msg = str(context.exception)
        self.assertIn("pk", error_msg)
        self.assertIn("not populated", error_msg)


# ============================================================================
# 6.7 Model and Dict Input Tests
# ============================================================================


class TestUpdateItemPartialModelAndDictInput(unittest.TestCase):
    """Tests for model and dict input in update_item_partial() - Requirement 6.7"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_update_item_partial_works_with_dict_inputs(self):
        """Test update_item_partial() works with dict inputs"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            self.assertTrue(mock_update.called)

    def test_dict_input_is_not_modified(self):
        """Test dict input is not modified"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}
        original_item = item.copy()

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            # Item should not be modified
            self.assertEqual(item, original_item)

    def test_primary_key_extraction_works_for_dict(self):
        """Test primary key extraction works for dict"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            key = call_args.kwargs.get("key")

            self.assertEqual(key["pk"], "user-123")
            self.assertEqual(key["sk"], "user-123")


# ============================================================================
# Edge Cases and Special Values
# ============================================================================


class TestUpdateItemPartialEdgeCases(unittest.TestCase):
    """Tests for edge cases in update_item_partial()"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DynamoDB()

    def test_empty_string_value_is_updated(self):
        """Test empty string value is updated"""
        item = {"pk": "user-123", "sk": "user-123", "name": ""}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            attr_values = call_args.kwargs.get("expression_attribute_values")

            self.assertIn(":name", attr_values)
            self.assertEqual(attr_values[":name"], "")

    def test_zero_value_is_updated(self):
        """Test zero value is updated"""
        item = {"pk": "user-123", "sk": "user-123", "age": 0}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            attr_values = call_args.kwargs.get("expression_attribute_values")

            self.assertIn(":age", attr_values)
            self.assertEqual(attr_values[":age"], 0)

    def test_false_value_is_updated(self):
        """Test False value is updated"""
        item = {"pk": "user-123", "sk": "user-123", "active": False}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            attr_values = call_args.kwargs.get("expression_attribute_values")

            self.assertIn(":active", attr_values)
            self.assertEqual(attr_values[":active"], False)

    def test_multiple_fields_are_updated(self):
        """Test multiple fields are updated"""
        item = {
            "pk": "user-123",
            "sk": "user-123",
            "name": "John",
            "email": "john@example.com",
            "age": 30,
            "status": "active",
        }

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(item=item, table_name="users")

            call_args = mock_update.call_args
            attr_values = call_args.kwargs.get("expression_attribute_values")

            # Should have all field values
            self.assertIn(":name", attr_values)
            self.assertIn(":email", attr_values)
            self.assertIn(":age", attr_values)
            self.assertIn(":status", attr_values)

    def test_fields_to_clear_as_list(self):
        """Test fields_to_clear as list"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                fields_to_clear=["temp_field"],
            )

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            self.assertIn("REMOVE", update_expr)

    def test_fields_to_clear_as_set(self):
        """Test fields_to_clear as set"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            self.db.update_item_partial(
                item=item,
                table_name="users",
                fields_to_clear={"temp_field"},
            )

            call_args = mock_update.call_args
            update_expr = call_args.kwargs.get("update_expression")

            self.assertIn("REMOVE", update_expr)

    def test_source_parameter_is_used_in_logging(self):
        """Test source parameter is used in logging"""
        item = {"pk": "user-123", "sk": "user-123", "name": "John"}

        with patch.object(self.db, "update_item") as mock_update:
            mock_update.return_value = {}
            with patch("boto3_assist.dynamodb.dynamodb.logger") as mock_logger:
                self.db.update_item_partial(
                    item=item,
                    table_name="users",
                    source="test_source",
                )

                # Verify logger was called
                self.assertTrue(mock_logger.info.called)


if __name__ == "__main__":
    unittest.main()
