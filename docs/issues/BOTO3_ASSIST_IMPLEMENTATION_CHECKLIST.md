# boto3-assist Decimal Enhancement - Implementation Checklist

> **Status**: 📋 Proposed Enhancement - Pending Implementation  
> **Last Updated**: 2025-10-12  
> **TODO**: Complete when implementing in boto3-assist library

---

## Files to Modify

### 1. `boto3_assist/dynamodb/dynamodb_serializer.py`

**Add import:**
```python
from typing import get_type_hints, get_origin, get_args, Any
from decimal import Decimal
```

**Add helper function** (before `.map()` method):
```python
def _get_type_hint(obj: Any, attr_name: str) -> Any:
    """
    Get the type hint for an attribute.
    
    Returns:
        The type hint if available, None otherwise
    """
    try:
        hints = get_type_hints(type(obj))
        return hints.get(attr_name)
    except (AttributeError, TypeError, NameError):
        return None


def _convert_decimal_by_type(value: Any, target_type: Any) -> Any:
    """
    Recursively convert Decimal objects based on target type hint.
    
    Conversion rules:
    - Decimal + float hint → float
    - Decimal + int hint → int  
    - Dict[str, float] → recursively convert dict values
    - List[float] → convert list items
    - No type hint + nested dict/list → convert Decimals to float
    - No type hint + direct Decimal → preserve as Decimal (backward compat)
    
    Args:
        value: The value to convert (may contain Decimals)
        target_type: The type hint from the target property
    
    Returns:
        Converted value with Decimals changed to appropriate types
    """
    if value is None:
        return None
    
    # Handle direct Decimal conversion
    if isinstance(value, Decimal):
        # Has explicit type hint
        if target_type == float or str(target_type) == "<class 'float'>":
            return float(value)
        elif target_type == int or str(target_type) == "<class 'int'>":
            return int(value)
        # No type hint or unknown hint - preserve Decimal for backward compatibility
        return value
    
    # Handle Dict types
    if isinstance(value, dict):
        origin = get_origin(target_type)
        if origin is dict:
            # Has Dict[K, V] type hint
            args = get_args(target_type)
            if len(args) == 2:
                value_type = args[1]  # V in Dict[K, V]
                return {
                    k: _convert_decimal_by_type(v, value_type)
                    for k, v in value.items()
                }
        # No specific type hint - convert any Decimals to float by default
        # This prevents common errors with Dict[str, Any] or untyped dicts
        return {
            k: _convert_decimal_by_type(v, None) if isinstance(v, Decimal) else 
               _convert_decimal_by_type(v, None) if isinstance(v, (dict, list)) else v
            for k, v in value.items()
        }
    
    # Handle List types  
    if isinstance(value, list):
        origin = get_origin(target_type)
        if origin is list:
            # Has List[T] type hint
            args = get_args(target_type)
            if args:
                item_type = args[0]
                return [_convert_decimal_by_type(item, item_type) for item in value]
        # No specific type hint - convert any Decimals to float
        return [
            _convert_decimal_by_type(item, None) if isinstance(item, Decimal) else
            _convert_decimal_by_type(item, None) if isinstance(item, (dict, list)) else item
            for item in value
        ]
    
    # Non-Decimal, non-container types - return as-is
    return value
```

**Modify `.map()` method:**
```python
def map(source: dict, target: DynamoDBModelBase) -> DynamoDBModelBase:
    """
    Map source dictionary to target model instance.
    
    Automatically converts Decimal objects from DynamoDB to appropriate
    Python types based on property type hints.
    
    Args:
        source: Dictionary from DynamoDB (may contain Decimals)
        target: Target model instance to populate
    
    Returns:
        Populated model instance with Decimals converted appropriately
    """
    # ... existing code to handle ResponseMetadata, etc ...
    
    # Main mapping loop
    for attr_name, attr_value in source.items():
        if not hasattr(target, attr_name):
            continue
        
        # Get type hint for this property
        target_type = _get_type_hint(target, attr_name)
        
        # Convert Decimals based on type hint
        converted_value = _convert_decimal_by_type(attr_value, target_type)
        
        # Set the converted value
        setattr(target, attr_name, converted_value)
    
    return target
```

---

## Tests to Add

### 2. `tests/test_dynamodb_serializer_decimals.py` (NEW FILE)

Create comprehensive test suite (see full examples in BOTO3_ASSIST_DECIMAL_PATTERN.md):

**Test coverage:**
- ✅ `test_decimal_to_float` - Direct Decimal with float hint
- ✅ `test_decimal_to_int` - Direct Decimal with int hint  
- ✅ `test_dict_of_decimals_to_floats` - Dict[str, float] conversion
- ✅ `test_list_of_decimals_to_floats` - List[float] conversion
- ✅ `test_no_type_hint_preserves_decimal` - Backward compatibility
- ✅ `test_nested_dict_without_type_hint` - Dict[str, Any] behavior
- ✅ `test_mixed_types_in_dict` - Multiple types in one dict
- ✅ `test_round_trip_consistency` - Save/retrieve integration

---

## Documentation Updates

### 3. `README.md` or `docs/DECIMAL_HANDLING.md`

Add section:

```markdown
## Automatic Decimal Conversion

boto3-assist automatically converts DynamoDB's `Decimal` objects to Python 
native types based on your model's type hints:

### Example

```python
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from typing import Dict

class VoteSummary(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._choice_averages: Dict[str, float] = {}
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        return self._choice_averages
    
    @choice_averages.setter  
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value

# Save with floats
summary = VoteSummary()
summary.choice_averages = {"option_a": 4.5}
db.save(table_name="summaries", item=summary)

# Retrieve - Decimals automatically converted to floats!
result = db.get(table_name="summaries", key={...})
mapped = summary.map(result)
assert isinstance(mapped.choice_averages["option_a"], float)  # ✅
assert mapped.choice_averages["option_a"] > 4.0  # ✅ Works without float()!
```

### Type Hint Support

| Type Hint | DynamoDB Type | Converted To |
|-----------|---------------|--------------|
| `float` | Decimal | `float` |
| `int` | Decimal | `int` |
| `Dict[str, float]` | Dict with Decimals | Dict with `float` values |
| `List[float]` | List with Decimals | List with `float` items |
| No hint (direct) | Decimal | `Decimal` (backward compat) |
| No hint (nested) | Decimal in dict/list | `float` (convenience) |

### Benefits

- ✅ No manual `float()` conversions needed
- ✅ Type-safe with Python's type hints
- ✅ Backward compatible
- ✅ Prevents `TypeError: unsupported operand type(s) for -: 'decimal.Decimal' and 'float'`
```

---

## Version and Changelog

### 4. `setup.py` or `pyproject.toml`

Bump version (e.g., `0.8.0` → `0.9.0` for new feature)

### 5. `CHANGELOG.md`

Add entry:

```markdown
## [0.9.0] - 2025-10-XX

### Added
- **Automatic Decimal Conversion**: DynamoDBSerializer now automatically converts
  DynamoDB Decimal objects to Python native types (float/int) based on property
  type hints. This eliminates the need for manual `float()` conversions and
  prevents common TypeError issues.
- Type hint support for Dict[str, float], List[float], and nested structures
- Comprehensive test suite for Decimal conversion edge cases

### Changed
- Enhanced `.map()` method to use type hints for smarter deserialization
- Dicts and lists without specific type hints now convert nested Decimals to
  float by default (was: preserved as Decimal)

### Backward Compatibility
- Properties without type hints preserve Decimal objects (maintains legacy behavior)
- No breaking changes to existing APIs
```

---

## Testing Strategy

### Run Tests
```bash
# Unit tests for serializer
pytest tests/test_dynamodb_serializer_decimals.py -v

# Integration tests with real models
pytest tests/integration/test_decimal_models.py -v

# Full regression suite
pytest tests/ -v
```

### Manual Verification
1. Create model with `Dict[str, float]` property
2. Save to DynamoDB (moto or real)
3. Retrieve and verify types are `float`, not `Decimal`
4. Ensure arithmetic operations work without explicit conversion

---

## Rollout Plan

### Phase 1: Implementation (Week 1)
- [ ] Add helper functions to `dynamodb_serializer.py`
- [ ] Enhance `.map()` method
- [ ] Write comprehensive unit tests
- [ ] Verify all existing tests still pass

### Phase 2: Documentation (Week 1)
- [ ] Update README with examples
- [ ] Add detailed guide to docs
- [ ] Update CHANGELOG

### Phase 3: Testing (Week 2)
- [ ] Integration tests with sample models
- [ ] Performance benchmarks (ensure no regression)
- [ ] Manual testing with real DynamoDB

### Phase 4: Release (Week 2)
- [ ] Bump version to 0.9.0
- [ ] Tag release in git
- [ ] Publish to PyPI
- [ ] Announce in release notes

---

## Success Criteria

✅ **All existing tests pass** (backward compatibility)  
✅ **New tests achieve 100% coverage** for Decimal conversion  
✅ **Documentation is clear** with examples  
✅ **No performance degradation** (< 5% overhead acceptable)  
✅ **Real-world validation** with production-like models  

---

## Common Pitfalls to Avoid

❌ **Don't convert in property getters** - breaks object identity  
❌ **Don't ignore backward compatibility** - preserve Decimal when no hint  
❌ **Don't forget nested structures** - handle Dict[str, Dict[str, float]]  
❌ **Don't skip integration tests** - unit tests alone aren't enough  
❌ **Don't forget edge cases** - None values, empty dicts, mixed types  

---

**This enhancement will make boto3-assist significantly more developer-friendly!** 🚀
