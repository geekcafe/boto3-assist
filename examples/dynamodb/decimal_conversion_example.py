"""
DynamoDB Decimal Conversion Example

This example demonstrates how the boto3-assist library handles decimal conversion
between DynamoDB's Decimal types and Python's native int/float types.
"""

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase, DynamoDBSerializer
from boto3_assist.utilities.decimal_conversion_utility import DecimalConversionUtility
from boto3_assist.utilities.serialization_utility import JsonEncoder
# from examples.dynamodb.models.product_model import Product


class Product(DynamoDBModelBase):
    """Simple Product model for demonstration"""
    
    def __init__(self):
        super().__init__()
        self.id: str = None
        self.name: str = None
        self.price: float = 0.0
        self.cost: float = 0.0
        self.tax_rate: float = 0.0
        self.weight: float = 0.0
        self.sku: str = None


class DecimalConversionExample:
    """Example demonstrating decimal conversion functionality"""

    def __init__(self):
        self.db = DynamoDB()
        # Ensure decimal conversion is enabled (this is the default)
        self.db.convert_decimals = True

    def demonstrate_decimal_conversion_utility(self):
        """Demonstrate the DecimalConversionUtility functions"""
        print("=" * 60)
        print("DECIMAL CONVERSION UTILITY DEMONSTRATION")
        print("=" * 60)

        # Example 1: Converting Decimals to native types
        print("\n1. Converting DynamoDB Decimals to native Python types:")
        dynamodb_data = {
            'product_id': 'prod_123',
            'name': 'Test Product',
            'price': Decimal('19.99'),
            'quantity': Decimal('5'),
            'tax_rate': Decimal('0.08'),
            'weight': Decimal('2.5'),
            'active': True
        }
        
        print(f"Original DynamoDB data (with Decimals):")
        for key, value in dynamodb_data.items():
            print(f"  {key}: {value} ({type(value).__name__})")

        converted_data = DecimalConversionUtility.convert_decimals_to_native_types(dynamodb_data)
        
        print(f"\nConverted to native Python types:")
        for key, value in converted_data.items():
            print(f"  {key}: {value} ({type(value).__name__})")

        # Example 2: Converting native types to Decimals
        print("\n2. Converting native Python types to Decimals (for DynamoDB storage):")
        python_data = {
            'product_id': 'prod_456',
            'name': 'Another Product',
            'price': 29.99,
            'quantity': 10,
            'tax_rate': 0.10,
            'weight': 3.7,
            'active': True
        }

        print(f"Original Python data (native types):")
        for key, value in python_data.items():
            print(f"  {key}: {value} ({type(value).__name__})")

        decimal_data = DecimalConversionUtility.convert_native_types_to_decimals(python_data)
        
        print(f"\nConverted to Decimals (for DynamoDB):")
        for key, value in decimal_data.items():
            print(f"  {key}: {value} ({type(value).__name__})")

        # Example 3: Nested data structures
        print("\n3. Converting nested data structures:")
        nested_data = {
            'order': {
                'id': 'order_789',
                'total': Decimal('99.99'),
                'items': [
                    {'price': Decimal('29.99'), 'qty': Decimal('2')},
                    {'price': Decimal('39.99'), 'qty': Decimal('1')}
                ]
            },
            'metadata': {
                'tax': Decimal('8.00'),
                'shipping': Decimal('9.99')
            }
        }

        converted_nested = DecimalConversionUtility.convert_decimals_to_native_types(nested_data)
        
        print("Nested structure conversion:")
        print(json.dumps(converted_nested, indent=2, cls=JsonEncoder))

    def demonstrate_model_decimal_conversion(self):
        """Demonstrate decimal conversion with DynamoDB models"""
        print("\n" + "=" * 60)
        print("MODEL DECIMAL CONVERSION DEMONSTRATION")
        print("=" * 60)

        # Simulate a DynamoDB response with Decimal values
        simulated_dynamodb_response = {
            'Item': {
                'id': 'prod_999',
                'name': 'Decimal Test Product',
                'price': Decimal('49.99'),
                'cost': Decimal('25.00'),
                'tax_rate': Decimal('0.085'),
                'weight': Decimal('1.2'),
                'sku': 'DECIMAL001'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 200
            }
        }

        print("1. Simulated DynamoDB response (with Decimals):")
        print(json.dumps(simulated_dynamodb_response, indent=2, cls=JsonEncoder))

        # Map to Product model - decimal conversion happens automatically
        product = Product()
        mapped_product = product.map(simulated_dynamodb_response)

        print(f"\n2. Mapped to Product model (Decimals converted to native types):")
        print(f"  ID: {mapped_product.id}")
        print(f"  Name: {mapped_product.name}")
        print(f"  Price: {mapped_product.price} ({type(mapped_product.price).__name__})")
        print(f"  Cost: {mapped_product.cost} ({type(mapped_product.cost).__name__})")
        print(f"  Tax Rate: {mapped_product.tax_rate} ({type(mapped_product.tax_rate).__name__})")
        print(f"  Weight: {mapped_product.weight} ({type(mapped_product.weight).__name__})")

        # Demonstrate that the unified map() method handles all DynamoDB response structures
        print(f"\n3. Using unified map() method with Item structure:")
        item_only_response = {
            'Item': {
                'id': 'prod_888',
                'name': 'Item Structure Test',
                'price': Decimal('59.99'),
                'cost': Decimal('30.00')
            }
        }
        
        another_product = Product()
        unified_mapped = another_product.map(item_only_response)
        
        print(f"  Price: {unified_mapped.price} ({type(unified_mapped.price).__name__})")
        print(f"  Cost: {unified_mapped.cost} ({type(unified_mapped.cost).__name__})")

    def demonstrate_dynamodb_integration(self):
        """Demonstrate decimal conversion in DynamoDB operations"""
        print("\n" + "=" * 60)
        print("DYNAMODB INTEGRATION DEMONSTRATION")
        print("=" * 60)

        # Simulate DynamoDB get response
        print("1. Simulating DynamoDB get() response with decimal conversion:")
        
        # This would normally come from an actual DynamoDB call
        mock_get_response = {
            'Item': {
                'pk': 'product#123',
                'sk': 'product#123',
                'name': 'Mock Product',
                'price': Decimal('79.99'),
                'cost': Decimal('40.00'),
                'tax_rate': Decimal('0.09'),
                'weight': Decimal('5.5')
            }
        }

        # Apply decimal conversion (this happens automatically in the DynamoDB class)
        converted_response = self.db._apply_decimal_conversion(mock_get_response)
        
        print("Original response (with Decimals):")
        print(json.dumps(mock_get_response, indent=2, cls=JsonEncoder))
        
        print("\nAfter decimal conversion:")
        print(json.dumps(converted_response, indent=2))

        # Demonstrate conversion toggle
        print("\n2. Demonstrating conversion toggle:")
        self.db.convert_decimals = False
        no_conversion_response = self.db._apply_decimal_conversion(mock_get_response)
        
        print("With conversion disabled (Decimals preserved):")
        print(json.dumps(no_conversion_response, indent=2, cls=JsonEncoder))
        
        # Re-enable conversion
        self.db.convert_decimals = True

    def demonstrate_safe_decimal_conversion(self):
        """Demonstrate safe decimal conversion with error handling"""
        print("\n" + "=" * 60)
        print("SAFE DECIMAL CONVERSION DEMONSTRATION")
        print("=" * 60)

        test_values = [
            42,           # int
            3.14,         # float
            "19.99",      # valid string
            "invalid",    # invalid string
            None,         # None
            [1, 2, 3],    # list (invalid)
            Decimal('99.99')  # existing Decimal
        ]

        print("Testing safe decimal conversion with various inputs:")
        for value in test_values:
            result = DecimalConversionUtility.safe_decimal_conversion(value, "DEFAULT")
            print(f"  Input: {value} ({type(value).__name__}) -> Result: {result} ({type(result).__name__})")

    def demonstrate_formatting(self):
        """Demonstrate decimal formatting for display"""
        print("\n" + "=" * 60)
        print("DECIMAL FORMATTING DEMONSTRATION")
        print("=" * 60)

        test_decimals = [
            Decimal('19.99'),
            Decimal('19.999'),
            Decimal('19'),
            19.99,  # Will be converted to Decimal first
        ]

        print("Formatting decimals for display:")
        for decimal_val in test_decimals:
            formatted_2 = DecimalConversionUtility.format_decimal_for_display(decimal_val, precision=2)
            formatted_3 = DecimalConversionUtility.format_decimal_for_display(decimal_val, precision=3)
            print(f"  {decimal_val} -> 2 decimals: {formatted_2}, 3 decimals: {formatted_3}")

    def run_all_examples(self):
        """Run all decimal conversion examples"""
        print("BOTO3-ASSIST DECIMAL CONVERSION EXAMPLES")
        print("This example demonstrates how boto3-assist handles decimal conversion")
        print("between DynamoDB's Decimal types and Python's native numeric types.")
        
        self.demonstrate_decimal_conversion_utility()
        self.demonstrate_model_decimal_conversion()
        self.demonstrate_dynamodb_integration()
        self.demonstrate_safe_decimal_conversion()
        self.demonstrate_formatting()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("✓ Decimal conversion utility functions work correctly")
        print("✓ Unified map() method handles all DynamoDB response structures")
        print("✓ Model mapping automatically converts Decimals to native types")
        print("✓ DynamoDB operations apply decimal conversion by default")
        print("✓ Conversion can be disabled via environment variable or property")
        print("✓ Safe conversion handles invalid inputs gracefully")
        print("✓ Formatting utilities provide display-ready strings")
        print("\nDecimal conversion is now seamlessly integrated into boto3-assist!")
        print("All mapping uses the consistent map() method - no confusion with multiple methods!")


def main():
    """Main function to run the decimal conversion example"""
    example = DecimalConversionExample()
    example.run_all_examples()


if __name__ == "__main__":
    main()
