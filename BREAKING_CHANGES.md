# Breaking Changes Log

This document tracks all breaking changes made during the architectural improvements leading to version 1.0.

## Version 0.50.0 (In Progress)

### Python Version Requirement Update ⚠️

**Status**: Complete

**Breaking Changes**: Minimum Python version increased from 3.10 to 3.11

**Reason**: The codebase uses `datetime.UTC` which was introduced in Python 3.11. This provides better timezone-aware datetime handling.

**Changes Made**:
- ✅ Updated `pyproject.toml` to require Python 3.11+
- ✅ Updated GitHub Actions workflow to test Python 3.11, 3.12, 3.13
- ✅ Updated README.md to document Python 3.11+ requirement
- ✅ Added Python version badge to README

**Impact**:
- Users on Python 3.10 must upgrade to Python 3.11+ to use version 0.50.0+
- Users on Python 3.11+ are not affected
- All tests passing on Python 3.11, 3.12, and 3.13

**Migration Path**:
- If using Python 3.10: Upgrade to Python 3.11 or higher
- If using Python 3.11+: No changes required
- Last version supporting Python 3.10: 0.49.x

---

## Version 0.42.0 (In Progress)

### Critical Fix #8: Standardize Error Handling ✅

**Status**: Complete

**Breaking Changes**: None - fully backward compatible

**Changes Made**:
- ✅ Created comprehensive exception hierarchy in `src/boto3_assist/errors/exceptions.py`
- ✅ Added 20+ specific exception types with error codes and structured details
- ✅ All exceptions inherit from `Boto3AssistError` base class
- ✅ Maintained backward compatibility with legacy exceptions (`Error`, `DbFailures`)
- ✅ Created `src/boto3_assist/errors/__init__.py` for easy imports
- ✅ Added comprehensive documentation in `docs/error-handling.md`
- ✅ All 163 tests still passing

**New Exception Categories**:
- DynamoDB: `ItemNotFoundError`, `ConditionalCheckFailedError`, `DynamoDBQueryError`, etc.
- Validation: `InvalidParameterError`, `MissingParameterError`, `InvalidKeyError`
- Serialization: `ModelMappingError`, `DecimalConversionError`
- S3: `S3BucketNotFoundError`, `S3ObjectNotFoundError`, `S3UploadError`
- Cognito: `AuthenticationError`, `AuthorizationError`, `TokenValidationError`
- Connection: `ConnectionPoolExhaustedError`, `AWSCredentialsError`
- Configuration: `InvalidConfigurationError`

**Migration Path**:
- No migration required - new exceptions are opt-in
- Legacy exceptions still work: `Error`, `DbFailures`, `InvalidHttpMethod`, etc.
- Recommended: Start using new exceptions for better error handling
- See `docs/error-handling.md` for usage examples
- Future versions (1.0+) may deprecate legacy exceptions with warnings

---

## Migration Guide Template

When breaking changes are introduced, each will follow this format:

### Change Title

**What Changed**: Description of the change

**Why**: Reason for the change

**Before**:
```python
# Old code example
```

**After**:
```python
# New code example
```

**Migration Steps**:
1. Step-by-step migration instructions
2. Any tools or scripts to help
3. Timeline for deprecation (if applicable)

---

## Deprecation Policy

- **Minor versions** (0.x.0): May introduce new features and deprecation warnings
- **Patch versions** (0.x.y): Bug fixes only, no breaking changes
- **Version 1.0.0**: Will remove all deprecated features with clear migration path
- **Post 1.0**: Will follow semantic versioning strictly



### Critical Fix #9: Add Configuration Management ✅

**Status**: Complete

**Breaking Changes**: None - fully backward compatible

**Changes Made**:
- ✅ Created centralized configuration system in `src/boto3_assist/config.py`
- ✅ Added `Boto3AssistConfig` class with sub-configurations for AWS, DynamoDB, S3, Cognito, Logging
- ✅ Implemented `get_config()`, `set_config()`, and `reset_config()` functions
- ✅ Configuration loads from environment variables via existing `EnvironmentVariables` class
- ✅ Supports programmatic configuration for testing
- ✅ Added comprehensive documentation in `docs/configuration.md`
- ✅ All 163 tests still passing

**New Features**:
- Type-safe configuration with dataclasses
- Centralized configuration access via `get_config()`
- Easy testing with `set_config()` and `reset_config()`
- Configuration inspection with `to_dict()`
- Organized into logical sections (aws, dynamodb, s3, cognito, logging)

**Migration Path**:
- No migration required - new configuration system is opt-in
- Existing `os.getenv()` and `EnvironmentVariables` usage continues to work
- Recommended: Gradually migrate to `get_config()` for better type safety
- See `docs/configuration.md` for usage examples

---


### Critical Fix #7: Complete Type Hints 🔄

**Status**: In Progress (30% complete)

**Breaking Changes**: None - type hints are additive only

**Changes Made**:
- ✅ Created comprehensive tracking document in `docs/type-hints-progress.md`
- ✅ Identified all modules needing type hint improvements
- ✅ Documented type hint standards and best practices
- ✅ Created 4-week implementation plan
- 🔄 DynamoDB module improvements (in progress)

**Scope**:
- Add complete type hints to all public APIs
- Replace generic `Any` types with specific types
- Add TypedDict for structured dictionaries
- Use Generic/TypeVar for reusable types
- Enable stricter mypy configuration

**Estimated Completion**: 3-4 weeks

**Migration Path**:
- No migration required - type hints are backward compatible
- Existing code continues to work
- IDEs will provide better autocomplete and error detection
- Gradual improvement over time

---


### High Priority #11: Standardize Docstrings 🔄

**Status**: In Progress (3 core methods complete)

**Breaking Changes**: None - docstrings are documentation only

**Changes Made**:
- ✅ Created comprehensive docstring examples in `docs/docstring-improvements.md`
- ✅ Documented Google-style docstring standards and best practices
- ✅ Applied improved docstrings to three core DynamoDB methods:
  - `DynamoDB.get()` - Complete with examples, parameter descriptions, and usage notes
  - `DynamoDB.save()` - Complete with conditional expressions and error handling
  - `DynamoDB.query()` - Complete with pagination, GSI usage, and filtering examples
- ✅ All 163 tests still passing

**Improvements**:
- Clear one-line summaries
- Detailed descriptions explaining what methods do
- Complete Args sections with type information and examples
- Returns sections describing what's returned
- Raises sections listing possible exceptions
- Multiple Examples showing common use cases
- Note sections with important caveats and tips
- See Also sections linking to related methods

**Next Steps**:
- Apply improved docstrings to other DynamoDB methods (update_item, delete, scan, batch operations)
- Extend to S3 module methods
- Extend to Cognito module methods
- Extend to utility functions
- Generate API documentation from docstrings using Sphinx

**Migration Path**:
- No migration required - docstrings are documentation only
- Improved IDE autocomplete and documentation
- Better developer experience

---
