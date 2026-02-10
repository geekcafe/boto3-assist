# Type Hints Improvements - Requirements

## Overview
Add comprehensive type hints to boto3-assist core modules to improve developer experience, enable better IDE support, and catch bugs at development time.

## Current State
- **DynamoDB module**: 59 mypy errors
- **Coverage**: ~30% (estimated)
- **Main issues**: Generic `Dict[Any, Any]`, missing return types, inconsistent Optional usage

## Goals
1. Reduce mypy errors by 80% (from 59 to <12)
2. Add proper type hints to all public methods
3. Improve IDE autocomplete experience
4. Maintain 100% backward compatibility
5. Focus on practical improvements over perfection

## User Stories

### US-1: As a developer, I want IDE autocomplete for DynamoDB methods
**Priority**: Critical
**Description**: When I use DynamoDB methods, my IDE should show parameter types and return types

**Acceptance Criteria**:
- All public methods have complete type annotations
- IDE shows parameter hints when calling methods
- Return types are clearly indicated
- Optional parameters are properly marked

### US-2: As a developer, I want type checking to catch bugs early
**Priority**: High
**Description**: mypy should catch type mismatches before runtime

**Acceptance Criteria**:
- mypy runs without critical errors
- Common mistakes are caught (wrong parameter types, missing required params)
- Type errors are actionable and clear

### US-3: As a developer, I want proper types for model operations
**Priority**: High
**Description**: When working with DynamoDBModelBase, I want proper generic types

**Acceptance Criteria**:
- Model-based methods return correct model types
- IDE autocomplete works for model attributes
- Generic TypeVar used appropriately

## Acceptance Criteria

### AC-1: Core DynamoDB Methods Have Complete Type Hints
**Methods** (Priority Order):
1. ✅ `__init__()` - Already has types
2. ⏳ `get()` - Needs Generic[T] support
3. ⏳ `save()` - Needs Union types
4. ⏳ `query()` - Needs proper return type
5. ⏳ `update_item()` - Needs dict types
6. ⏳ `delete()` - Needs proper types
7. ⏳ `batch_get_item()` - Needs list types
8. ⏳ `batch_write_item()` - Needs operation types
9. ⏳ `transact_write_items()` - Needs TypedDict
10. ⏳ `transact_get_items()` - Needs TypedDict

**Acceptance**: Each method has complete parameter and return type annotations

### AC-2: Mypy Errors Reduced to <12
**Current**: 59 errors
**Target**: <12 errors (80% reduction)

**Acceptance**:
- `mypy src/boto3_assist/dynamodb/ --ignore-missing-imports` shows <12 errors
- No critical type safety issues
- Remaining errors are acceptable (boto3 stubs limitations)

### AC-3: TypedDict for Structured Data
**Target structures**:
- DynamoDB keys
- Query responses
- Batch operation requests
- Transaction operations

**Acceptance**:
- Common structures use TypedDict
- Better IDE autocomplete for dict structures
- Clear documentation of expected structure

### AC-4: Generic Support for Models
**Implementation**:
```python
T = TypeVar('T', bound=DynamoDBModelBase)

def get(self, model_class: Type[T], ...) -> Optional[T]:
    ...
```

**Acceptance**:
- Model-based operations return correct types
- IDE knows the return type
- Type checking works for model attributes

## Non-Goals
- Fixing all mypy errors (some boto3 stubs are incomplete)
- Adding types to test files
- Strict mypy mode (too restrictive)
- Breaking changes to existing APIs
- Perfect type coverage (focus on high-impact areas)

## Success Metrics
- Mypy errors: 59 → <12 (80% reduction)
- IDE autocomplete works for all public methods
- Zero breaking changes (all tests pass)
- Developer feedback positive

## Timeline
- **Phase 1**: Core methods (get, save, query) - 1 day
- **Phase 2**: Batch/transaction methods - 1 day
- **Phase 3**: Helper methods and cleanup - 0.5 days

**Total**: 2-3 days for significant improvement
