"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.

Exception classes for boto3-assist.
"""

# Import legacy exceptions for backward compatibility
from boto3_assist.errors.custom_exceptions import (
    DbFailures,
    Error,
    FileNotFound,
    InvalidHttpMethod,
    InvalidRoutePath,
)

# Import all exceptions for easy access
from boto3_assist.errors.exceptions import (  # Base exceptions; DynamoDB exceptions; Validation exceptions; Serialization exceptions; S3 exceptions; Cognito exceptions; Connection exceptions; Configuration exceptions
    AuthenticationError,
    AuthorizationError,
    AWSCredentialsError,
    Boto3AssistError,
    CognitoError,
    ConditionalCheckFailedError,
    ConfigurationError,
    ConnectionError,
    ConnectionPoolExhaustedError,
    DecimalConversionError,
    DynamoDBConnectionError,
    DynamoDBError,
    DynamoDBQueryError,
    DynamoDBTableNotFoundError,
    InvalidConfigurationError,
    InvalidKeyError,
    InvalidParameterError,
    ItemNotFoundError,
    MissingParameterError,
    ModelMappingError,
    S3BucketNotFoundError,
    S3Error,
    S3ObjectNotFoundError,
    S3UploadError,
    SerializationError,
    TokenValidationError,
    ValidationError,
)

__all__ = [
    # Base exceptions
    "Boto3AssistError",
    "Error",  # Legacy alias
    # DynamoDB exceptions
    "DynamoDBError",
    "DbFailures",  # Legacy alias
    "ItemNotFoundError",
    "ConditionalCheckFailedError",
    "DynamoDBConnectionError",
    "DynamoDBQueryError",
    "DynamoDBTableNotFoundError",
    # Validation exceptions
    "ValidationError",
    "InvalidParameterError",
    "MissingParameterError",
    "InvalidKeyError",
    # Serialization exceptions
    "SerializationError",
    "ModelMappingError",
    "DecimalConversionError",
    # S3 exceptions
    "S3Error",
    "S3BucketNotFoundError",
    "S3ObjectNotFoundError",
    "S3UploadError",
    # Cognito exceptions
    "CognitoError",
    "AuthenticationError",
    "AuthorizationError",
    "TokenValidationError",
    # Connection exceptions
    "ConnectionError",
    "ConnectionPoolExhaustedError",
    "AWSCredentialsError",
    # Configuration exceptions
    "ConfigurationError",
    "InvalidConfigurationError",
    # Legacy exceptions
    "InvalidHttpMethod",
    "InvalidRoutePath",
    "FileNotFound",
]
