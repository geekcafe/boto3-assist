"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for DynamoDB update expressions
"""

import unittest
from moto import mock_aws
import boto3

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService


@mock_aws
class TestUpdateExpressionsSET(unittest.TestCase):
    """Tests for SET operation in update expressions"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_update_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_set_single_attribute(self):
        """Test SET operation for single attribute"""
        # Create item
        item = {
            "pk": "user#001",
            "sk": "user#001",
            "name": "Alice",
            "email": "alice@old.com"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update email
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#001", "sk": "user#001"},
            update_expression="SET email = :email",
            expression_attribute_values={":email": "alice@new.com"}
        )
        
        # Verify update
        response = self.db.get(
            key={"pk": "user#001", "sk": "user#001"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["email"], "alice@new.com")
        self.assertEqual(response["Item"]["name"], "Alice")  # Unchanged
    
    def test_set_multiple_attributes(self):
        """Test SET operation for multiple attributes"""
        # Create item
        item = {
            "pk": "user#002",
            "sk": "user#002",
            "name": "Bob",
            "age": 25,
            "city": "NYC"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update multiple attributes
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#002", "sk": "user#002"},
            update_expression="SET age = :age, city = :city",
            expression_attribute_values={":age": 26, ":city": "LA"}
        )
        
        # Verify updates
        response = self.db.get(
            key={"pk": "user#002", "sk": "user#002"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["age"], 26)
        self.assertEqual(response["Item"]["city"], "LA")
    
    def test_set_with_reserved_word(self):
        """Test SET operation with reserved keyword"""
        # Create item
        item = {
            "pk": "item#003",
            "sk": "item#003",
            "name": "Widget",
            "status": "pending"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update status (reserved word)
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "item#003", "sk": "item#003"},
            update_expression="SET #status = :status",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":status": "active"}
        )
        
        # Verify update
        response = self.db.get(
            key={"pk": "item#003", "sk": "item#003"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["status"], "active")
    
    def test_set_with_math_expression(self):
        """Test SET operation with mathematical expression"""
        # Create item with counter
        item = {
            "pk": "counter#004",
            "sk": "counter#004",
            "count": 10,
            "price": 100
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Increment count
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "counter#004", "sk": "counter#004"},
            update_expression="SET #count = #count + :inc, price = price - :discount",
            expression_attribute_names={"#count": "count"},
            expression_attribute_values={":inc": 5, ":discount": 10}
        )
        
        # Verify math operations
        response = self.db.get(
            key={"pk": "counter#004", "sk": "counter#004"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["count"], 15)
        self.assertEqual(response["Item"]["price"], 90)


@mock_aws
class TestUpdateExpressionsADD(unittest.TestCase):
    """Tests for ADD operation in update expressions"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_add_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_add_atomic_counter(self):
        """Test ADD operation for atomic counter"""
        # Create item with counter
        item = {
            "pk": "post#001",
            "sk": "post#001",
            "title": "My Post",
            "views": 0
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Increment views atomically
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "post#001", "sk": "post#001"},
            update_expression="ADD #views :inc",
            expression_attribute_names={"#views": "views"},
            expression_attribute_values={":inc": 1}
        )
        
        # Verify increment
        response = self.db.get(
            key={"pk": "post#001", "sk": "post#001"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["views"], 1)
        
        # Increment again
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "post#001", "sk": "post#001"},
            update_expression="ADD #views :inc",
            expression_attribute_names={"#views": "views"},
            expression_attribute_values={":inc": 5}
        )
        
        # Verify second increment
        response = self.db.get(
            key={"pk": "post#001", "sk": "post#001"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["views"], 6)
    
    def test_add_to_set(self):
        """Test ADD operation for adding to a set"""
        # Create item with set
        item = {
            "pk": "user#002",
            "sk": "user#002",
            "name": "Bob",
            "tags": {"premium"}
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Add to set
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#002", "sk": "user#002"},
            update_expression="ADD tags :new_tags",
            expression_attribute_values={":new_tags": {"verified", "admin"}}
        )
        
        # Verify set addition
        response = self.db.get(
            key={"pk": "user#002", "sk": "user#002"},
            table_name=self.table_name
        )
        self.assertIn("premium", response["Item"]["tags"])
        self.assertIn("verified", response["Item"]["tags"])
        self.assertIn("admin", response["Item"]["tags"])


@mock_aws
class TestUpdateExpressionsREMOVE(unittest.TestCase):
    """Tests for REMOVE operation in update expressions"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_remove_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_remove_attribute(self):
        """Test REMOVE operation to delete an attribute"""
        # Create item with temp field
        item = {
            "pk": "doc#001",
            "sk": "doc#001",
            "title": "Document",
            "temp_field": "temporary data",
            "status": "active"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Remove temp field
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "doc#001", "sk": "doc#001"},
            update_expression="REMOVE temp_field"
        )
        
        # Verify removal
        response = self.db.get(
            key={"pk": "doc#001", "sk": "doc#001"},
            table_name=self.table_name
        )
        self.assertNotIn("temp_field", response["Item"])
        self.assertIn("title", response["Item"])  # Other fields intact
    
    def test_remove_multiple_attributes(self):
        """Test REMOVE operation for multiple attributes"""
        # Create item
        item = {
            "pk": "user#002",
            "sk": "user#002",
            "name": "Alice",
            "temp1": "remove me",
            "temp2": "remove me too",
            "keep_me": "important"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Remove multiple fields
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#002", "sk": "user#002"},
            update_expression="REMOVE temp1, temp2"
        )
        
        # Verify removals
        response = self.db.get(
            key={"pk": "user#002", "sk": "user#002"},
            table_name=self.table_name
        )
        self.assertNotIn("temp1", response["Item"])
        self.assertNotIn("temp2", response["Item"])
        self.assertIn("keep_me", response["Item"])


@mock_aws
class TestUpdateExpressionsComplex(unittest.TestCase):
    """Tests for complex update expressions combining operations"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_complex_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_combined_set_and_add(self):
        """Test combining SET and ADD operations"""
        # Create item
        item = {
            "pk": "post#001",
            "sk": "post#001",
            "title": "My Post",
            "views": 10,
            "status": "draft"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update status and increment views
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "post#001", "sk": "post#001"},
            update_expression="SET #status = :status ADD #views :inc",
            expression_attribute_names={"#status": "status", "#views": "views"},
            expression_attribute_values={":status": "published", ":inc": 1}
        )
        
        # Verify both operations
        response = self.db.get(
            key={"pk": "post#001", "sk": "post#001"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["status"], "published")
        self.assertEqual(response["Item"]["views"], 11)
    
    def test_set_add_remove(self):
        """Test combining SET, ADD, and REMOVE"""
        # Create item
        item = {
            "pk": "item#002",
            "sk": "item#002",
            "name": "Widget",
            "count": 5,
            "temp_field": "delete this",
            "status": "pending"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Perform multiple operations
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "item#002", "sk": "item#002"},
            update_expression="SET #status = :status ADD #count :inc REMOVE temp_field",
            expression_attribute_names={"#status": "status", "#count": "count"},
            expression_attribute_values={":status": "active", ":inc": 3}
        )
        
        # Verify all operations
        response = self.db.get(
            key={"pk": "item#002", "sk": "item#002"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["status"], "active")
        self.assertEqual(response["Item"]["count"], 8)
        self.assertNotIn("temp_field", response["Item"])


@mock_aws
class TestUpdateExpressionsReturnValues(unittest.TestCase):
    """Tests for return_values parameter"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_return_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_return_all_new(self):
        """Test return_values='ALL_NEW' returns updated item"""
        # Create item
        item = {
            "pk": "user#001",
            "sk": "user#001",
            "name": "Alice",
            "age": 25
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update with return values
        response = self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#001", "sk": "user#001"},
            update_expression="SET age = :age",
            expression_attribute_values={":age": 26},
            return_values="ALL_NEW"
        )
        
        # Verify return value
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["age"], 26)
        self.assertEqual(response["Attributes"]["name"], "Alice")
    
    def test_return_all_old(self):
        """Test return_values='ALL_OLD' returns original item"""
        # Create item
        item = {
            "pk": "user#002",
            "sk": "user#002",
            "name": "Bob",
            "email": "bob@old.com"
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update with return old values
        response = self.db.update_item(
            table_name=self.table_name,
            key={"pk": "user#002", "sk": "user#002"},
            update_expression="SET email = :email",
            expression_attribute_values={":email": "bob@new.com"},
            return_values="ALL_OLD"
        )
        
        # Verify old values returned
        self.assertIn("Attributes", response)
        self.assertEqual(response["Attributes"]["email"], "bob@old.com")  # Old value


@mock_aws
class TestUpdateExpressionsConditional(unittest.TestCase):
    """Tests for conditional updates"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_conditional_update_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_conditional_update_success(self):
        """Test update succeeds when condition is met"""
        # Create item
        item = {
            "pk": "order#001",
            "sk": "order#001",
            "status": "pending",
            "total": 100
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Update with condition
        self.db.update_item(
            table_name=self.table_name,
            key={"pk": "order#001", "sk": "order#001"},
            update_expression="SET #status = :status",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":status": "shipped", ":pending": "pending"},
            condition_expression="#status = :pending"
        )
        
        # Verify update
        response = self.db.get(
            key={"pk": "order#001", "sk": "order#001"},
            table_name=self.table_name
        )
        self.assertEqual(response["Item"]["status"], "shipped")
    
    def test_conditional_update_failure(self):
        """Test update fails when condition is not met"""
        # Create item
        item = {
            "pk": "account#002",
            "sk": "account#002",
            "balance": 50
        }
        self.db.save(item=item, table_name=self.table_name)
        
        # Try to update with failing condition
        with self.assertRaises(RuntimeError) as context:
            self.db.update_item(
                table_name=self.table_name,
                key={"pk": "account#002", "sk": "account#002"},
                update_expression="SET balance = balance - :amount",
                expression_attribute_values={":amount": 100},
                condition_expression="balance >= :amount"
            )
        
        self.assertIn("Conditional check failed", str(context.exception))


def main():
    unittest.main()


if __name__ == "__main__":
    main()
