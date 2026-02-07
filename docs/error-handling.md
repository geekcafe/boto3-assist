# Error Handling in boto3-assist

This guide explains the exception hierarchy and error handling patterns in boto3-assist.

## Exception Hierarchy

All boto3-assist exceptions inherit from `Boto3AssistError`, making it easy to catch library-specific errors:

```
Boto3AssistError (base)
├── DynamoDBError
│   ├── ItemNotFoundError
│   ├── ConditionalCheckFailedError
│   ├── DynamoDBConnectionError
│   ├── DynamoDBQueryError
│   └── DynamoDBTableNotFoundError
├── ValidationError
│   ├── InvalidParameterError
│   ├── MissingParameterError
│   └── InvalidKeyError
├── SerializationError
│   ├── ModelMappingError
│   └── DecimalConversionError
├── S3Error
│   ├── S3BucketNotFoundError
│   ├── S3ObjectNotFoundError
│   └── S3UploadError
├── CognitoError
│   ├── AuthenticationError
│   ├── AuthorizationError
│   └── TokenValidationError
├── ConnectionError
│   ├── ConnectionPoolExhaustedError
│   └── AWSCredentialsError
└── ConfigurationError
    └── InvalidConfigurationError
```

## Basic Usage

### Catching Specific Exceptions

```python
from boto3_assist.dynamodb import DynamoDB
from boto3_assist.errors import ItemNotFoundError, DynamoDBError

db = DynamoDB()

try:
    user = db.get(
        table_name="users",
        primary_key={"pk": "user#123", "sk": "user#123"}
    )
except ItemNotFoundError as e:
    print(f"User not found: {e.message}")
    print(f"Error code: {e.error_code}")
    print(f"Details: {e.details}")
except DynamoDBError as e:
    print(f"DynamoDB error: {e}")
```

### Catching All Library Errors

```python
from boto3_assist.errors import Boto3AssistError

try:
    # Any boto3-assist operation
    result = db.query(...)
except Boto3AssistError as e:
    # Catch any boto3-assist error
    print(f"boto3-assist error: {e}")
    print(f"Error details: {e.to_dict()}")
```

## Exception Attributes

All exceptions have these attributes:

- `message`: Human-readable error message
- `error_code`: Machine-readable error code (e.g., "ITEM_NOT_FOUND")
- `details`: Dictionary with additional context

### Example: Accessing Exception Details

```python
from boto3_assist.errors import ItemNotFoundError

try:
    user = db.get(table_name="users", primary_key={"pk": "user#123"})
except ItemNotFoundError as e:
    # Access structured error information
    error_dict = e.to_dict()
    # {
    #     "error_code": "ITEM_NOT_FOUND",
    #     "message": "Item not found in DynamoDB",
    #     "details": {
    #         "table_name": "users",
    #         "key": {"pk": "user#123"}
    #     }
    # }

    # Log to your logging system
    logger.error("Database error", extra=error_dict)
```

## Common Error Scenarios

### DynamoDB Errors

#### Item Not Found

```python
from boto3_assist.errors import ItemNotFoundError

try:
    item = db.get(table_name="users", primary_key={"pk": "user#999"})
except ItemNotFoundError as e:
    # Handle missing item
    print(f"Item not found in table: {e.details['table_name']}")
    return None
```

#### Conditional Check Failed

```python
from boto3_assist.errors import ConditionalCheckFailedError

try:
    db.update_item(
        table_name="users",
        key={"pk": "user#123"},
        update_expression="SET #status = :status",
        condition_expression="attribute_exists(pk)",
        expression_attribute_names={"#status": "status"},
        expression_attribute_values={":status": "active"}
    )
except ConditionalCheckFailedError as e:
    print(f"Condition failed: {e.details.get('condition')}")
    # Handle optimistic locking failure
```

### Validation Errors

#### Invalid Parameter

```python
from boto3_assist.errors import InvalidParameterError

try:
    # Some operation with validation
    result = validate_and_process(value=-1)
except InvalidParameterError as e:
    print(f"Invalid {e.details['parameter_name']}: {e.details['value']}")
    if 'expected' in e.details:
        print(f"Expected: {e.details['expected']}")
```

#### Missing Parameter

```python
from boto3_assist.errors import MissingParameterError

try:
    result = db.save(item=user_model)  # Missing table_name
except MissingParameterError as e:
    print(f"Missing required parameter: {e.details['parameter_name']}")
```

### S3 Errors

#### Object Not Found

```python
from boto3_assist.s3 import S3
from boto3_assist.errors import S3ObjectNotFoundError

s3 = S3()

try:
    content = s3.get_object(bucket="my-bucket", key="missing-file.txt")
except S3ObjectNotFoundError as e:
    print(f"File not found: s3://{e.details['bucket_name']}/{e.details['key']}")
```

#### Upload Error

```python
from boto3_assist.errors import S3UploadError

try:
    s3.upload_file(bucket="my-bucket", key="file.txt", file_path="/path/to/file")
except S3UploadError as e:
    print(f"Upload failed: {e.message}")
    if 'original_error' in e.details:
        print(f"Underlying error: {e.details['original_error']}")
```

### Cognito Errors

#### Authentication Failed

```python
from boto3_assist.cognito import CognitoAuthorizer
from boto3_assist.errors import AuthenticationError

try:
    user = authorizer.authenticate(username="user@example.com", password="wrong")
except AuthenticationError as e:
    print(f"Login failed for user: {e.details.get('username')}")
```

#### Token Validation Failed

```python
from boto3_assist.errors import TokenValidationError

try:
    claims = authorizer.validate_token(token)
except TokenValidationError as e:
    print(f"Invalid token: {e.details.get('reason')}")
```

## Error Handling Best Practices

### 1. Catch Specific Exceptions First

```python
try:
    result = db.get(...)
except ItemNotFoundError:
    # Handle missing item specifically
    return default_value
except DynamoDBError:
    # Handle other DynamoDB errors
    logger.error("Database error")
    raise
except Boto3AssistError:
    # Handle any other library error
    logger.error("Unexpected error")
    raise
```

### 2. Use Exception Details for Logging

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = db.query(...)
except Boto3AssistError as e:
    # Log structured error information
    logger.error(
        f"Operation failed: {e.message}",
        extra={
            "error_code": e.error_code,
            "details": e.details
        }
    )
```

### 3. Convert to API Responses

```python
from flask import jsonify

@app.route('/users/<user_id>')
def get_user(user_id):
    try:
        user = db.get(table_name="users", primary_key={"pk": f"user#{user_id}"})
        return jsonify(user)
    except ItemNotFoundError as e:
        return jsonify(e.to_dict()), 404
    except DynamoDBError as e:
        return jsonify(e.to_dict()), 500
```

### 4. Wrap External Errors

When catching boto3 or other external errors, wrap them in boto3-assist exceptions:

```python
import botocore.exceptions
from boto3_assist.errors import DynamoDBConnectionError

try:
    # boto3 operation
    response = dynamodb_client.get_item(...)
except botocore.exceptions.ClientError as e:
    # Wrap in library exception
    raise DynamoDBConnectionError(
        message="Failed to connect to DynamoDB",
        original_error=e
    )
```

## Backward Compatibility

For backward compatibility, the following legacy exceptions are still available:

- `Error` → alias for `Boto3AssistError`
- `DbFailures` → alias for `DynamoDBError`
- `InvalidHttpMethod` → still available
- `InvalidRoutePath` → still available
- `FileNotFound` → still available

**Note**: These legacy exceptions will be deprecated in version 1.0. Please migrate to the new exception hierarchy.

## Migration from Generic Exceptions

If your code currently catches generic exceptions like `Exception` or `RuntimeError`, consider migrating to specific boto3-assist exceptions:

### Before

```python
try:
    user = db.get(table_name="users", primary_key={"pk": "user#123"})
except Exception as e:
    print(f"Error: {e}")
```

### After

```python
from boto3_assist.errors import ItemNotFoundError, DynamoDBError

try:
    user = db.get(table_name="users", primary_key={"pk": "user#123"})
except ItemNotFoundError:
    # Handle missing item
    return None
except DynamoDBError as e:
    # Handle other database errors
    logger.error(f"Database error: {e}")
    raise
```

## Error Codes Reference

| Error Code | Exception | Description |
|------------|-----------|-------------|
| `ITEM_NOT_FOUND` | ItemNotFoundError | DynamoDB item not found |
| `CONDITIONAL_CHECK_FAILED` | ConditionalCheckFailedError | DynamoDB conditional check failed |
| `DYNAMODB_CONNECTION_ERROR` | DynamoDBConnectionError | Failed to connect to DynamoDB |
| `DYNAMODB_QUERY_ERROR` | DynamoDBQueryError | DynamoDB query failed |
| `TABLE_NOT_FOUND` | DynamoDBTableNotFoundError | DynamoDB table not found |
| `INVALID_PARAMETER` | InvalidParameterError | Invalid parameter value |
| `MISSING_PARAMETER` | MissingParameterError | Required parameter missing |
| `INVALID_KEY` | InvalidKeyError | Invalid DynamoDB key |
| `MODEL_MAPPING_ERROR` | ModelMappingError | Failed to map data to model |
| `DECIMAL_CONVERSION_ERROR` | DecimalConversionError | Decimal conversion failed |
| `S3_BUCKET_NOT_FOUND` | S3BucketNotFoundError | S3 bucket not found |
| `S3_OBJECT_NOT_FOUND` | S3ObjectNotFoundError | S3 object not found |
| `S3_UPLOAD_ERROR` | S3UploadError | S3 upload failed |
| `AUTHENTICATION_FAILED` | AuthenticationError | Authentication failed |
| `AUTHORIZATION_FAILED` | AuthorizationError | Authorization failed |
| `TOKEN_VALIDATION_FAILED` | TokenValidationError | Token validation failed |
| `CONNECTION_POOL_EXHAUSTED` | ConnectionPoolExhaustedError | Connection pool exhausted |
| `AWS_CREDENTIALS_ERROR` | AWSCredentialsError | AWS credentials invalid/missing |
| `INVALID_CONFIGURATION` | InvalidConfigurationError | Invalid configuration |

## Testing with Exceptions

When writing tests, you can easily verify exception behavior:

```python
import unittest
from boto3_assist.errors import ItemNotFoundError

class TestUserService(unittest.TestCase):
    def test_get_missing_user_raises_error(self):
        with self.assertRaises(ItemNotFoundError) as context:
            service.get_user("nonexistent-id")

        # Verify error details
        self.assertEqual(context.exception.error_code, "ITEM_NOT_FOUND")
        self.assertIn("table_name", context.exception.details)
```
