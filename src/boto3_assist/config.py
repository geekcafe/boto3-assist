"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.

Centralized configuration management for boto3-assist.
"""

from dataclasses import dataclass, field
from typing import Optional

from boto3_assist.environment_services.environment_variables import EnvironmentVariables


@dataclass
class AWSConfig:
    """AWS-specific configuration settings."""

    region: Optional[str] = None
    profile: Optional[str] = None
    account_id: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None

    @classmethod
    def from_environment(cls) -> "AWSConfig":
        """Create AWS configuration from environment variables."""
        return cls(
            region=EnvironmentVariables.AWS.region(),
            profile=EnvironmentVariables.AWS.profile(),
            account_id=EnvironmentVariables.AWS.account_id(),
            endpoint_url=EnvironmentVariables.AWS.endpoint_url(),
            access_key_id=EnvironmentVariables.AWS.aws_access_key_id(),
            secret_access_key=EnvironmentVariables.AWS.aws_secret_access_key(),
        )


@dataclass
class DynamoDBConfig:
    """DynamoDB-specific configuration settings."""

    single_table: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    raise_on_error: bool = True
    convert_decimals: bool = True
    log_item_size: bool = False

    @classmethod
    def from_environment(cls) -> "DynamoDBConfig":
        """Create DynamoDB configuration from environment variables."""
        return cls(
            single_table=EnvironmentVariables.AWS.DynamoDB.single_table(),
            endpoint_url=EnvironmentVariables.AWS.DynamoDB.endpoint_url(),
            access_key_id=EnvironmentVariables.AWS.DynamoDB.aws_access_key_id(),
            secret_access_key=EnvironmentVariables.AWS.DynamoDB.aws_secret_access_key(),
            raise_on_error=EnvironmentVariables.AWS.DynamoDB.raise_on_error_setting(),
        )


@dataclass
class S3Config:
    """S3-specific configuration settings."""

    signature_version: Optional[str] = None
    endpoint_url: Optional[str] = None

    @classmethod
    def from_environment(cls) -> "S3Config":
        """Create S3 configuration from environment variables."""
        import os

        return cls(
            signature_version=os.getenv("AWS_S3_SIGNATURE_VERSION"),
            endpoint_url=EnvironmentVariables.AWS.endpoint_url(),
        )


@dataclass
class CognitoConfig:
    """Cognito-specific configuration settings."""

    user_pool: Optional[str] = None

    @classmethod
    def from_environment(cls) -> "CognitoConfig":
        """Create Cognito configuration from environment variables."""
        return cls(
            user_pool=EnvironmentVariables.AWS.Cognito.user_pool(),
        )


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    log_level: str = "INFO"
    enable_stack_trace: bool = False

    @classmethod
    def from_environment(cls) -> "LoggingConfig":
        """Create logging configuration from environment variables."""
        import os

        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_stack_trace=os.getenv("ENABLE_STACK_TRACE", "false").lower() == "true",
        )


@dataclass
class Boto3AssistConfig:
    """
    Centralized configuration for boto3-assist.

    This class provides a single point of access to all configuration settings,
    making it easier to manage and test configuration across the library.

    Attributes:
        aws: AWS-specific configuration
        dynamodb: DynamoDB-specific configuration
        s3: S3-specific configuration
        cognito: Cognito-specific configuration
        logging: Logging configuration
        environment: Environment name (dev, staging, prod, etc.)

    Example:
        >>> config = Boto3AssistConfig.from_environment()
        >>> print(config.aws.region)
        'us-east-1'
        >>> print(config.dynamodb.single_table)
        'my-table'
    """

    aws: AWSConfig = field(default_factory=AWSConfig)
    dynamodb: DynamoDBConfig = field(default_factory=DynamoDBConfig)
    s3: S3Config = field(default_factory=S3Config)
    cognito: CognitoConfig = field(default_factory=CognitoConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    environment: str = ""

    @classmethod
    def from_environment(cls) -> "Boto3AssistConfig":
        """
        Create configuration from environment variables.

        This is the recommended way to initialize configuration in most applications.

        Returns:
            Boto3AssistConfig: Configuration loaded from environment variables

        Example:
            >>> config = Boto3AssistConfig.from_environment()
            >>> db = DynamoDB(
            ...     aws_region=config.aws.region,
            ...     aws_profile=config.aws.profile
            ... )
        """
        return cls(
            aws=AWSConfig.from_environment(),
            dynamodb=DynamoDBConfig.from_environment(),
            s3=S3Config.from_environment(),
            cognito=CognitoConfig.from_environment(),
            logging=LoggingConfig.from_environment(),
            environment=EnvironmentVariables.get_environment_setting(),
        )

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Useful for logging or debugging configuration values.

        Returns:
            dict: Configuration as dictionary

        Example:
            >>> config = Boto3AssistConfig.from_environment()
            >>> print(config.to_dict())
            {'aws': {'region': 'us-east-1', ...}, ...}
        """
        return {
            "aws": {
                "region": self.aws.region,
                "profile": self.aws.profile,
                "account_id": self.aws.account_id,
                "endpoint_url": self.aws.endpoint_url,
                # Don't include credentials in dict for security
            },
            "dynamodb": {
                "single_table": self.dynamodb.single_table,
                "endpoint_url": self.dynamodb.endpoint_url,
                "raise_on_error": self.dynamodb.raise_on_error,
                "convert_decimals": self.dynamodb.convert_decimals,
                "log_item_size": self.dynamodb.log_item_size,
            },
            "s3": {
                "signature_version": self.s3.signature_version,
                "endpoint_url": self.s3.endpoint_url,
            },
            "cognito": {
                "user_pool": self.cognito.user_pool,
            },
            "logging": {
                "log_level": self.logging.log_level,
                "enable_stack_trace": self.logging.enable_stack_trace,
            },
            "environment": self.environment,
        }


# Global configuration instance (lazy-loaded)
_config: Optional[Boto3AssistConfig] = None


def get_config() -> Boto3AssistConfig:
    """
    Get the global configuration instance.

    This function returns a singleton configuration instance loaded from
    environment variables. The configuration is cached after the first call.

    Returns:
        Boto3AssistConfig: Global configuration instance

    Example:
        >>> from boto3_assist.config import get_config
        >>> config = get_config()
        >>> print(config.aws.region)
        'us-east-1'

    Note:
        To reload configuration from environment variables, use:
        >>> reset_config()
        >>> config = get_config()
    """
    global _config
    if _config is None:
        _config = Boto3AssistConfig.from_environment()
    return _config


def reset_config() -> None:
    """
    Reset the global configuration instance.

    This forces the configuration to be reloaded from environment variables
    on the next call to get_config().

    Useful for testing or when environment variables change at runtime.

    Example:
        >>> import os
        >>> os.environ['AWS_REGION'] = 'us-west-2'
        >>> reset_config()
        >>> config = get_config()
        >>> print(config.aws.region)
        'us-west-2'
    """
    global _config
    _config = None


def set_config(config: Boto3AssistConfig) -> None:
    """
    Set a custom configuration instance.

    This allows you to provide a custom configuration instead of loading
    from environment variables. Useful for testing or programmatic configuration.

    Args:
        config: Custom configuration instance

    Example:
        >>> custom_config = Boto3AssistConfig(
        ...     aws=AWSConfig(region='us-west-2'),
        ...     dynamodb=DynamoDBConfig(single_table='my-table')
        ... )
        >>> set_config(custom_config)
        >>> config = get_config()
        >>> print(config.aws.region)
        'us-west-2'
    """
    global _config
    _config = config
