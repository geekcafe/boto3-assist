"""
Unit tests for DecimalConversionUtility
"""

import unittest
from decimal import Decimal
from boto3_assist.utilities.decimal_conversion_utility import DecimalConversionUtility


class TestDecimalConversionUtility(unittest.TestCase):
    """Test cases for DecimalConversionUtility"""

    def test_convert_decimals_to_native_types_simple_decimal(self):
        """Test converting a simple Decimal to native type"""
        # Test whole number conversion to int
        result = DecimalConversionUtility.convert_decimals_to_native_types(Decimal('42'))
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

        # Test decimal number conversion to float
        result = DecimalConversionUtility.convert_decimals_to_native_types(Decimal('3.14'))
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)

    def test_convert_decimals_to_native_types_dict(self):
        """Test converting Decimals in a dictionary"""
        input_dict = {
            'price': Decimal('19.99'),
            'quantity': Decimal('5'),
            'name': 'Product A',
            'active': True
        }
        
        result = DecimalConversionUtility.convert_decimals_to_native_types(input_dict)
        
        expected = {
            'price': 19.99,
            'quantity': 5,
            'name': 'Product A',
            'active': True
        }
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result['price'], float)
        self.assertIsInstance(result['quantity'], int)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['active'], bool)

    def test_convert_decimals_to_native_types_list(self):
        """Test converting Decimals in a list"""
        input_list = [Decimal('1.5'), Decimal('2'), 'text', True, None]
        
        result = DecimalConversionUtility.convert_decimals_to_native_types(input_list)
        
        expected = [1.5, 2, 'text', True, None]
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result[0], float)
        self.assertIsInstance(result[1], int)

    def test_convert_decimals_to_native_types_nested_structure(self):
        """Test converting Decimals in nested data structures"""
        input_data = {
            'order': {
                'total': Decimal('99.99'),
                'items': [
                    {'price': Decimal('29.99'), 'qty': Decimal('2')},
                    {'price': Decimal('39.99'), 'qty': Decimal('1')}
                ]
            },
            'customer_id': 'cust_123'
        }
        
        result = DecimalConversionUtility.convert_decimals_to_native_types(input_data)
        
        expected = {
            'order': {
                'total': 99.99,
                'items': [
                    {'price': 29.99, 'qty': 2},
                    {'price': 39.99, 'qty': 1}
                ]
            },
            'customer_id': 'cust_123'
        }
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result['order']['total'], float)
        self.assertIsInstance(result['order']['items'][0]['qty'], int)

    def test_convert_native_types_to_decimals_simple_types(self):
        """Test converting native types to Decimals"""
        # Test int conversion
        result = DecimalConversionUtility.convert_native_types_to_decimals(42)
        self.assertEqual(result, Decimal('42'))
        self.assertIsInstance(result, Decimal)

        # Test float conversion
        result = DecimalConversionUtility.convert_native_types_to_decimals(3.14)
        self.assertEqual(result, Decimal('3.14'))
        self.assertIsInstance(result, Decimal)

        # Test non-numeric types remain unchanged
        result = DecimalConversionUtility.convert_native_types_to_decimals('text')
        self.assertEqual(result, 'text')
        self.assertIsInstance(result, str)

    def test_convert_native_types_to_decimals_dict(self):
        """Test converting native types to Decimals in a dictionary"""
        input_dict = {
            'price': 19.99,
            'quantity': 5,
            'name': 'Product A',
            'active': True
        }
        
        result = DecimalConversionUtility.convert_native_types_to_decimals(input_dict)
        
        expected = {
            'price': Decimal('19.99'),
            'quantity': Decimal('5'),
            'name': 'Product A',
            'active': True
        }
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result['price'], Decimal)
        self.assertIsInstance(result['quantity'], Decimal)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['active'], bool)

    def test_convert_native_types_to_decimals_list(self):
        """Test converting native types to Decimals in a list"""
        input_list = [1.5, 2, 'text', True, None]
        
        result = DecimalConversionUtility.convert_native_types_to_decimals(input_list)
        
        expected = [Decimal('1.5'), Decimal('2'), 'text', True, None]
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result[0], Decimal)
        self.assertIsInstance(result[1], Decimal)

    def test_is_numeric_type(self):
        """Test numeric type detection"""
        self.assertTrue(DecimalConversionUtility.is_numeric_type(42))
        self.assertTrue(DecimalConversionUtility.is_numeric_type(3.14))
        self.assertTrue(DecimalConversionUtility.is_numeric_type(Decimal('19.99')))
        
        self.assertFalse(DecimalConversionUtility.is_numeric_type('text'))
        self.assertFalse(DecimalConversionUtility.is_numeric_type(True))
        self.assertFalse(DecimalConversionUtility.is_numeric_type(None))
        self.assertFalse(DecimalConversionUtility.is_numeric_type([]))
        self.assertFalse(DecimalConversionUtility.is_numeric_type({}))

    def test_safe_decimal_conversion_success(self):
        """Test successful safe decimal conversion"""
        # Test with int
        result = DecimalConversionUtility.safe_decimal_conversion(42)
        self.assertEqual(result, Decimal('42'))
        
        # Test with float
        result = DecimalConversionUtility.safe_decimal_conversion(3.14)
        self.assertEqual(result, Decimal('3.14'))
        
        # Test with string
        result = DecimalConversionUtility.safe_decimal_conversion('19.99')
        self.assertEqual(result, Decimal('19.99'))
        
        # Test with existing Decimal
        decimal_val = Decimal('99.99')
        result = DecimalConversionUtility.safe_decimal_conversion(decimal_val)
        self.assertEqual(result, decimal_val)

    def test_safe_decimal_conversion_failure(self):
        """Test safe decimal conversion with invalid inputs"""
        # Test with invalid string
        result = DecimalConversionUtility.safe_decimal_conversion('invalid', 'default')
        self.assertEqual(result, 'default')
        
        # Test with None and no default
        result = DecimalConversionUtility.safe_decimal_conversion(None)
        self.assertIsNone(result)
        
        # Test with list
        result = DecimalConversionUtility.safe_decimal_conversion([1, 2, 3], 'default')
        self.assertEqual(result, 'default')

    def test_format_decimal_for_display(self):
        """Test decimal formatting for display"""
        # Test with Decimal
        result = DecimalConversionUtility.format_decimal_for_display(Decimal('19.99'))
        self.assertEqual(result, '19.99')
        
        # Test with custom precision
        result = DecimalConversionUtility.format_decimal_for_display(Decimal('19.999'), precision=3)
        self.assertEqual(result, '19.999')
        
        # Test with non-Decimal input
        result = DecimalConversionUtility.format_decimal_for_display(19.99)
        self.assertEqual(result, '19.99')
        
        # Test with integer precision
        result = DecimalConversionUtility.format_decimal_for_display(Decimal('19'), precision=0)
        self.assertEqual(result, '19')

    def test_round_trip_conversion(self):
        """Test that converting to decimals and back preserves data integrity"""
        original_data = {
            'prices': [19.99, 29.99, 39.99],
            'quantities': [1, 2, 3],
            'metadata': {
                'total': 149.95,
                'tax': 12.00
            }
        }
        
        # Convert to decimals
        decimal_data = DecimalConversionUtility.convert_native_types_to_decimals(original_data)
        
        # Convert back to native types
        result_data = DecimalConversionUtility.convert_decimals_to_native_types(decimal_data)
        
        self.assertEqual(result_data, original_data)

    def test_dynamodb_response_structure(self):
        """Test conversion with typical DynamoDB response structure"""
        dynamodb_response = {
            'Item': {
                'pk': 'order#123',
                'sk': 'order#123',
                'total': Decimal('99.99'),
                'tax': Decimal('8.00'),
                'quantity': Decimal('3'),
                'created_at': '2023-01-01T00:00:00Z',
                'active': True
            },
            'ResponseMetadata': {
                'RequestId': 'abc123',
                'HTTPStatusCode': 200
            }
        }
        
        result = DecimalConversionUtility.convert_decimals_to_native_types(dynamodb_response)
        
        expected = {
            'Item': {
                'pk': 'order#123',
                'sk': 'order#123',
                'total': 99.99,
                'tax': 8.00,
                'quantity': 3,
                'created_at': '2023-01-01T00:00:00Z',
                'active': True
            },
            'ResponseMetadata': {
                'RequestId': 'abc123',
                'HTTPStatusCode': 200
            }
        }
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result['Item']['total'], float)
        self.assertIsInstance(result['Item']['quantity'], int)


if __name__ == '__main__':
    unittest.main()
