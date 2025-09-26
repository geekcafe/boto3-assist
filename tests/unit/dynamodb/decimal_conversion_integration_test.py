"""
Integration tests for DynamoDB decimal conversion functionality
"""

import unittest
from decimal import Decimal
from unittest.mock import Mock, patch
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase, DynamoDBSerializer
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.utilities.decimal_conversion_utility import DecimalConversionUtility


class ProductTestModel(DynamoDBModelBase):
    """Test model for decimal conversion testing"""
    
    def __init__(self):
        super().__init__()
        self.id: str = None
        self.name: str = None
        self.price: float = 0.0
        self.quantity: int = 0
        self.tax_rate: float = 0.0


class TestDynamoDBDecimalConversion(unittest.TestCase):
    """Integration tests for DynamoDB decimal conversion"""

    def setUp(self):
        """Set up test fixtures"""
        self.dynamodb = DynamoDB()
        self.dynamodb.convert_decimals = True  # Ensure conversion is enabled

    def test_model_map_with_decimal_conversion(self):
        """Test that model mapping converts Decimals to native types"""
        # Simulate DynamoDB response with Decimal values
        dynamodb_item = {
            'id': 'prod_123',
            'name': 'Test Product',
            'price': Decimal('19.99'),
            'quantity': Decimal('5'),
            'tax_rate': Decimal('0.08')
        }
        
        product = ProductTestModel()
        result = product.map(dynamodb_item)
        
        self.assertEqual(result.id, 'prod_123')
        self.assertEqual(result.name, 'Test Product')
        self.assertEqual(result.price, 19.99)
        self.assertIsInstance(result.price, float)
        self.assertEqual(result.quantity, 5)
        self.assertIsInstance(result.quantity, int)
        self.assertEqual(result.tax_rate, 0.08)
        self.assertIsInstance(result.tax_rate, float)

    def test_model_map_with_dynamodb_response_structure(self):
        """Test mapping with full DynamoDB response structure"""
        dynamodb_response = {
            'Item': {
                'id': 'prod_456',
                'name': 'Another Product',
                'price': Decimal('29.99'),
                'quantity': Decimal('10'),
                'tax_rate': Decimal('0.10')
            },
            'ResponseMetadata': {
                'RequestId': 'abc123',
                'HTTPStatusCode': 200
            }
        }
        
        product = ProductTestModel()
        result = product.map(dynamodb_response)
        
        self.assertEqual(result.id, 'prod_456')
        self.assertEqual(result.price, 29.99)
        self.assertIsInstance(result.price, float)
        self.assertEqual(result.quantity, 10)
        self.assertIsInstance(result.quantity, int)

    def test_unified_map_method_with_item_structure(self):
        """Test that the unified map() method handles DynamoDB Item structures"""
        dynamodb_response = {
            'Item': {
                'id': 'prod_789',
                'name': 'Serializer Test Product',
                'price': Decimal('39.99'),
                'quantity': Decimal('15')
            }
        }
        
        product = ProductTestModel()
        result = product.map(dynamodb_response)
        
        self.assertEqual(result.id, 'prod_789')
        self.assertEqual(result.price, 39.99)
        self.assertIsInstance(result.price, float)
        self.assertEqual(result.quantity, 15)
        self.assertIsInstance(result.quantity, int)

    def test_dynamodb_apply_decimal_conversion(self):
        """Test the DynamoDB _apply_decimal_conversion method"""
        response_with_decimals = {
            'Item': {
                'price': Decimal('49.99'),
                'quantity': Decimal('20')
            },
            'Count': 1
        }
        
        result = self.dynamodb._apply_decimal_conversion(response_with_decimals)
        
        expected = {
            'Item': {
                'price': 49.99,
                'quantity': 20
            },
            'Count': 1
        }
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result['Item']['price'], float)
        self.assertIsInstance(result['Item']['quantity'], int)

    def test_dynamodb_conversion_disabled(self):
        """Test that conversion can be disabled"""
        self.dynamodb.convert_decimals = False
        
        response_with_decimals = {
            'Item': {
                'price': Decimal('49.99'),
                'quantity': Decimal('20')
            }
        }
        
        result = self.dynamodb._apply_decimal_conversion(response_with_decimals)
        
        # Should return unchanged when conversion is disabled
        self.assertEqual(result, response_with_decimals)
        self.assertIsInstance(result['Item']['price'], Decimal)
        self.assertIsInstance(result['Item']['quantity'], Decimal)

    @patch('boto3_assist.dynamodb.dynamodb.DynamoDB.dynamodb_resource')
    def test_get_method_applies_decimal_conversion(self, mock_resource):
        """Test that the get method applies decimal conversion to responses"""
        # Mock the DynamoDB table response
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test_id',
                'price': Decimal('99.99'),
                'quantity': Decimal('3')
            }
        }
        
        result = self.dynamodb.get(
            key={'id': 'test_id'},
            table_name='test_table'
        )
        
        # Verify decimal conversion was applied
        self.assertEqual(result['Item']['price'], 99.99)
        self.assertIsInstance(result['Item']['price'], float)
        self.assertEqual(result['Item']['quantity'], 3)
        self.assertIsInstance(result['Item']['quantity'], int)

    @patch('boto3_assist.dynamodb.dynamodb.DynamoDB.dynamodb_resource')
    def test_query_method_applies_decimal_conversion(self, mock_resource):
        """Test that the query method applies decimal conversion to responses"""
        # Mock the DynamoDB table response
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_table.query.return_value = {
            'Items': [
                {
                    'id': 'item1',
                    'price': Decimal('19.99'),
                    'quantity': Decimal('2')
                },
                {
                    'id': 'item2',
                    'price': Decimal('29.99'),
                    'quantity': Decimal('1')
                }
            ],
            'Count': 2
        }
        
        from boto3.dynamodb.conditions import Key
        result = self.dynamodb.query(
            key=Key('pk').eq('test'),
            table_name='test_table'
        )
        
        # Verify decimal conversion was applied to all items
        self.assertEqual(len(result['Items']), 2)
        
        for item in result['Items']:
            self.assertIsInstance(item['price'], float)
            self.assertIsInstance(item['quantity'], int)
        
        self.assertEqual(result['Items'][0]['price'], 19.99)
        self.assertEqual(result['Items'][0]['quantity'], 2)
        self.assertEqual(result['Items'][1]['price'], 29.99)
        self.assertEqual(result['Items'][1]['quantity'], 1)

    def test_nested_decimal_conversion_in_complex_structure(self):
        """Test decimal conversion in complex nested structures"""
        complex_response = {
            'Items': [
                {
                    'order_id': 'order_123',
                    'total': Decimal('199.99'),
                    'items': [
                        {
                            'product_id': 'prod_1',
                            'price': Decimal('99.99'),
                            'quantity': Decimal('1')
                        },
                        {
                            'product_id': 'prod_2',
                            'price': Decimal('49.99'),
                            'quantity': Decimal('2')
                        }
                    ],
                    'metadata': {
                        'tax': Decimal('16.00'),
                        'shipping': Decimal('9.99')
                    }
                }
            ]
        }
        
        result = self.dynamodb._apply_decimal_conversion(complex_response)
        
        # Verify all nested Decimals were converted
        order = result['Items'][0]
        self.assertIsInstance(order['total'], float)
        self.assertEqual(order['total'], 199.99)
        
        # Check nested items
        for item in order['items']:
            self.assertIsInstance(item['price'], float)
            self.assertIsInstance(item['quantity'], int)
        
        # Check nested metadata
        self.assertIsInstance(order['metadata']['tax'], int)  # 16.00 becomes int(16)
        self.assertIsInstance(order['metadata']['shipping'], float)  # 9.99 stays float
        self.assertEqual(order['metadata']['tax'], 16)
        self.assertEqual(order['metadata']['shipping'], 9.99)

    def test_error_response_handling(self):
        """Test that error responses are handled correctly"""
        error_response = {
            'exception': 'Some error occurred'
        }
        
        result = self.dynamodb._apply_decimal_conversion(error_response)
        
        # Error responses should pass through unchanged
        self.assertEqual(result, error_response)

    def test_environment_variable_configuration(self):
        """Test that decimal conversion can be configured via environment variable"""
        # Mock only the specific environment variable we care about
        with patch('os.getenv') as mock_getenv:
            def side_effect(key, default=None):
                if key == 'DYNAMODB_CONVERT_DECIMALS':
                    return 'False'
                elif key == 'LOG_LEVEL':
                    return 'INFO'  # Return a valid log level
                else:
                    return default
            
            mock_getenv.side_effect = side_effect
            
            # Create new instance to pick up the environment variable
            dynamodb = DynamoDB()
            
            # Verify conversion is disabled
            self.assertFalse(dynamodb.convert_decimals)


if __name__ == '__main__':
    unittest.main()
