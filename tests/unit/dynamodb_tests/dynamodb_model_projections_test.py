"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest


from tests.unit.dynamodb_tests.db_models.user_model import User
from tests.unit.dynamodb_tests.db_models.simple_model import Simple


class DynamoDBModeProjectionUnitTest(unittest.TestCase):
    "Serialization Tests"

    def test_projection_expressions_transformation(self):
        """Test Basic Serialization"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
            "status": "active",
        }

        # Act
        model: User = User().map(data)

        # Assert

        self.assertEqual(model.first_name, "John")
        self.assertEqual(model.age, 30)
        self.assertEqual(model.email, "john@example.com")
        self.assertIsInstance(model, User)

        key = model.indexes.primary.key()
        self.assertIsInstance(key, dict)

        expressions = model.projection_expression
        self.assertIsInstance(expressions, str)

        self.assertIn("#status", expressions)

        print(expressions)

        attribute_names = model.projection_expression_attribute_names
        self.assertIsInstance(attribute_names, dict)

        self.assertIn("#status", attribute_names)

        self.assertIn("status", attribute_names["#status"])

    def test_simple_model(self):
        """Test Basic Serialization"""
        # Arrange
        data = {
            "id": "123456",
        }

        # Act
        model: Simple = Simple().map(data)

        # Assert

        self.assertEqual(model.id, "123456")

        self.assertIsInstance(model, Simple)

        key = model.indexes.primary.key()
        self.assertIsInstance(key, dict)

        expressions = model.projection_expression
        self.assertIsInstance(expressions, str)

        self.assertIn("id", expressions)

        print(expressions)

        attribute_names = model.projection_expression_attribute_names
        self.assertIsNone(attribute_names)

    def test_user_model_and_nulls(self):
        """Test nulls"""
        model: User = User()
        model.first_name = "John"

        expressions = model.projection_expression
        self.assertIsInstance(expressions, str)

        self.assertIn("id", expressions)

    def test_user_limited_projections(self):
        """Test limited projections"""
        model: User = User()
        model.first_name = "John"

        model.projection_expression = "id"
        model.projection_expression_attribute_names = None
        model.auto_generate_projections = False
        expressions = model.projection_expression
        attributes = model.projection_expression_attribute_names
        self.assertIsInstance(expressions, str)

        self.assertIn("id", expressions)
        self.assertNotIn("first_name", expressions)
        self.assertNotIn("age", expressions)
        self.assertNotIn("email", expressions)
        self.assertNotIn("status", expressions)
        self.assertIsNone(attributes)

    def test_user_limited_reserved_projections(self):
        """Test reserved word addition."""
        model: User = User()
        model.first_name = "John"

        model.projection_expression = "id,status"
        # model.projection_expression_attribute_names = None
        model.auto_generate_projections = False
        expressions = model.projection_expression
        attributes = model.projection_expression_attribute_names
        self.assertIsInstance(expressions, str)

        self.assertIn("id", expressions)
        self.assertNotIn("first_name", expressions)
        self.assertNotIn("age", expressions)
        self.assertNotIn("email", expressions)
        self.assertIn("#status", expressions)
        # self.assertIsNone(attributes)
        self.assertIn("#status", attributes)
