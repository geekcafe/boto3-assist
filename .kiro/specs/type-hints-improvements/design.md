# Type Hints Improvements - Design

## Overview
This document outlines a pragmatic approach to adding type hints to boto3-assist, focusing on high-impact improvements that provide immediate value.

## Design Principles

### 1. Pragmatism Over Perfection
- Focus on public APIs (80/20 rule)
- Accept some `Any` types where boto3 stubs are incomplete
- Don't fight with boto3's type stubs

### 2. Developer Experience First
- Prioritize IDE autocomplete
- Clear, actionable type errors
- Helpful type hints over technically perfect ones

### 3. Backward Compatibility
- No breaking changes
- All existing code continues to work
- Types are additive only

## Technical Approach

### Phase 1: Add TypedDict Definitions

Create common type definitions at the top of the file:

```python
from typing import TypedDict, TypeVar, Generic, Optional, Union, Dict, List, Any

# Type variable for model-based operations
T = TypeVar('T', bound='DynamoDBModelBase')

# Common DynamoDB types
class DynamoDBKey(TypedDict, total=False):
    """Primary key for DynamoDB items."""
    pk: str
    sk: str

class QueryResponse(TypedDict, total=False):
    """Response from query operations."""
    Items: List[Dict[str, Any]]
    Count: int
    ScannedCount: int
    LastEvaluatedKey: Optional[Dict[str, Any]]
    ConsumedCapacity: Optional[Dict[str, Any]]

class GetResponse(TypedDict, total=False):
    """Response from get operations."""
    Item: Optional[Dict[str, Any]]
    ConsumedCapacity: Optional[Dict[str, Any]]

# Transaction operation types
class TransactWriteOperation(TypedDict, total=False):
    """Single operation in a transaction write."""
    Put: Optional[Dict[str, Any]]
    Update: Optional[Dict[str, Any]]
    Delete: Optional[Dict[str, Any]]
    ConditionCheck: Optional[Dict[str, Any]]
```

### Phase 2: Add Generic Support for Models

Update method signatures to use generics:

```python
@overload
def get(
    self,
    *,
    table_name: str,
    key: Dict[str, Any],
    model_class: None = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    ...

@overload
def get(
    self,
    *,
    table_name: str,
    key: Dict[str, Any],
    model_class: Type[T],
    **kwargs
) -> Optional[T]:
    ...

def get(
    self,
    *,
    table_name: str,
    key: Dict[str, Any],
    model_class: Optional[Type[T]] = None,
    **kwargs
) -> Optional[Union[Dict[str, Any], T]]:
    """Get implementation..."""
    ...
```

### Phase 3: Improve Return Types

Replace generic `dict` with specific types:

**Before**:
```python
def query(self, ...) -> dict:
    ...
```

**After**:
```python
def query(self, ...) -> QueryResponse:
    ...
```

### Phase 4: Add Union Types for Flexible Parameters

**Before**:
```python
def save(self, item: dict | DynamoDBModelBase, ...) -> dict:
    ...
```

**After**:
```python
def save(
    self,
    item: Union[Dict[str, Any], DynamoDBModelBase],
    table_name: str,
    ...
) -> Dict[str, Any]:
    ...
```

## Implementation Strategy

### Priority 1: Core CRUD Methods (Day 1)

1. **get()** - Add overloads for dict vs model returns
2. **save()** - Add Union types for item parameter
3. **query()** - Add QueryResponse return type
4. **update_item()** - Add proper dict types
5. **delete()** - Add proper parameter types

### Priority 2: Batch Operations (Day 2)

6. **batch_get_item()** - Add list and response types
7. **batch_write_item()** - Add operation types
8. **transact_write_items()** - Add TypedDict for operations
9. **transact_get_items()** - Add TypedDict for operations

### Priority 3: Helper Methods (Day 2-3)

10. **query_by_criteria()** - Add model types
11. **has_more_records()** - Already simple
12. **last_key()** - Add proper return type
13. **items()** - Add list type
14. **item()** - Add dict type

## Handling Boto3 Type Stubs

### Known Issues
- Boto3 stubs are incomplete for some operations
- DynamoDB client/resource types are complex
- Some operations use `**kwargs` extensively

### Solutions
1. **Use `Any` strategically**: For boto3 internals we don't control
2. **Focus on our API surface**: Type our methods, not boto3's
3. **Use `# type: ignore` sparingly**: Only for known boto3 stub issues
4. **Document limitations**: Note where types are approximate

## Testing Strategy

### Type Checking
```bash
# Run mypy on DynamoDB module
mypy src/boto3_assist/dynamodb/ --ignore-missing-imports

# Target: <12 errors (down from 59)
```

### Runtime Testing
```bash
# Ensure all tests still pass
pytest tests/unit/ -v

# Target: 231/231 passing
```

### IDE Testing
1. Open file in IDE
2. Hover over method calls
3. Verify parameter hints appear
4. Verify return types are shown

## Success Criteria

### Quantitative
- ✅ Mypy errors: 59 → <12 (80% reduction)
- ✅ All 231 tests passing
- ✅ Zero breaking changes

### Qualitative
- ✅ IDE autocomplete works for all public methods
- ✅ Type errors are clear and actionable
- ✅ Developer experience improved

## Example: Before and After

### Before
```python
def get(self, table_name, key, model_class=None, **kwargs):
    # No type hints
    ...
```

**IDE shows**: `get(table_name, key, model_class=None, **kwargs)`
**Problems**: No parameter types, no return type, no autocomplete

### After
```python
@overload
def get(
    self,
    *,
    table_name: str,
    key: Dict[str, Any],
    model_class: None = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    ...

@overload
def get(
    self,
    *,
    table_name: str,
    key: Dict[str, Any],
    model_class: Type[T],
    **kwargs
) -> Optional[T]:
    ...
```

**IDE shows**: Full parameter types, return type based on model_class
**Benefits**: Autocomplete, type checking, better documentation

## Timeline

### Day 1 (4-6 hours)
- Add TypedDict definitions
- Implement get() with overloads
- Implement save() with Union types
- Implement query() with QueryResponse
- Implement update_item() and delete()
- Run mypy, fix critical errors

### Day 2 (4-6 hours)
- Implement batch operations
- Implement transaction operations
- Run mypy, fix remaining errors
- Test IDE autocomplete

### Day 3 (2-3 hours)
- Implement helper methods
- Final mypy cleanup
- Documentation updates
- Testing and validation

**Total**: 10-15 hours over 2-3 days
