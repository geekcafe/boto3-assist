"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.

Comprehensive exception hierarchy for boto3-assist.
"""

from typing import Any, Dict, Optional


class Boto3AssistError(Exception):
    """
    Base exception for all boto3-assist errors.

    All custom exceptions in boto3-assist inherit from this class,
    making it easy to catch any library-specific error.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional context about the error
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"[{self.error_code}] {self.message} | Details: {self.details}"
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging or API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# DynamoDB Errors
# ============================================================================


class DynamoDBError(Boto3AssistError):
    """Base exception for DynamoDB-related errors."""

    pass


class ItemNotFoundError(DynamoDBError):
    """Raised when a DynamoDB item is not found."""

    def __init__(
        self,
        table_name: Optional[str] = None,
        key: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ):
        details: Dict[str, Any] = {}
        if table_name:
            details["table_name"] = table_name
        if key:
            details["key"] = key

        msg = message or "Item not found in DynamoDB"
        super().__init__(message=msg, error_code="ITEM_NOT_FOUND", details=details)


class ConditionalCheckFailedError(DynamoDBError):
    """Raised when a DynamoDB conditional check fails."""

    def __init__(
        self,
        condition: Optional[str] = None,
        message: Optional[str] = None,
    ):
        details = {}
        if condition:
            details["condition"] = condition

        msg = message or "DynamoDB conditional check failed"
        super().__init__(message=msg, error_code="CONDITIONAL_CHECK_FAILED", details=details)


class DynamoDBConnectionError(DynamoDBError):
    """Raised when unable to connect to DynamoDB."""

    def __init__(self, message: Optional[str] = None, original_error: Optional[Exception] = None):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)

        msg = message or "Failed to connect to DynamoDB"
        super().__init__(message=msg, error_code="DYNAMODB_CONNECTION_ERROR", details=details)


class DynamoDBQueryError(DynamoDBError):
    """Raised when a DynamoDB query fails."""

    def __init__(
        self,
        query_type: Optional[str] = None,
        message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = {}
        if query_type:
            details["query_type"] = query_type
        if original_error:
            details["original_error"] = str(original_error)

        msg = message or "DynamoDB query failed"
        super().__init__(message=msg, error_code="DYNAMODB_QUERY_ERROR", details=details)


class DynamoDBTableNotFoundError(DynamoDBError):
    """Raised when a DynamoDB table is not found."""

    def __init__(self, table_name: str, message: Optional[str] = None):
        details = {"table_name": table_name}
        msg = message or f"DynamoDB table '{table_name}' not found"
        super().__init__(message=msg, error_code="TABLE_NOT_FOUND", details=details)


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(Boto3AssistError):
    """Base exception for validation errors."""

    pass


class InvalidParameterError(ValidationError):
    """Raised when a parameter has an invalid value."""

    def __init__(
        self,
        parameter_name: str,
        value: Any,
        expected: Optional[str] = None,
        message: Optional[str] = None,
    ):
        details = {
            "parameter_name": parameter_name,
            "value": str(value),
        }
        if expected:
            details["expected"] = expected

        msg = message or f"Invalid value for parameter '{parameter_name}': {value}"
        super().__init__(message=msg, error_code="INVALID_PARAMETER", details=details)


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing."""

    def __init__(self, parameter_name: str, message: Optional[str] = None):
        details = {"parameter_name": parameter_name}
        msg = message or f"Required parameter '{parameter_name}' is missing"
        super().__init__(message=msg, error_code="MISSING_PARAMETER", details=details)


class InvalidKeyError(ValidationError):
    """Raised when a DynamoDB key is invalid."""

    def __init__(
        self,
        key_name: Optional[str] = None,
        reason: Optional[str] = None,
        message: Optional[str] = None,
    ):
        details = {}
        if key_name:
            details["key_name"] = key_name
        if reason:
            details["reason"] = reason

        msg = message or "Invalid DynamoDB key"
        super().__init__(message=msg, error_code="INVALID_KEY", details=details)


# ============================================================================
# Serialization Errors
# ============================================================================


class SerializationError(Boto3AssistError):
    """Base exception for serialization/deserialization errors."""

    pass


class ModelMappingError(SerializationError):
    """Raised when mapping data to a model fails."""

    def __init__(
        self,
        model_class: Optional[str] = None,
        field_name: Optional[str] = None,
        message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = {}
        if model_class:
            details["model_class"] = model_class
        if field_name:
            details["field_name"] = field_name
        if original_error:
            details["original_error"] = str(original_error)

        msg = message or "Failed to map data to model"
        super().__init__(message=msg, error_code="MODEL_MAPPING_ERROR", details=details)


class DecimalConversionError(SerializationError):
    """Raised when decimal conversion fails."""

    def __init__(
        self,
        value: Any,
        message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = {"value": str(value)}
        if original_error:
            details["original_error"] = str(original_error)

        msg = message or f"Failed to convert value to Decimal: {value}"
        super().__init__(message=msg, error_code="DECIMAL_CONVERSION_ERROR", details=details)


# ============================================================================
# S3 Errors
# ============================================================================


class S3Error(Boto3AssistError):
    """Base exception for S3-related errors."""

    pass


class S3BucketNotFoundError(S3Error):
    """Raised when an S3 bucket is not found."""

    def __init__(self, bucket_name: str, message: Optional[str] = None):
        details = {"bucket_name": bucket_name}
        msg = message or f"S3 bucket '{bucket_name}' not found"
        super().__init__(message=msg, error_code="S3_BUCKET_NOT_FOUND", details=details)


class S3ObjectNotFoundError(S3Error):
    """Raised when an S3 object is not found."""

    def __init__(
        self,
        bucket_name: str,
        key: str,
        message: Optional[str] = None,
    ):
        details = {"bucket_name": bucket_name, "key": key}
        msg = message or f"S3 object not found: s3://{bucket_name}/{key}"
        super().__init__(message=msg, error_code="S3_OBJECT_NOT_FOUND", details=details)


class S3UploadError(S3Error):
    """Raised when an S3 upload fails."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        key: Optional[str] = None,
        message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = {}
        if bucket_name:
            details["bucket_name"] = bucket_name
        if key:
            details["key"] = key
        if original_error:
            details["original_error"] = str(original_error)

        msg = message or "Failed to upload to S3"
        super().__init__(message=msg, error_code="S3_UPLOAD_ERROR", details=details)


# ============================================================================
# Cognito Errors
# ============================================================================


class CognitoError(Boto3AssistError):
    """Base exception for Cognito-related errors."""

    pass


class AuthenticationError(CognitoError):
    """Raised when authentication fails."""

    def __init__(self, message: Optional[str] = None, username: Optional[str] = None):
        details = {}
        if username:
            details["username"] = username

        msg = message or "Authentication failed"
        super().__init__(message=msg, error_code="AUTHENTICATION_FAILED", details=details)


class AuthorizationError(CognitoError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: Optional[str] = None,
        required_permission: Optional[str] = None,
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission

        msg = message or "Authorization failed"
        super().__init__(message=msg, error_code="AUTHORIZATION_FAILED", details=details)


class TokenValidationError(CognitoError):
    """Raised when token validation fails."""

    def __init__(self, message: Optional[str] = None, reason: Optional[str] = None):
        details = {}
        if reason:
            details["reason"] = reason

        msg = message or "Token validation failed"
        super().__init__(message=msg, error_code="TOKEN_VALIDATION_FAILED", details=details)


# ============================================================================
# Connection Errors
# ============================================================================


class ConnectionError(Boto3AssistError):
    """Base exception for connection-related errors."""

    pass


class ConnectionPoolExhaustedError(ConnectionError):
    """Raised when the connection pool is exhausted."""

    def __init__(self, pool_size: Optional[int] = None, message: Optional[str] = None):
        details = {}
        if pool_size:
            details["pool_size"] = pool_size

        msg = message or "Connection pool exhausted"
        super().__init__(message=msg, error_code="CONNECTION_POOL_EXHAUSTED", details=details)


class AWSCredentialsError(ConnectionError):
    """Raised when AWS credentials are invalid or missing."""

    def __init__(self, message: Optional[str] = None, profile: Optional[str] = None):
        details = {}
        if profile:
            details["profile"] = profile

        msg = message or "AWS credentials are invalid or missing"
        super().__init__(message=msg, error_code="AWS_CREDENTIALS_ERROR", details=details)


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(Boto3AssistError):
    """Base exception for configuration-related errors."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        config_key: Optional[str] = None,
        message: Optional[str] = None,
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key

        msg = message or "Invalid configuration"
        super().__init__(message=msg, error_code="INVALID_CONFIGURATION", details=details)


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================

# Keep old exception names for backward compatibility
Error = Boto3AssistError  # Alias for existing code
DbFailures = DynamoDBError  # Alias for existing code
