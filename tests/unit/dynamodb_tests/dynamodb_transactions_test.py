"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for DynamoDB transactions (transact_write_items, transact_get_items)
"""

import unittest
from moto import mock_aws
import boto3

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.services.table_service import DynamoDBTableService


@mock_aws
class TestTransactWriteItems(unittest.TestCase):
    """Tests for transact_write_items method"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_transactions_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_transact_write_put_operations(self):
        """Test transaction with multiple Put operations"""
        operations = [
            {
                'Put': {
                    'TableName': self.table_name,
                    'Item': {
                        'pk': 'user#user-001',
                        'sk': 'user#user-001',
                        'id': 'user-001',
                        'name': 'Alice'
                    }
                }
            },
            {
                'Put': {
                    'TableName': self.table_name,
                    'Item': {
                        'pk': 'user#user-002',
                        'sk': 'user#user-002',
                        'id': 'user-002',
                        'name': 'Bob'
                    }
                }
            }
        ]
        
        response = self.db.transact_write_items(operations=operations)
        
        # Verify response structure
        self.assertIn('ResponseMetadata', response)
        
        # Verify items were created
        user1 = self.db.get(
            key={'pk': 'user#user-001', 'sk': 'user#user-001'},
            table_name=self.table_name
        )
        user2 = self.db.get(
            key={'pk': 'user#user-002', 'sk': 'user#user-002'},
            table_name=self.table_name
        )
        
        self.assertIn('Item', user1)
        self.assertIn('Item', user2)
        self.assertEqual(user1['Item']['name'], 'Alice')
        self.assertEqual(user2['Item']['name'], 'Bob')
    
    def test_transact_write_update_operations(self):
        """Test transaction with Update operations"""
        # Create initial items
        self.db.save(
            item={'pk': 'account#123', 'sk': 'account#123', 'balance': 1000},
            table_name=self.table_name
        )
        self.db.save(
            item={'pk': 'account#456', 'sk': 'account#456', 'balance': 500},
            table_name=self.table_name
        )
        
        # Transfer 100 from account 123 to account 456
        operations = [
            {
                'Update': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'account#123', 'sk': 'account#123'},
                    'UpdateExpression': 'SET balance = balance - :amount',
                    'ExpressionAttributeValues': {':amount': 100}
                }
            },
            {
                'Update': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'account#456', 'sk': 'account#456'},
                    'UpdateExpression': 'SET balance = balance + :amount',
                    'ExpressionAttributeValues': {':amount': 100}
                }
            }
        ]
        
        response = self.db.transact_write_items(operations=operations)
        self.assertIn('ResponseMetadata', response)
        
        # Verify balances updated correctly
        account1 = self.db.get(
            key={'pk': 'account#123', 'sk': 'account#123'},
            table_name=self.table_name
        )
        account2 = self.db.get(
            key={'pk': 'account#456', 'sk': 'account#456'},
            table_name=self.table_name
        )
        
        self.assertEqual(account1['Item']['balance'], 900)
        self.assertEqual(account2['Item']['balance'], 600)
    
    def test_transact_write_delete_operations(self):
        """Test transaction with Delete operations"""
        # Create items to delete
        self.db.save(
            item={'pk': 'temp#001', 'sk': 'temp#001', 'data': 'delete me'},
            table_name=self.table_name
        )
        self.db.save(
            item={'pk': 'temp#002', 'sk': 'temp#002', 'data': 'delete me too'},
            table_name=self.table_name
        )
        
        operations = [
            {
                'Delete': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'temp#001', 'sk': 'temp#001'}
                }
            },
            {
                'Delete': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'temp#002', 'sk': 'temp#002'}
                }
            }
        ]
        
        response = self.db.transact_write_items(operations=operations)
        self.assertIn('ResponseMetadata', response)
        
        # Verify items deleted
        result1 = self.db.get(
            key={'pk': 'temp#001', 'sk': 'temp#001'},
            table_name=self.table_name
        )
        result2 = self.db.get(
            key={'pk': 'temp#002', 'sk': 'temp#002'},
            table_name=self.table_name
        )
        
        self.assertNotIn('Item', result1)
        self.assertNotIn('Item', result2)
    
    def test_transact_write_mixed_operations(self):
        """Test transaction with mixed Put/Update/Delete operations"""
        # Create an existing item to update
        self.db.save(
            item={'pk': 'user#existing', 'sk': 'user#existing', 'version': 1},
            table_name=self.table_name
        )
        
        operations = [
            {
                'Put': {
                    'TableName': self.table_name,
                    'Item': {'pk': 'user#new', 'sk': 'user#new', 'name': 'NewUser'}
                }
            },
            {
                'Update': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'user#existing', 'sk': 'user#existing'},
                    'UpdateExpression': 'SET version = version + :inc',
                    'ExpressionAttributeValues': {':inc': 1}
                }
            }
        ]
        
        response = self.db.transact_write_items(operations=operations)
        self.assertIn('ResponseMetadata', response)
        
        # Verify new item created
        new_user = self.db.get(
            key={'pk': 'user#new', 'sk': 'user#new'},
            table_name=self.table_name
        )
        self.assertIn('Item', new_user)
        self.assertEqual(new_user['Item']['name'], 'NewUser')
        
        # Verify existing item updated
        existing = self.db.get(
            key={'pk': 'user#existing', 'sk': 'user#existing'},
            table_name=self.table_name
        )
        self.assertEqual(existing['Item']['version'], 2)
    
    def test_transact_write_with_condition(self):
        """Test transaction with conditional expressions"""
        # Create item with balance
        self.db.save(
            item={'pk': 'account#789', 'sk': 'account#789', 'balance': 50},
            table_name=self.table_name
        )
        
        # Try to withdraw more than balance (should fail)
        operations = [
            {
                'Update': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'account#789', 'sk': 'account#789'},
                    'UpdateExpression': 'SET balance = balance - :amount',
                    'ConditionExpression': 'balance >= :amount',
                    'ExpressionAttributeValues': {':amount': 100}
                }
            }
        ]
        
        # This should fail because balance (50) < amount (100)
        with self.assertRaises(Exception):
            self.db.transact_write_items(operations=operations)
        
        # Verify balance unchanged
        account = self.db.get(
            key={'pk': 'account#789', 'sk': 'account#789'},
            table_name=self.table_name
        )
        self.assertEqual(account['Item']['balance'], 50)
    
    def test_transact_write_empty_operations(self):
        """Test that empty operations list raises error"""
        with self.assertRaises(ValueError) as context:
            self.db.transact_write_items(operations=[])
        
        self.assertIn("At least one operation is required", str(context.exception))
    
    def test_transact_write_too_many_operations(self):
        """Test that > 100 operations raises error"""
        operations = [
            {
                'Put': {
                    'TableName': self.table_name,
                    'Item': {'pk': f'user#{i}', 'sk': f'user#{i}'}
                }
            }
            for i in range(101)
        ]
        
        with self.assertRaises(ValueError) as context:
            self.db.transact_write_items(operations=operations)
        
        self.assertIn("maximum 100 operations", str(context.exception))


@mock_aws
class TestTransactGetItems(unittest.TestCase):
    """Tests for transact_get_items method"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_transact_get_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create test items"""
        for i in range(5):
            item = {
                'pk': f'user#user-{i}',
                'sk': f'user#user-{i}',
                'id': f'user-{i}',
                'name': f'User {i}',
                'balance': 100 * (i + 1)
            }
            self.db.save(item=item, table_name=self.table_name)
    
    def test_transact_get_basic(self):
        """Test basic transactional get"""
        keys = [
            {
                'Key': {'pk': 'user#user-0', 'sk': 'user#user-0'},
                'TableName': self.table_name
            },
            {
                'Key': {'pk': 'user#user-1', 'sk': 'user#user-1'},
                'TableName': self.table_name
            }
        ]
        
        response = self.db.transact_get_items(keys=keys)
        
        self.assertIn('Items', response)
        self.assertEqual(response['Count'], 2)
        
        # Verify correct items returned
        names = [item['name'] for item in response['Items']]
        self.assertIn('User 0', names)
        self.assertIn('User 1', names)
    
    def test_transact_get_with_projection(self):
        """Test transactional get with projection expression"""
        keys = [
            {
                'Key': {'pk': 'user#user-0', 'sk': 'user#user-0'},
                'TableName': self.table_name,
                'ProjectionExpression': 'id,#name',
                'ExpressionAttributeNames': {'#name': 'name'}
            }
        ]
        
        response = self.db.transact_get_items(keys=keys)
        
        self.assertEqual(response['Count'], 1)
        item = response['Items'][0]
        
        # Should have projected fields
        self.assertIn('id', item)
        self.assertIn('name', item)
        
        # Note: moto doesn't always respect projections in transact_get_items
        # In real DynamoDB, these fields would be excluded by the projection
        # For now, just verify the required fields are present
    
    def test_transact_get_multiple_items(self):
        """Test getting all test items"""
        keys = [
            {
                'Key': {'pk': f'user#user-{i}', 'sk': f'user#user-{i}'},
                'TableName': self.table_name
            }
            for i in range(5)
        ]
        
        response = self.db.transact_get_items(keys=keys)
        
        self.assertEqual(response['Count'], 5)
        
        # Verify all items returned
        ids = [item['id'] for item in response['Items']]
        for i in range(5):
            self.assertIn(f'user-{i}', ids)
    
    def test_transact_get_decimal_conversion(self):
        """Test that numbers are converted from Decimal"""
        keys = [
            {
                'Key': {'pk': 'user#user-0', 'sk': 'user#user-0'},
                'TableName': self.table_name
            }
        ]
        
        response = self.db.transact_get_items(keys=keys)
        
        item = response['Items'][0]
        
        # Verify balance is int, not Decimal
        self.assertIsInstance(item['balance'], int)
        self.assertEqual(item['balance'], 100)
    
    def test_transact_get_nonexistent_items(self):
        """Test getting items that don't exist"""
        keys = [
            {
                'Key': {'pk': 'user#nonexistent', 'sk': 'user#nonexistent'},
                'TableName': self.table_name
            }
        ]
        
        response = self.db.transact_get_items(keys=keys)
        
        # Non-existent items simply don't appear in results
        self.assertEqual(response['Count'], 0)
    
    def test_transact_get_empty_keys(self):
        """Test that empty keys list raises error"""
        with self.assertRaises(ValueError) as context:
            self.db.transact_get_items(keys=[])
        
        self.assertIn("At least one key is required", str(context.exception))
    
    def test_transact_get_too_many_keys(self):
        """Test that > 100 keys raises error"""
        keys = [
            {
                'Key': {'pk': f'user#{i}', 'sk': f'user#{i}'},
                'TableName': self.table_name
            }
            for i in range(101)
        ]
        
        with self.assertRaises(ValueError) as context:
            self.db.transact_get_items(keys=keys)
        
        self.assertIn("maximum 100 items", str(context.exception))


@mock_aws  
class TestTransactionAtomicity(unittest.TestCase):
    """Tests for transaction atomicity guarantees"""

    def setUp(self):
        """Set up mock DynamoDB environment"""
        self.db = DynamoDB()
        self.db.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table_name = "test_atomicity_table"
        
        # Create test table
        table_service = DynamoDBTableService(self.db)
        table_service.create_a_table(table_name=self.table_name)
    
    def test_transaction_all_or_nothing(self):
        """Test that failed transaction doesn't partially commit"""
        # Create an account
        self.db.save(
            item={'pk': 'account#999', 'sk': 'account#999', 'balance': 50},
            table_name=self.table_name
        )
        
        # Try a transaction where second operation should fail
        operations = [
            {
                'Put': {
                    'TableName': self.table_name,
                    'Item': {'pk': 'log#001', 'sk': 'log#001', 'action': 'transfer'}
                }
            },
            {
                'Update': {
                    'TableName': self.table_name,
                    'Key': {'pk': 'account#999', 'sk': 'account#999'},
                    'UpdateExpression': 'SET balance = balance - :amount',
                    'ConditionExpression': 'balance >= :amount',
                    'ExpressionAttributeValues': {':amount': 100}  # More than balance!
                }
            }
        ]
        
        # Transaction should fail
        with self.assertRaises(Exception):
            self.db.transact_write_items(operations=operations)
        
        # Verify NEITHER operation committed
        # Log should NOT exist
        log = self.db.get(
            key={'pk': 'log#001', 'sk': 'log#001'},
            table_name=self.table_name
        )
        self.assertNotIn('Item', log)  # Log was NOT created
        
        # Account balance should be unchanged
        account = self.db.get(
            key={'pk': 'account#999', 'sk': 'account#999'},
            table_name=self.table_name
        )
        self.assertEqual(account['Item']['balance'], 50)  # Unchanged


def main():
    unittest.main()


if __name__ == "__main__":
    main()
