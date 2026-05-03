"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for PartialUpdateBuilder class
"""

import unittest

from boto3_assist.dynamodb.partial_update_builder import (
    PartialUpdateBuilder,
    UpdateExpressionComponents,
)


class TestUpdateExpressionComponents(unittest.TestCase):
    """Tests for UpdateExpressionComponents dataclass"""

    def test_create_components(self):
        """Test creating UpdateExpressionComponents"""
        components = UpdateExpressionComponents(
            update_expression="SET name = :name",
            expression_attribute_names={},
            expression_attribute_values={":name": "John"},
        )

        self.assertEqual(components.update_expression, "SET name = :name")
        self.assertEqual(components.expression_attribute_names, {})
        self.assertEqual(components.expression_attribute_values, {":name": "John"})

    def test_components_with_reserved_keywords(self):
        """Test components with reserved keyword mappings"""
        components = UpdateExpressionComponents(
            update_expression="SET #status = :status",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":status": "active"},
        )

        self.assertEqual(components.update_expression, "SET #status = :status")
        self.assertEqual(components.expression_attribute_names, {"#status": "status"})
        self.assertEqual(components.expression_attribute_values, {":status": "active"})


class TestPartialUpdateBuilderInit(unittest.TestCase):
    """Tests for PartialUpdateBuilder initialization"""

    def test_builder_initialization(self):
        """Test PartialUpdateBuilder initializes correctly"""
        builder = PartialUpdateBuilder()
        self.assertIsNotNone(builder.reserved_words)

    def test_builder_has_reserved_words_instance(self):
        """Test builder has DynamoDBReservedWords instance"""
        builder = PartialUpdateBuilder()
        self.assertTrue(hasattr(builder, "reserved_words"))
        self.assertTrue(hasattr(builder.reserved_words, "is_reserved_word"))


class TestSeparateOperations(unittest.TestCase):
    """Tests for _separate_operations() method"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = PartialUpdateBuilder()

    def test_separate_operations_with_non_none_values(self):
        """Test separating fields with non-None values"""
        fields = {"name": "John", "email": "john@example.com"}
        set_fields, remove_fields = self.builder._separate_operations(fields)

        self.assertEqual(set_fields, {"name": "John", "email": "john@example.com"})
        self.assertEqual(remove_fields, set())

    def test_separate_operations_excludes_none_values(self):
        """Test that None values are excluded from updates"""
        fields = {"name": "John", "email": None, "age": 30}
        set_fields, remove_fields = self.builder._separate_operations(fields)

        self.assertEqual(set_fields, {"name": "John", "age": 30})
        self.assertNotIn("email", set_fields)
        self.assertEqual(remove_fields, set())

    def test_separate_operations_with_empty_dict(self):
        """Test separating empty field dictionary"""
        fields = {}
        set_fields, remove_fields = self.builder._separate_operations(fields)

        self.assertEqual(set_fields, {})
        self.assertEqual(remove_fields, set())

    def test_separate_operations_with_all_none_values(self):
        """Test separating fields with all None values"""
        fields = {"name": None, "email": None, "age": None}
        set_fields, remove_fields = self.builder._separate_operations(fields)

        self.assertEqual(set_fields, {})
        self.assertEqual(remove_fields, set())

    def test_separate_operations_with_various_types(self):
        """Test separating fields with various data types"""
        fields = {
            "name": "John",
            "age": 30,
            "active": True,
            "balance": 100.50,
            "tags": ["tag1", "tag2"],
        }
        set_fields, remove_fields = self.builder._separate_operations(fields)

        self.assertEqual(len(set_fields), 5)
        self.assertEqual(set_fields["name"], "John")
        self.assertEqual(set_fields["age"], 30)
        self.assertEqual(set_fields["active"], True)
        self.assertEqual(set_fields["balance"], 100.50)
        self.assertEqual(set_fields["tags"], ["tag1", "tag2"])


class TestBuildSetClause(unittest.TestCase):
    """Tests for _build_set_clause() method"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = PartialUpdateBuilder()

    def test_build_set_clause_single_field(self):
        """Test building SET clause with single field"""
        fields = {"username": "John"}
        clause, names, values = self.builder._build_set_clause(fields)

        self.assertEqual(clause, "SET username = :username")
        self.assertEqual(names, {})
        self.assertEqual(values, {":username": "John"})

    def test_build_set_clause_multiple_fields(self):
        """Test building SET clause with multiple fields"""
        fields = {"name": "John", "email": "john@example.com", "age": 30}
        clause, names, values = self.builder._build_set_clause(fields)

        self.assertIn("SET", clause)
        self.assertIn("name = :name", clause)
        self.assertIn("email = :email", clause)
        self.assertIn("age = :age", clause)
        self.assertEqual(len(values), 3)
        self.assertEqual(values[":name"], "John")
        self.assertEqual(values[":email"], "john@example.com")
        self.assertEqual(values[":age"], 30)

    def test_build_set_clause_with_reserved_keyword(self):
        """Test building SET clause with reserved keyword"""
        fields = {"status": "active"}
        clause, names, values = self.builder._build_set_clause(fields)

        self.assertIn("SET", clause)
        self.assertIn("#status = :status", clause)
        self.assertEqual(names, {"#status": "status"})
        self.assertEqual(values, {":status": "active"})

    def test_build_set_clause_with_multiple_reserved_keywords(self):
        """Test building SET clause with multiple reserved keywords"""
        fields = {"status": "active", "name": "John", "type": "user"}
        clause, names, values = self.builder._build_set_clause(fields)

        self.assertIn("SET", clause)
        self.assertIn("#status = :status", clause)
        self.assertIn("#type = :type", clause)
        self.assertIn("#name = :name", clause)
        self.assertEqual(names["#status"], "status")
        self.assertEqual(names["#type"], "type")
        self.assertEqual(names["#name"], "name")

    def test_build_set_clause_mixed_reserved_and_non_reserved(self):
        """Test building SET clause with mix of reserved and non-reserved keywords"""
        fields = {"status": "active", "email": "john@example.com", "type": "user"}
        clause, names, values = self.builder._build_set_clause(fields)

        self.assertIn("SET", clause)
        self.assertEqual(len(names), 2)  # status and type are reserved
        self.assertEqual(len(values), 3)  # All three fields have values

    def test_build_set_clause_comma_separation(self):
        """Test that multiple fields are comma-separated"""
        fields = {"name": "John", "email": "john@example.com"}
        clause, names, values = self.builder._build_set_clause(fields)

        # Should have exactly one comma separating the two fields
        self.assertEqual(clause.count(","), 1)

    def test_build_set_clause_with_special_values(self):
        """Test building SET clause with special values"""
        fields = {"active": True, "count": 0, "balance": -100.50}
        clause, names, values = self.builder._build_set_clause(fields)

        self.assertEqual(values[":active"], True)
        self.assertEqual(values[":count"], 0)
        self.assertEqual(values[":balance"], -100.50)


class TestBuildRemoveClause(unittest.TestCase):
    """Tests for _build_remove_clause() method"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = PartialUpdateBuilder()

    def test_build_remove_clause_single_field(self):
        """Test building REMOVE clause with single field"""
        fields = {"temp_field"}
        clause, names = self.builder._build_remove_clause(fields)

        self.assertEqual(clause, "REMOVE temp_field")
        self.assertEqual(names, {})

    def test_build_remove_clause_multiple_fields(self):
        """Test building REMOVE clause with multiple fields"""
        fields = {"temp_field", "old_data", "deprecated"}
        clause, names = self.builder._build_remove_clause(fields)

        self.assertIn("REMOVE", clause)
        self.assertIn("temp_field", clause)
        self.assertIn("old_data", clause)
        self.assertIn("deprecated", clause)

    def test_build_remove_clause_with_reserved_keyword(self):
        """Test building REMOVE clause with reserved keyword"""
        fields = {"status"}
        clause, names = self.builder._build_remove_clause(fields)

        self.assertIn("REMOVE", clause)
        self.assertIn("#status", clause)
        self.assertEqual(names, {"#status": "status"})

    def test_build_remove_clause_with_multiple_reserved_keywords(self):
        """Test building REMOVE clause with multiple reserved keywords"""
        fields = {"status", "type", "name"}
        clause, names = self.builder._build_remove_clause(fields)

        self.assertIn("REMOVE", clause)
        # status, type, and name are all reserved
        self.assertEqual(len(names), 3)
        self.assertIn("#status", clause)
        self.assertIn("#type", clause)
        self.assertIn("#name", clause)

    def test_build_remove_clause_comma_separation(self):
        """Test that multiple fields are comma-separated"""
        fields = {"temp_field", "old_data"}
        clause, names = self.builder._build_remove_clause(fields)

        # Should have exactly one comma separating the two fields
        self.assertEqual(clause.count(","), 1)

    def test_build_remove_clause_empty_set(self):
        """Test building REMOVE clause with empty set"""
        fields = set()
        clause, names = self.builder._build_remove_clause(fields)

        # Should return empty string for empty set
        self.assertEqual(clause, "")
        self.assertEqual(names, {})


class TestPlaceholderGeneration(unittest.TestCase):
    """Tests for placeholder generation helper methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = PartialUpdateBuilder()

    def test_get_placeholder_name(self):
        """Test _get_placeholder_name() generates correct format"""
        placeholder = self.builder._get_placeholder_name("status")
        self.assertEqual(placeholder, "#status")

    def test_get_placeholder_name_various_fields(self):
        """Test _get_placeholder_name() with various field names"""
        self.assertEqual(self.builder._get_placeholder_name("name"), "#name")
        self.assertEqual(self.builder._get_placeholder_name("email"), "#email")
        self.assertEqual(self.builder._get_placeholder_name("user_id"), "#user_id")

    def test_get_placeholder_value(self):
        """Test _get_placeholder_value() generates correct format"""
        placeholder = self.builder._get_placeholder_value("status")
        self.assertEqual(placeholder, ":status")

    def test_get_placeholder_value_various_fields(self):
        """Test _get_placeholder_value() with various field names"""
        self.assertEqual(self.builder._get_placeholder_value("name"), ":name")
        self.assertEqual(self.builder._get_placeholder_value("email"), ":email")
        self.assertEqual(self.builder._get_placeholder_value("user_id"), ":user_id")


class TestBuildUpdateExpression(unittest.TestCase):
    """Tests for build_update_expression() method"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = PartialUpdateBuilder()

    def test_build_update_expression_set_only(self):
        """Test building update expression with SET operations only"""
        fields = {"name": "John", "email": "john@example.com"}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertIn("name = :name", components.update_expression)
        self.assertIn("email = :email", components.update_expression)
        self.assertEqual(len(components.expression_attribute_values), 2)

    def test_build_update_expression_with_reserved_keywords(self):
        """Test building update expression with reserved keywords"""
        fields = {"status": "active", "name": "John"}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertIn("#status = :status", components.update_expression)
        self.assertIn("name = :name", components.update_expression)
        self.assertEqual(components.expression_attribute_names["#status"], "status")

    def test_build_update_expression_excludes_none_values(self):
        """Test that None values are included in expression"""
        fields = {"username": "John", "email": None, "age": 30}
        components = self.builder.build_update_expression(fields)

        self.assertIn("username = :username", components.update_expression)
        self.assertIn("age = :age", components.update_expression)
        # None values are still included in the expression
        self.assertIn("email = :email", components.update_expression)
        self.assertEqual(len(components.expression_attribute_values), 3)

    def test_build_update_expression_empty_fields(self):
        """Test building update expression with empty fields"""
        fields = {}

        # Should raise ValueError when no fields to update
        with self.assertRaises(ValueError):
            self.builder.build_update_expression(fields)

    def test_build_update_expression_all_none_values(self):
        """Test building update expression with all None values"""
        fields = {"name": None, "email": None}
        components = self.builder.build_update_expression(fields)

        # None values are still included in the expression
        self.assertIn("#name = :name", components.update_expression)
        self.assertIn("email = :email", components.update_expression)
        self.assertEqual(len(components.expression_attribute_values), 2)

    def test_build_update_expression_returns_components(self):
        """Test that build_update_expression returns UpdateExpressionComponents"""
        fields = {"name": "John"}
        components = self.builder.build_update_expression(fields)

        self.assertIsInstance(components, UpdateExpressionComponents)
        self.assertTrue(hasattr(components, "update_expression"))
        self.assertTrue(hasattr(components, "expression_attribute_names"))
        self.assertTrue(hasattr(components, "expression_attribute_values"))

    def test_build_update_expression_multiple_reserved_keywords(self):
        """Test building expression with multiple reserved keywords"""
        fields = {"status": "active", "type": "user", "name": "John"}
        components = self.builder.build_update_expression(fields)

        self.assertIn("#status = :status", components.update_expression)
        self.assertIn("#type = :type", components.update_expression)
        self.assertIn("#name = :name", components.update_expression)
        self.assertEqual(len(components.expression_attribute_names), 3)

    def test_build_update_expression_with_various_data_types(self):
        """Test building expression with various data types"""
        fields = {
            "name": "John",
            "age": 30,
            "active": True,
            "balance": 100.50,
            "tags": ["tag1", "tag2"],
        }
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertEqual(len(components.expression_attribute_values), 5)
        self.assertEqual(components.expression_attribute_values[":name"], "John")
        self.assertEqual(components.expression_attribute_values[":age"], 30)
        self.assertEqual(components.expression_attribute_values[":active"], True)
        self.assertEqual(components.expression_attribute_values[":balance"], 100.50)
        self.assertEqual(components.expression_attribute_values[":tags"], ["tag1", "tag2"])

    def test_build_update_expression_single_field(self):
        """Test building expression with single field"""
        fields = {"username": "John"}
        components = self.builder.build_update_expression(fields)

        self.assertEqual(components.update_expression, "SET username = :username")
        self.assertEqual(components.expression_attribute_values, {":username": "John"})

    def test_build_update_expression_preserves_field_values(self):
        """Test that field values are preserved correctly"""
        fields = {"name": "John", "email": "john@example.com", "age": 30}
        components = self.builder.build_update_expression(fields)

        self.assertEqual(components.expression_attribute_values[":name"], "John")
        self.assertEqual(components.expression_attribute_values[":email"], "john@example.com")
        self.assertEqual(components.expression_attribute_values[":age"], 30)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and special scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = PartialUpdateBuilder()

    def test_field_with_empty_string_value(self):
        """Test handling field with empty string value"""
        fields = {"name": ""}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":name"], "")

    def test_field_with_zero_value(self):
        """Test handling field with zero value"""
        fields = {"count": 0}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":count"], 0)

    def test_field_with_false_value(self):
        """Test handling field with False value"""
        fields = {"active": False}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":active"], False)

    def test_field_with_empty_list(self):
        """Test handling field with empty list value"""
        fields = {"tags": []}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":tags"], [])

    def test_field_with_empty_dict(self):
        """Test handling field with empty dict value"""
        fields = {"metadata": {}}
        components = self.builder.build_update_expression(fields)

        self.assertIn("SET", components.update_expression)
        self.assertEqual(components.expression_attribute_values[":metadata"], {})

    def test_reserved_keyword_case_insensitive(self):
        """Test that reserved keyword detection is case-insensitive"""
        # DynamoDB reserved words are case-insensitive
        fields = {"STATUS": "active"}  # uppercase
        components = self.builder.build_update_expression(fields)

        # Should detect STATUS as reserved keyword (case-insensitive)
        self.assertIn("#STATUS", components.update_expression)
        self.assertEqual(components.expression_attribute_names["#STATUS"], "STATUS")


if __name__ == "__main__":
    unittest.main()
