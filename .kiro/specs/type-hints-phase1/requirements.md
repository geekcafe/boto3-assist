# Type Hints Improvement - Phase 1

## Overview
Add comprehensive type hints to boto3-assist to improve developer experience, enable better IDE support, and catch bugs at development time.

## Current State
- **Coverage**: ~30% (estimated)
- **mypy errors**: 59 in DynamoDB module alone
- **Main issues**:
  - Generic `Dict[Any, Any]` types
  - Missing return type annotations
  - Inconsistent Optional usage
  - No TypedDict for structured data

## Goals
1. Add complete type hints to core DynamoDB methods
2. Replace `Any` with specific types where possible
3. Add TypedDict for structured dictionaries
4. Ensure mypy passes with minimal errors
5. Maintain 100% backward compatibility

## Acceptance Criteria

### 1.1 DynamoDB Core Methods Have Complete Type Hints
**Priority**: Critical
**Description**: All public methods in `DynamoDB` class have complete type annotations

**Methods to annotate**:
- `get()` - Retrieve single item
- `save()` - Save/update item
- `query()` - Query with conditions
- `update_item()` - Update specific attributes
- `delete()` - Delete item
- `scan()` - Scan table
- `batch_get()` - Batch retrieve
- `batch_write()` - Batch write
- `transact_write()` - Transaction write
- `transact_get()` - Transaction get

**Acceptance**: Each method has:
- Complete parameter type hints
- Return type annotation
- Generic types for model-based operations

### 1.2 Replace Dict[Any, Any] with Specific Types
**Priority**: High
**Description**: Replace generic dictionary types with specific TypedDict or proper types

**Target**: Reduce `Any` usage by 50%+

**Acceptance**:
- Key structures use TypedDict
- DynamoDB items properly typed
- Response types clearly defined

### 1.3 Add Generic Type Support for Models
**Priority**: High
**Description**: Use TypeVar and Generic for model-based operations

**Example**:
```python
T = TypeVar('T', bound=DynamoDBModelBase)

def get(self, model_class: Type[T], ...) -> Optional[T]:
    ...
```

**Acceptance**: IDE autocomplete works for model returns

### 1.4 Mypy Passes with Strict Settings
**Priority**: Medium
**Description**: Code passes mypy type checking with reasonable strictness

**Target**: < 10 errors in DynamoDB module

**Acceptance**:
- `mypy src/boto3_assist/dynamodb/ --ignore-missing-imports` shows < 10 errors
- No critical type safety issues

### 1.5 Documentation Updated
**Priority**: Low
**Description**: Type hints documentation and examples updated

**Acceptance**:
- `docs/type-hints-progress.md` updated with progress
- Examples show proper type usage
- README mentions type hint support

## Non-Goals
- Fixing all mypy errors (some boto3 stubs are incomplete)
- Adding types to test files (focus on production code)
- Strict mypy mode (too restrictive for current codebase)
- Breaking changes to existing APIs

## Technical Approach

### Phase 1: Core DynamoDB Methods (This Phase)
1. Add TypedDict for common structures
2. Add Generic support for model operations
3. Annotate `get()`, `save()`, `query()` methods
4. Test with mypy and fix critical issues

### Phase 2: Remaining DynamoDB Methods
1. Annotate batch operations
2. Annotate transaction methods
3. Annotate helper methods

### Phase 3: Other Modules
1. S3 module
2. Cognito module
3. Utility modules

## Success Metrics
- mypy errors reduced from 59 to < 10 in DynamoDB
- IDE autocomplete works for all public methods
- No breaking changes (all tests pass)
- Developer feedback positive

## Timeline
- Phase 1: 2-3 days
- Phase 2: 2-3 days
- Phase 3: 1 week

Total: ~2 weeks for complete coverage
