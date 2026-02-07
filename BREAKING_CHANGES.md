# Breaking Changes Log

This document tracks all breaking changes made during the architectural improvements leading to version 1.0.

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
