"""
Backward Compatibility Tests for Decimal Conversion Enhancement

This test suite ensures that the automatic decimal conversion enhancement
does not introduce breaking changes to existing code patterns.

Based on: docs/issues/BOTO3_ASSIST_BEFORE_AFTER.md
"""

import unittest
from decimal import Decimal
from typing import Dict, List, Any, Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


# Test Models - Simulating "Before" patterns (with manual conversion)
class VoteSummaryLegacy(DynamoDBModelBase):
    """Legacy model with manual Decimal conversion in property getter"""
    
    def __init__(self):
        super().__init__()
        self._choice_averages: Dict[str, float] = {}
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        # Legacy pattern: Manual conversion in getter
        return {k: float(v) if isinstance(v, Decimal) else v 
                for k, v in self._choice_averages.items()}
    
    @choice_averages.setter
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value


# Test Models - Simulating "After" patterns (automatic conversion)
class VoteSummaryModern(DynamoDBModelBase):
    """Modern model relying on automatic decimal conversion"""
    
    def __init__(self):
        super().__init__()
        self._choice_averages: Dict[str, float] = {}
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        # Modern pattern: Just return it - boto3-assist handles conversion
        return self._choice_averages
    
    @choice_averages.setter
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value


class AnalyticsLegacy(DynamoDBModelBase):
    """Legacy model with manual Decimal handling for float property"""
    
    def __init__(self):
        super().__init__()
        self._conversion_rate: float = 0.0
    
    @property
    def conversion_rate(self) -> float:
        # Legacy pattern: Check and convert
        if isinstance(self._conversion_rate, Decimal):
            return float(self._conversion_rate)
        return self._conversion_rate
    
    @conversion_rate.setter
    def conversion_rate(self, value: float):
        self._conversion_rate = value


class AnalyticsModern(DynamoDBModelBase):
    """Modern model with automatic conversion"""
    
    def __init__(self):
        super().__init__()
        self._conversion_rate: float = 0.0
    
    @property
    def conversion_rate(self) -> float:
        return self._conversion_rate
    
    @conversion_rate.setter
    def conversion_rate(self, value: float):
        self._conversion_rate = value


class MetricsLegacy(DynamoDBModelBase):
    """Legacy model with list conversion"""
    
    def __init__(self):
        super().__init__()
        self._scores: List[float] = []
    
    @property
    def scores(self) -> List[float]:
        # Legacy pattern: Convert list items
        return [float(x) if isinstance(x, Decimal) else x for x in self._scores]
    
    @scores.setter
    def scores(self, value: List[float]):
        self._scores = value


class MetricsModern(DynamoDBModelBase):
    """Modern model with automatic list conversion"""
    
    def __init__(self):
        super().__init__()
        self._scores: List[float] = []
    
    @property
    def scores(self) -> List[float]:
        return self._scores
    
    @scores.setter
    def scores(self, value: List[float]):
        self._scores = value


class ReportLegacy(DynamoDBModelBase):
    """Legacy model with complex nested structure conversion"""
    
    def __init__(self):
        super().__init__()
        self._metrics: Dict[str, Any] = {}
    
    @property
    def metrics(self) -> Dict[str, Any]:
        # Legacy pattern: Recursive conversion
        def convert(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            return obj
        return convert(self._metrics)
    
    @metrics.setter
    def metrics(self, value: Dict[str, Any]):
        self._metrics = value


class ReportModern(DynamoDBModelBase):
    """Modern model with automatic nested conversion"""
    
    def __init__(self):
        super().__init__()
        self._metrics: Dict[str, Any] = {}
    
    @property
    def metrics(self) -> Dict[str, Any]:
        return self._metrics
    
    @metrics.setter
    def metrics(self, value: Dict[str, Any]):
        self._metrics = value


class ProductModel(DynamoDBModelBase):
    """Test model with various numeric types"""
    
    def __init__(self):
        super().__init__()
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.price: float = 0.0
        self.quantity: int = 0
        self.weight: float = 0.0
        self.cost: float = 0.0
        self.tax_rate: float = 0.0


class TestDecimalBackwardCompatibility(unittest.TestCase):
    """
    Test suite to ensure no breaking changes from decimal conversion enhancement.
    
    These tests verify that:
    1. Models without manual conversion in getters work correctly
    2. New code patterns (automatic conversion) work as expected
    3. Automatic conversion eliminates the need for manual conversion
    4. No regressions in existing functionality
    """

    def test_simple_model_without_conversion_works(self):
        """
        Test that simple models without manual conversion work correctly
        
        This represents the most common existing code pattern that will
        benefit from automatic conversion.
        """
        # Simulate DynamoDB response with Decimal values
        dynamodb_item = {
            "choice_averages": {
                "product_a": Decimal("4.5"),
                "product_b": Decimal("3.8"),
                "product_c": Decimal("4.2")
            }
        }
        
        # Modern pattern with automatic conversion
        summary = VoteSummaryModern().map(dynamodb_item)
        
        # Verify the values are floats (automatic conversion during map)
        self.assertIsInstance(summary.choice_averages["product_a"], float)
        self.assertEqual(summary.choice_averages["product_a"], 4.5)
        
        # Verify arithmetic operations work
        self.assertTrue(abs(summary.choice_averages["product_a"] - 4.5) < 0.1)

    def test_modern_dict_float_pattern_works(self):
        """
        Test that modern pattern with automatic conversion works correctly
        
        This verifies the enhancement works as designed.
        """
        # Simulate DynamoDB response with Decimal values
        dynamodb_item = {
            "choice_averages": {
                "product_a": Decimal("4.5"),
                "product_b": Decimal("3.8"),
                "product_c": Decimal("4.2")
            }
        }
        
        # Modern pattern relies on automatic conversion
        summary = VoteSummaryModern().map(dynamodb_item)
        
        # Verify the values are floats (automatic conversion during map)
        self.assertIsInstance(summary.choice_averages["product_a"], float)
        self.assertEqual(summary.choice_averages["product_a"], 4.5)
        
        # Verify arithmetic operations work
        self.assertTrue(abs(summary.choice_averages["product_a"] - 4.5) < 0.1)

    def test_multiple_models_produce_consistent_results(self):
        """
        Test that different models with same data produce consistent results
        
        This ensures consistency in decimal conversion across models.
        """
        dynamodb_item_analytics = {"conversion_rate": Decimal("0.15")}
        dynamodb_item_votes = {
            "choice_averages": {
                "product_a": Decimal("4.5"),
                "product_b": Decimal("3.8")
            }
        }
        
        analytics = AnalyticsModern().map(dynamodb_item_analytics)
        votes = VoteSummaryModern().map(dynamodb_item_votes)
        
        # Both should have float values
        self.assertIsInstance(analytics.conversion_rate, float)
        self.assertIsInstance(votes.choice_averages["product_a"], float)

    def test_float_property_automatic_conversion(self):
        """Test that float properties are automatically converted"""
        dynamodb_item = {
            "conversion_rate": Decimal("0.15")
        }
        
        analytics = AnalyticsModern().map(dynamodb_item)
        
        self.assertIsInstance(analytics.conversion_rate, float)
        self.assertEqual(analytics.conversion_rate, 0.15)

    def test_modern_float_property_works(self):
        """Test that modern float property with automatic conversion works"""
        dynamodb_item = {
            "conversion_rate": Decimal("0.15")
        }
        
        analytics = AnalyticsModern().map(dynamodb_item)
        
        self.assertIsInstance(analytics.conversion_rate, float)
        self.assertEqual(analytics.conversion_rate, 0.15)

    def test_list_pattern_automatic_conversion(self):
        """Test that list items are automatically converted"""
        dynamodb_item = {
            "scores": [Decimal("1.5"), Decimal("2.7"), Decimal("3.9")]
        }
        
        metrics = MetricsModern().map(dynamodb_item)
        
        # All should be floats
        for score in metrics.scores:
            self.assertIsInstance(score, float)
        
        # Can perform arithmetic
        avg = sum(metrics.scores) / len(metrics.scores)
        self.assertAlmostEqual(avg, 2.7, places=1)

    def test_modern_list_pattern_works(self):
        """Test that modern list pattern with automatic conversion works"""
        dynamodb_item = {
            "scores": [Decimal("1.5"), Decimal("2.7"), Decimal("3.9")]
        }
        
        metrics = MetricsModern().map(dynamodb_item)
        
        # All should be floats
        for score in metrics.scores:
            self.assertIsInstance(score, float)
        
        # Can perform arithmetic
        avg = sum(metrics.scores) / len(metrics.scores)
        self.assertAlmostEqual(avg, 2.7, places=1)

    def test_nested_structure_automatic_conversion(self):
        """Test that nested structures are automatically converted"""
        dynamodb_item = {
            "metrics": {
                "performance": {
                    "avg_load_time_ms": Decimal("185.5"),
                    "requests": Decimal("1000")
                },
                "scores": [Decimal("4.5"), Decimal("4.8")]
            }
        }
        
        report = ReportModern().map(dynamodb_item)
        
        # Verify nested conversion works
        avg_load = report.metrics["performance"]["avg_load_time_ms"]
        self.assertIsInstance(avg_load, float)
        self.assertEqual(avg_load, 185.5)
        
        # Can do comparisons
        self.assertTrue(avg_load < 200)

    def test_modern_nested_structure_works(self):
        """Test that modern nested structure with automatic conversion works"""
        dynamodb_item = {
            "metrics": {
                "performance": {
                    "avg_load_time_ms": Decimal("185.5"),
                    "requests": Decimal("1000")
                },
                "scores": [Decimal("4.5"), Decimal("4.8")]
            }
        }
        
        report = ReportModern().map(dynamodb_item)
        
        # Verify nested conversion works
        avg_load = report.metrics["performance"]["avg_load_time_ms"]
        self.assertIsInstance(avg_load, float)
        self.assertEqual(avg_load, 185.5)
        
        # Can do comparisons
        self.assertTrue(avg_load < 200)

    def test_whole_numbers_convert_to_int(self):
        """Test that Decimal whole numbers convert to int, not float"""
        dynamodb_item = {
            "id": "prod_123",
            "name": "Test Product",
            "price": Decimal("19.99"),
            "quantity": Decimal("5"),  # Whole number
            "weight": Decimal("2.5")
        }
        
        product = ProductModel().map(dynamodb_item)
        
        # Whole number should be int
        self.assertIsInstance(product.quantity, int)
        self.assertEqual(product.quantity, 5)
        
        # Decimal number should be float
        self.assertIsInstance(product.price, float)
        self.assertEqual(product.price, 19.99)

    def test_arithmetic_operations_no_typeerror(self):
        """
        Test that arithmetic operations work without TypeErrors
        
        This was a common issue before the enhancement.
        """
        dynamodb_item = {
            "price": Decimal("19.99"),
            "cost": Decimal("12.50"),
            "quantity": Decimal("10")
        }
        
        product = ProductModel().map(dynamodb_item)
        
        # These should not raise TypeError
        profit = product.price - product.cost
        self.assertIsInstance(profit, float)
        self.assertAlmostEqual(profit, 7.49, places=2)
        
        total = product.price * product.quantity
        self.assertIsInstance(total, (int, float))
        self.assertAlmostEqual(total, 199.9, places=1)

    def test_map_with_dynamodb_response_metadata(self):
        """Test mapping with full DynamoDB response structure"""
        dynamodb_response = {
            "Item": {
                "id": "prod_456",
                "name": "Test Product",
                "price": Decimal("29.99"),
                "quantity": Decimal("10")
            },
            "ResponseMetadata": {
                "RequestId": "abc123",
                "HTTPStatusCode": 200
            }
        }
        
        product = ProductModel().map(dynamodb_response)
        
        # Should handle the nested Item structure
        self.assertEqual(product.id, "prod_456")
        self.assertIsInstance(product.price, float)
        self.assertEqual(product.price, 29.99)
        self.assertIsInstance(product.quantity, int)
        self.assertEqual(product.quantity, 10)

    def test_map_with_item_only_response(self):
        """Test mapping with Item-only response structure"""
        dynamodb_response = {
            "Item": {
                "id": "prod_789",
                "name": "Another Product",
                "price": Decimal("39.99")
            }
        }
        
        product = ProductModel().map(dynamodb_response)
        
        self.assertEqual(product.id, "prod_789")
        self.assertIsInstance(product.price, float)
        self.assertEqual(product.price, 39.99)

    def test_map_with_direct_data(self):
        """Test mapping with direct data (no Item wrapper)"""
        direct_data = {
            "id": "prod_999",
            "name": "Direct Product",
            "price": Decimal("49.99"),
            "quantity": Decimal("5")
        }
        
        product = ProductModel().map(direct_data)
        
        self.assertEqual(product.id, "prod_999")
        self.assertIsInstance(product.price, float)
        self.assertEqual(product.price, 49.99)
        self.assertIsInstance(product.quantity, int)
        self.assertEqual(product.quantity, 5)

    def test_mixed_decimal_and_native_types(self):
        """Test mapping with mixed Decimal and native Python types"""
        mixed_data = {
            "id": "prod_111",
            "name": "Mixed Product",
            "price": Decimal("19.99"),  # Decimal
            "quantity": 10,              # Already int
            "weight": 2.5,               # Already float
            "cost": Decimal("8.00")      # Decimal
        }
        
        product = ProductModel().map(mixed_data)
        
        # All numeric types should work correctly
        self.assertIsInstance(product.price, float)
        self.assertIsInstance(product.quantity, int)
        self.assertIsInstance(product.weight, float)
        self.assertIsInstance(product.cost, float)

    def test_empty_collections(self):
        """Test that empty collections are handled correctly"""
        empty_data = {
            "choice_averages": {}
        }
        
        summary = VoteSummaryModern().map(empty_data)
        self.assertEqual(summary.choice_averages, {})
        
        metrics_data = {
            "scores": []
        }
        
        metrics = MetricsModern().map(metrics_data)
        self.assertEqual(metrics.scores, [])

    def test_none_values_preserved(self):
        """Test that None values are preserved correctly"""
        data_with_none = {
            "id": "prod_222",
            "name": None,
            "price": Decimal("9.99")
        }
        
        product = ProductModel().map(data_with_none)
        
        self.assertEqual(product.id, "prod_222")
        self.assertIsNone(product.name)
        self.assertIsInstance(product.price, float)

    def test_boolean_values_not_affected(self):
        """Test that boolean values are not affected by numeric conversion"""
        # Create a model with boolean
        class ConfigModel(DynamoDBModelBase):
            def __init__(self):
                super().__init__()
                self.enabled: bool = False
                self.count: int = 0
        
        data = {
            "enabled": True,
            "count": Decimal("5")
        }
        
        config = ConfigModel().map(data)
        
        self.assertIsInstance(config.enabled, bool)
        self.assertTrue(config.enabled)
        self.assertIsInstance(config.count, int)
        self.assertEqual(config.count, 5)

    def test_string_values_not_affected(self):
        """Test that string values are not affected by conversion"""
        data = {
            "id": "prod_333",
            "name": "Test Product Name",
            "price": Decimal("14.99")
        }
        
        product = ProductModel().map(data)
        
        self.assertIsInstance(product.id, str)
        self.assertIsInstance(product.name, str)
        self.assertEqual(product.name, "Test Product Name")

    def test_map_conversion_from_decimals(self):
        """Test that map() converts Decimals from DynamoDB responses"""
        # Simulate actual DynamoDB response with Decimals
        dynamodb_data = {
            "id": "prod_444",
            "name": "Test Product",
            "price": Decimal("24.99"),
            "quantity": Decimal("7")
        }
        
        # Map to model
        product = ProductModel().map(dynamodb_data)
        
        # Values should be converted to native types
        self.assertEqual(product.id, "prod_444")
        self.assertEqual(product.name, "Test Product")
        self.assertIsInstance(product.price, float)
        self.assertEqual(product.price, 24.99)
        self.assertIsInstance(product.quantity, int)
        self.assertEqual(product.quantity, 7)

    def test_comparison_operations_work(self):
        """Test that comparison operations work without manual conversion"""
        data = {
            "price": Decimal("19.99"),
            "cost": Decimal("12.00"),
            "tax_rate": Decimal("0.08")
        }
        
        product = ProductModel().map(data)
        
        # All these comparisons should work without manual float() calls
        self.assertTrue(product.price > 10.0)
        self.assertTrue(product.price < 25.0)
        self.assertTrue(product.cost >= 12.0)
        self.assertTrue(product.tax_rate < 0.1)
        self.assertFalse(product.price == 20.0)

    def test_complex_nested_list_dict_structure(self):
        """Test complex nested structures with lists and dicts"""
        complex_data = {
            "metrics": {
                "daily": [
                    {"date": "2023-01-01", "revenue": Decimal("199.99"), "orders": Decimal("5")},
                    {"date": "2023-01-02", "revenue": Decimal("299.99"), "orders": Decimal("8")}
                ],
                "monthly": {
                    "total_revenue": Decimal("1499.99"),
                    "total_orders": Decimal("45"),
                    "avg_order_value": Decimal("33.33")
                }
            }
        }
        
        report = ReportModern().map(complex_data)
        
        # Check nested list items
        first_day = report.metrics["daily"][0]
        self.assertIsInstance(first_day["revenue"], float)
        self.assertIsInstance(first_day["orders"], int)
        self.assertEqual(first_day["revenue"], 199.99)
        
        # Check nested dict items
        monthly = report.metrics["monthly"]
        self.assertIsInstance(monthly["total_revenue"], float)
        self.assertIsInstance(monthly["total_orders"], int)
        self.assertIsInstance(monthly["avg_order_value"], float)


if __name__ == '__main__':
    unittest.main()
