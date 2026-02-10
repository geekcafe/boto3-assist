# Type Hints Improvements - Tasks

## Overview
Add comprehensive type hints to boto3-assist DynamoDB module to improve IDE support and reduce mypy errors from 59 to <12.

## Task List

### Phase 1: Setup and Core Type Definitions

- [x] 1. Add TypedDict definitions and imports
  - Add all necessary typing imports at top of `src/boto3_assist/dynamodb/dynamodb.py`
  - Create `DynamoDBKey` TypedDict for primary keys
  - Create `QueryResponse` TypedDict for query operation responses
  - Create `GetResponse` TypedDict for get operation responses
  - Create `TransactWriteOperation` TypedDict for transaction operations
  - Add TypeVar `T` bound to `DynamoDBModelBase` for generic support
  - **Validates**: Requirements AC-3 (TypedDict for Structured Data)

### Phase 2: Core CRUD Methods (Priority 1)

- [x] 2. Add type hints to `get()` method
  - Add `@overload` decorator for dict return (when model_class=None)
  - Add `@overload` decorator for model return (when model_class=Type[T])
  - Update implementation signature with proper types
  - Test IDE autocomplete shows correct return type
  - **Validates**: Requirements US-1, US-3, AC-1, AC-4

- [x] 3. Add type hints to `save()` method
  - Add Union type for item parameter: `Union[Dict[str, Any], DynamoDBModelBase]`
  - Add proper return type: `Dict[str, Any]`
  - Update all parameter types
  - **Validates**: Requirements US-1, AC-1

- [x] 4. Add type hints to `query()` method
  - Update return type to `QueryResponse`
  - Add proper parameter types
  - Update docstring if needed
  - **Validates**: Requirements US-1, AC-1, AC-3

- [x] 5. Add type hints to `update_item()` method
  - Add proper dict types for parameters
  - Add return type: `Dict[str, Any]`
  - **Validates**: Requirements US-1, AC-1

- [x] 6. Add type hints to `delete()` method
  - Add proper parameter types
  - Add return type: `Dict[str, Any]`
  - **Validates**: Requirements US-1, AC-1

### Phase 3: Batch Operations (Priority 2)

- [x] 7. Add type hints to `batch_get_item()` method
  - Add list types for keys parameter
  - Add proper return type with list of items
  - Add model_class generic support if applicable
  - **Validates**: Requirements US-1, AC-1

- [x] 8. Add type hints to `batch_write_item()` method
  - Add proper types for operations parameter
  - Add return type for failed items
  - **Validates**: Requirements US-1, AC-1

### Phase 4: Transaction Operations (Priority 2)

- [x] 9. Add type hints to `transact_write_items()` method
  - Use `TransactWriteOperation` TypedDict for operations
  - Add proper parameter and return types
  - **Validates**: Requirements US-1, AC-1, AC-3

- [x] 10. Add type hints to `transact_get_items()` method
  - Add TypedDict for transaction get operations
  - Add proper parameter and return types
  - **Validates**: Requirements US-1, AC-1, AC-3

### Phase 5: Helper Methods (Priority 3)

- [x] 11. Add type hints to helper methods
  - `query_by_criteria()` - Add model types
  - `has_more_records()` - Add bool return type
  - `last_key()` - Add Optional[Dict[str, Any]] return type
  - `items()` - Add List[Dict[str, Any]] return type
  - `item()` - Add Optional[Dict[str, Any]] return type
  - **Validates**: Requirements US-1, AC-1

### Phase 6: Validation and Testing

- [x] 12. Run mypy and fix critical errors
  - Run: `mypy src/boto3_assist/dynamodb/ --ignore-missing-imports`
  - Fix any critical type errors
  - Target: Reduce from 59 errors to <12 errors
  - Document remaining acceptable errors
  - **Validates**: Requirements US-2, AC-2

- [x] 13. Test IDE autocomplete functionality
  - Open `src/boto3_assist/dynamodb/dynamodb.py` in IDE
  - Test autocomplete on `get()` method - verify return type changes based on model_class
  - Test autocomplete on `save()` method - verify parameter hints
  - Test autocomplete on `query()` method - verify QueryResponse structure
  - **Validates**: Requirements US-1

- [x] 14. Run all tests to ensure no breaking changes
  - Run: `pytest tests/unit/ -v`
  - Ensure all 231 tests pass
  - Fix any test failures
  - **Validates**: Requirements "Maintain 100% backward compatibility"

### Phase 7: Documentation

- [x] 15. Update documentation
  - Update `docs/type-hints-progress.md` with completion status
  - Update `PROGRESS.md` to mark type hints as complete
  - Add notes about remaining mypy errors (if any)
  - Document any limitations or known issues

## Success Criteria

- ✅ Mypy errors reduced from 59 to <12 (80% reduction)
- ✅ All 231 tests passing
- ✅ IDE autocomplete works for all public methods
- ✅ Zero breaking changes
- ✅ TypedDict definitions for common structures
- ✅ Generic support for model-based operations

## Estimated Time

- Phase 1: 1 hour
- Phase 2: 3-4 hours
- Phase 3: 2 hours
- Phase 4: 2 hours
- Phase 5: 1 hour
- Phase 6: 2 hours
- Phase 7: 0.5 hours

**Total**: 11-12 hours over 2-3 days

## Notes

- Focus on pragmatic improvements over perfection
- Accept some `Any` types where boto3 stubs are incomplete
- Use `# type: ignore` sparingly for known boto3 stub issues
- Prioritize developer experience and IDE support
- All changes must be backward compatible
