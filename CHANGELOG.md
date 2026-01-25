# Changelog

All notable changes to boto3-assist will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.36.0] - 2026-01-25

### Added
- **Connection Pooling** - New `ConnectionPool` class for reusing boto3 sessions across Lambda invocations
  - Singleton pattern caches sessions by service, profile, region, and endpoint
  - Significantly improves Lambda performance by reducing connection overhead
  - `ConnectionPool.get_instance()` - Get singleton pool instance
  - `ConnectionPool.get_session()` - Get or create cached session
  - `ConnectionPool.reset()` - Clear cache (for testing)
  - `ConnectionPool.get_stats()` - Pool statistics

- **Factory Methods** - New recommended pattern for creating connections
  - `Connection.from_pool()` - Create connection using pool (recommended for Lambda)
  - `DynamoDB.from_pool()` - Create DynamoDB connection using pool
  - `S3.from_pool()` - Create S3 connection using pool
  - `SQSConnection.from_pool()` - Create SQS connection using pool
  - All service classes support `use_connection_pool` parameter

- **Package Exports** - Added `__init__.py` files for cleaner imports
  - `from boto3_assist import Connection, ConnectionPool`
  - `from boto3_assist.dynamodb import DynamoDB`
  - `from boto3_assist.s3 import S3`
  - `from boto3_assist.sqs import SQSConnection`

### Changed
- **Deprecation Warning** - Connections created without pooling now show deprecation warning
  - Warning guides users to new `.from_pool()` pattern
  - Default will change to `use_connection_pool=True` in v2.0.0
  - Existing code continues to work unchanged

### Backward Compatibility
- ✅ All existing code works without modification
- ✅ Deprecation warnings are informational only
- ✅ No breaking changes in this release

### Migration Guide
```python
# DynamoDB
# Old pattern (still works, shows deprecation warning)
db = DynamoDB()
# New pattern (recommended for Lambda)
db = DynamoDB.from_pool()

# S3
# Old pattern (still works, shows deprecation warning)
s3 = S3()
# New pattern (recommended for Lambda)
s3 = S3.from_pool()

# SQS
# Old pattern (still works, shows deprecation warning)
sqs = SQSConnection()
# New pattern (recommended for Lambda)
sqs = SQSConnection.from_pool()

# Explicit opt-in (any service)
db = DynamoDB(use_connection_pool=True)
s3 = S3(use_connection_pool=True)
sqs = SQSConnection(use_connection_pool=True)
```

### Testing
- Added 16 new tests for connection pooling
- All 107 tests passing (91 DynamoDB + 16 connection pool)
- Comprehensive backward compatibility testing

## [0.35.0] - Previous Release

### Features
- DynamoDB operations (save, query, update, batch, transactions)
- Session management with role assumption
- Decimal conversion for DynamoDB
- Conditional expressions
- Update expressions (SET, ADD, REMOVE)
- Transaction support
- Batch operations
- Connection tracking and monitoring

---

## Upgrade Notes

### From 0.35.0 to 0.36.0
No breaking changes. Optionally migrate to `.from_pool()` pattern for better Lambda performance.

### Future Breaking Changes
- **v2.0.0** (planned): `use_connection_pool=True` will become the default
  - To preserve old behavior in v2.0.0: `Connection(service_name="...", use_connection_pool=False)`
  - Timeline: 6+ months from v0.36.0 release

---

[0.36.0]: https://github.com/geekcafe/boto3-assist/compare/v0.35.0...v0.36.0
[0.35.0]: https://github.com/geekcafe/boto3-assist/releases/tag/v0.35.0
