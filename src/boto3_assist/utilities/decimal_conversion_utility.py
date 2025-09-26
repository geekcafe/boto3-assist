"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from decimal import Decimal
from typing import Any, Dict, List, Union


class DecimalConversionUtility:
    """
    Utility class for handling decimal conversions between Python types and DynamoDB.
    
    DynamoDB stores all numbers as Decimal types, but Python applications often
    expect int or float types. This utility provides conversion methods to handle
    the transformation seamlessly.
    """

    @staticmethod
    def convert_decimals_to_native_types(data: Any) -> Any:
        """
        Recursively converts Decimal objects to native Python types (int or float).
        
        This is typically used when deserializing data from DynamoDB, where all
        numbers are stored as Decimal objects but the application expects native
        Python numeric types.
        
        Args:
            data: The data structure to convert. Can be dict, list, or any other type.
            
        Returns:
            The data structure with Decimal objects converted to int or float.
        """
        if isinstance(data, dict):
            return {
                key: DecimalConversionUtility.convert_decimals_to_native_types(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                DecimalConversionUtility.convert_decimals_to_native_types(item)
                for item in data
            ]
        elif isinstance(data, Decimal):
            # Convert Decimal to int if it's a whole number, otherwise to float
            if data % 1 == 0:
                return int(data)
            else:
                return float(data)
        else:
            return data

    @staticmethod
    def convert_native_types_to_decimals(data: Any) -> Any:
        """
        Recursively converts native Python numeric types (int, float) to Decimal objects.
        
        This is typically used when serializing data for DynamoDB, where all
        numbers should be stored as Decimal objects for precision.
        
        Args:
            data: The data structure to convert. Can be dict, list, or any other type.
            
        Returns:
            The data structure with int and float objects converted to Decimal.
        """
        if isinstance(data, dict):
            return {
                key: DecimalConversionUtility.convert_native_types_to_decimals(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                DecimalConversionUtility.convert_native_types_to_decimals(item)
                for item in data
            ]
        elif isinstance(data, float):
            # Convert float to Decimal using string representation for precision
            return Decimal(str(data))
        elif isinstance(data, int) and not isinstance(data, bool):
            # Convert int to Decimal, but exclude bool (which is a subclass of int)
            return Decimal(data)
        else:
            return data

    @staticmethod
    def is_numeric_type(value: Any) -> bool:
        """
        Check if a value is a numeric type (int, float, or Decimal).
        
        Args:
            value: The value to check.
            
        Returns:
            True if the value is a numeric type, False otherwise.
        """
        return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)

    @staticmethod
    def safe_decimal_conversion(value: Any, default: Any = None) -> Union[Decimal, Any]:
        """
        Safely convert a value to Decimal, returning a default if conversion fails.
        
        Args:
            value: The value to convert to Decimal.
            default: The default value to return if conversion fails.
            
        Returns:
            Decimal representation of the value, or the default if conversion fails.
        """
        try:
            if isinstance(value, Decimal):
                return value
            elif isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                return Decimal(value)
            else:
                return default
        except (ValueError, TypeError, ArithmeticError):
            return default

    @staticmethod
    def format_decimal_for_display(value: Decimal, precision: int = 2) -> str:
        """
        Format a Decimal value for display with specified precision.
        
        Args:
            value: The Decimal value to format.
            precision: Number of decimal places to display.
            
        Returns:
            Formatted string representation of the Decimal.
        """
        if not isinstance(value, Decimal):
            value = DecimalConversionUtility.safe_decimal_conversion(value, Decimal('0'))
        
        format_string = f"{{:.{precision}f}}"
        return format_string.format(float(value))
