# boto3-assist: Decimal Conversion Enhancement Pattern

> **Status**: 📋 Proposed Enhancement - Pending Implementation  
> **Last Updated**: 2025-10-12  
> **TODO**: Review and integrate once boto3-assist library is updated

---

## Problem Statement

**Current Issue**: When DynamoDB returns data, numeric values are deserialized as `Decimal` objects (boto3's default). This causes issues in application code that expects `float` values.

### Current Workarounds (Problematic)

```python
# ❌ PROBLEM 1: Converting in property getter breaks mapping
@property
def content(self) -> Dict[str, Any]:
    return self._convert_decimals_to_floats(self._content)  # NEW object every call

# Result: boto3-assist's .map() loses track of the object → mapping fails silently
```

```python
# ❌ PROBLEM 2: Manual conversion everywhere
choice_avg = float(summary.choice_averages["product_a"])  # Must remember to convert
assert abs(choice_avg - 4.0) < 0.1
```

---

## Proposed Solution: Auto-Convert Decimals in DynamoDBSerializer

Enhance `boto3_assist.dynamodb.dynamodb_serializer.DynamoDBSerializer` to **automatically convert Decimals to appropriate Python types** during deserialization based on the target type hint.

### Implementation Strategy

#### 1. Decimal Conversion During `.map()`

```python
# In DynamoDBSerializer.map() method

def map(source: dict, target: DynamoDBModelBase) -> DynamoDBModelBase:
    """
    Map source dict to target model, converting Decimals automatically.
    
    Conversion rules:
    - Decimal → float (for float type hints)
    - Decimal → int (for int type hints, if whole number)
    - Dict[str, float] → converts nested Decimals in dict values
    - List[float] → converts Decimals in list items
    """
    for attr_name, attr_value in source.items():
        if not hasattr(target, attr_name):
            continue
            
        # Get the property type hint if available
        target_type = _get_type_hint(target, attr_name)
        
        # Convert Decimal based on target type
        converted_value = _convert_decimal_by_type(attr_value, target_type)
        
        # Set the converted value
        setattr(target, attr_name, converted_value)
    
    return target
```

#### 2. Type-Aware Decimal Conversion

```python
from typing import get_type_hints, get_origin, get_args
from decimal import Decimal

def _get_type_hint(obj: Any, attr_name: str) -> Any:
    """Get the type hint for an attribute."""
    try:
        hints = get_type_hints(type(obj))
        return hints.get(attr_name)
    except Exception:
        return None

def _convert_decimal_by_type(value: Any, target_type: Any) -> Any:
    """
    Convert Decimal to appropriate type based on target_type hint.
    
    Examples:
        value=Decimal('4.5'), target_type=float → 4.5
        value=Decimal('10'), target_type=int → 10
        value={'a': Decimal('1.5')}, target_type=Dict[str, float] → {'a': 1.5}
    """
    if value is None:
        return None
    
    # Direct Decimal conversion
    if isinstance(value, Decimal):
        if target_type == float or target_type == 'float':
            return float(value)
        elif target_type == int or target_type == 'int':
            return int(value)
        # Default: keep as Decimal if no type hint
        return value
    
    # Handle Dict[str, float] and similar
    if isinstance(value, dict):
        origin = get_origin(target_type)
        if origin is dict:
            args = get_args(target_type)
            if len(args) == 2:
                # Dict[K, V] - convert values
                value_type = args[1]
                return {
                    k: _convert_decimal_by_type(v, value_type) 
                    for k, v in value.items()
                }
        # No type info, recursively convert all Decimals to float
        return {
            k: _convert_decimal_by_type(v, None) 
            for k, v in value.items()
        }
    
    # Handle List[float] and similar
    if isinstance(value, list):
        origin = get_origin(target_type)
        if origin is list:
            args = get_args(target_type)
            if args:
                item_type = args[0]
                return [_convert_decimal_by_type(item, item_type) for item in value]
        # No type info, recursively convert
        return [_convert_decimal_by_type(item, None) for item in value]
    
    # Return as-is for non-Decimal types
    return value
```

---

## Model Pattern (After Enhancement)

With the enhancement, models can use simple, clean properties:

```python
class VoteSummary(BaseModel):
    def __init__(self):
        super().__init__()
        self._choice_averages: Dict[str, float] = {}  # Type hint drives conversion
        self._total_participants: int = 0
        self._choice_percentages: Dict[str, float] = {}
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        """Returns dict with floats (boto3-assist converts Decimals automatically)."""
        return self._choice_averages  # Just return it - no conversion needed!
    
    @choice_averages.setter
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value  # boto3-assist handles Decimal→float
```

### Key Benefits

✅ **No property getter manipulation** - Returns actual object, preserves identity  
✅ **Type-driven conversion** - Uses Python type hints (standard practice)  
✅ **Automatic and transparent** - Developers don't think about Decimals  
✅ **Backward compatible** - No type hint = no conversion (existing behavior)

---

## Test Patterns

### Test Suite for DynamoDBSerializer Enhancement

```python
import pytest
from decimal import Decimal
from typing import Dict, List
from boto3_assist.dynamodb.dynamodb_serializer import DynamoDBSerializer
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase

class TestModel(DynamoDBModelBase):
    """Test model with various type hints."""
    def __init__(self):
        super().__init__()
        self.float_value: float = 0.0
        self.int_value: int = 0
        self.dict_of_floats: Dict[str, float] = {}
        self.list_of_floats: List[float] = []
        self.no_hint_value = None  # No type hint


class TestDecimalConversion:
    """Test automatic Decimal conversion during .map()"""
    
    def test_decimal_to_float(self):
        """Test Decimal converts to float when property is typed as float."""
        source = {"float_value": Decimal("4.5")}
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        assert isinstance(result.float_value, float)
        assert result.float_value == 4.5
    
    def test_decimal_to_int(self):
        """Test Decimal converts to int when property is typed as int."""
        source = {"int_value": Decimal("42")}
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        assert isinstance(result.int_value, int)
        assert result.int_value == 42
    
    def test_dict_of_decimals_to_floats(self):
        """Test Dict[str, float] type hint converts nested Decimals."""
        source = {
            "dict_of_floats": {
                "avg_rating": Decimal("4.7"),
                "completion_rate": Decimal("0.85")
            }
        }
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        assert isinstance(result.dict_of_floats["avg_rating"], float)
        assert isinstance(result.dict_of_floats["completion_rate"], float)
        assert result.dict_of_floats["avg_rating"] == 4.7
        assert result.dict_of_floats["completion_rate"] == 0.85
    
    def test_list_of_decimals_to_floats(self):
        """Test List[float] type hint converts list items."""
        source = {
            "list_of_floats": [
                Decimal("1.5"),
                Decimal("2.7"),
                Decimal("3.9")
            ]
        }
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        assert all(isinstance(x, float) for x in result.list_of_floats)
        assert result.list_of_floats == [1.5, 2.7, 3.9]
    
    def test_no_type_hint_preserves_decimal(self):
        """Test that properties without type hints keep Decimal (backward compat)."""
        source = {"no_hint_value": Decimal("99.9")}
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        # Without type hint, should preserve Decimal for backward compatibility
        assert isinstance(result.no_hint_value, Decimal)
        assert result.no_hint_value == Decimal("99.9")
    
    def test_nested_dict_without_type_hint(self):
        """Test Dict[str, Any] or no hint converts Decimals to float by default."""
        # This is the common case: content: Dict[str, Any]
        source = {
            "no_hint_value": {
                "nested_decimal": Decimal("7.5"),
                "deeply": {
                    "nested": Decimal("3.14")
                }
            }
        }
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        # For dicts without specific type hints, convert Decimals to float
        # This prevents the common Decimal comparison errors
        assert isinstance(result.no_hint_value["nested_decimal"], float)
        assert isinstance(result.no_hint_value["deeply"]["nested"], float)
    
    def test_mixed_types_in_dict(self):
        """Test dict with mixed types (strings, ints, Decimals)."""
        source = {
            "dict_of_floats": {
                "count": 5,  # int stays int
                "name": "test",  # string stays string
                "average": Decimal("4.5"),  # Decimal → float
                "rate": 0.75  # float stays float
            }
        }
        target = TestModel()
        
        result = DynamoDBSerializer.map(source, target)
        
        assert isinstance(result.dict_of_floats["count"], int)
        assert isinstance(result.dict_of_floats["name"], str)
        assert isinstance(result.dict_of_floats["average"], float)
        assert isinstance(result.dict_of_floats["rate"], float)
    
    def test_round_trip_consistency(self):
        """Test save → retrieve maintains data consistency."""
        # This is the critical integration test
        from boto3_assist.dynamodb.dynamodb import DynamoDB
        import moto
        
        with moto.mock_aws():
            db = DynamoDB()
            # Create test table...
            
            # Save model
            model = TestModel()
            model.dict_of_floats = {"avg": 4.5, "rate": 0.85}
            db.save(table_name="test_table", item=model)
            
            # Retrieve model
            retrieved = db.get(
                table_name="test_table",
                key={"pk": model.pk, "sk": model.sk}
            )
            mapped = DynamoDBSerializer.map(retrieved, TestModel())
            
            # Should get back floats, not Decimals
            assert isinstance(mapped.dict_of_floats["avg"], float)
            assert mapped.dict_of_floats["avg"] == 4.5
            # Should work in comparisons without explicit conversion
            assert mapped.dict_of_floats["avg"] > 4.0
```

---

## Integration Test Pattern

Test that existing models work correctly after the enhancement:

```python
def test_vote_summary_decimal_handling(db, vote_summary_service):
    """Test VoteSummary with rating votes (has choice_averages)."""
    # Create summary with averages
    result = vote_summary_service.create(
        tenant_id="tenant_123",
        user_id="user_123",
        target_id="product_rating",
        vote_type="rating",
        choice_averages={"product_a": 4.5, "product_b": 3.7}
    )
    
    assert result.success
    summary_id = result.data.id
    
    # Retrieve from database (will come back with Decimals from DynamoDB)
    retrieved = vote_summary_service.get_by_id(
        summary_id, "tenant_123", "user_123"
    )
    
    assert retrieved.success
    summary = retrieved.data
    
    # Should be able to use directly in float operations
    # (Previously required float() conversion)
    assert summary.choice_averages["product_a"] > 4.0  # No TypeError!
    assert abs(summary.choice_averages["product_a"] - 4.5) < 0.1  # Works!
    
    # Type should be float
    assert isinstance(summary.choice_averages["product_a"], float)
```

---

## Migration Path

### Phase 1: Add Enhancement (Backward Compatible)
- Implement `_convert_decimal_by_type()` in DynamoDBSerializer
- Only convert when type hint is present
- Existing models without type hints work as before

### Phase 2: Update Documentation
- Document the pattern in boto3-assist README
- Add examples showing type hints enabling auto-conversion
- Show before/after code patterns

### Phase 3: Deprecation (Optional, Future)
- Consider making Decimal→float the default for `Dict[str, Any]`
- Add configuration option: `auto_convert_decimals=True` (default)
- Provide escape hatch for those who need raw Decimals

---

## Configuration Option (Advanced)

Allow users to control behavior:

```python
class DynamoDBSerializer:
    """
    Serializer with configurable Decimal handling.
    """
    
    @classmethod
    def map(cls, source: dict, target: DynamoDBModelBase, 
            auto_convert_decimals: bool = True) -> DynamoDBModelBase:
        """
        Map source to target with optional Decimal conversion.
        
        Args:
            auto_convert_decimals: If True, converts Decimals based on type hints.
                                   If False, preserves Decimals (legacy behavior).
        """
        if not auto_convert_decimals:
            # Legacy behavior - no conversion
            return cls._map_legacy(source, target)
        
        # New behavior - smart conversion
        return cls._map_with_conversion(source, target)
```

---

## Summary for AI Implementation

### What to Implement
1. **Add `_convert_decimal_by_type()` helper** in `dynamodb_serializer.py`
2. **Enhance `.map()` method** to use type hints for conversion
3. **Add comprehensive tests** covering all type hint scenarios
4. **Update documentation** with examples

### Key Principles
- ✅ Type hints drive conversion (Pythonic)
- ✅ Backward compatible (no breaking changes)
- ✅ Transparent to users (automatic)
- ✅ Preserves object identity (no new objects in getters)

### Test Coverage Required
- Direct Decimal → float/int conversion
- Nested dicts with type hints
- Lists with type hints
- Mixed types in containers
- Round-trip save/retrieve
- Backward compatibility (no type hint)

### Benefits
- Eliminates entire class of TypeError bugs
- Makes DynamoDB models work like native Python
- Reduces boilerplate in application code
- Follows Python's type hint best practices

---

**This enhancement would make boto3-assist the gold standard for DynamoDB Python models!** 🎯
