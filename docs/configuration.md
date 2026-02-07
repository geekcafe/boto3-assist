# Configuration Management

boto3-assist provides a centralized configuration system that makes it easy to manage settings across your application.

## Quick Start

### Using Environment Variables (Recommended)

The simplest way to configure boto3-assist is through environment variables:

```python
from boto3_assist.config import get_config
from boto3_assist.dynamodb import DynamoDB

# Load configuration from environment variables
config = get_config()

# Use configuration values
db = DynamoDB(
    aws_region=config.aws.region,
    aws_profile=config.aws.profile
)
```

### Programmatic Configuration

You can also create configuration programmatically:

```python
from boto3_assist.config import Boto3AssistConfig, AWSConfig, DynamoDBConfig, set_config

# Create custom configuration
custom_config = Boto3AssistConfig(
    aws=AWSConfig(
        region='us-west-2',
        profile='my-profile'
    ),
    dynamodb=DynamoDBConfig(
        single_table='my-table',
        raise_on_error=True
    )
)

# Set as global configuration
set_config(custom_config)

# Now all code using get_config() will use this configuration
config = get_config()
```

## Configuration Structure

The configuration is organized into logical sections:

```python
config = get_config()

# AWS general settings
config.aws.region              # AWS region
config.aws.profile             # AWS profile name
config.aws.account_id          # AWS account ID
config.aws.endpoint_url        # Custom endpoint URL
config.aws.access_key_id       # AWS access key (for local dev)
config.aws.secret_access_key   # AWS secret key (for local dev)

# DynamoDB settings
config.dynamodb.single_table        # Single table name
config.dynamodb.endpoint_url        # DynamoDB endpoint (for local dev)
config.dynamodb.raise_on_error      # Raise exceptions on errors
config.dynamodb.convert_decimals    # Auto-convert Decimal types
config.dynamodb.log_item_size       # Log item sizes

# S3 settings
config.s3.signature_version    # S3 signature version
config.s3.endpoint_url         # S3 endpoint (for local dev)

# Cognito settings
config.cognito.user_pool       # Cognito user pool ID

# Logging settings
config.logging.log_level           # Log level (INFO, DEBUG, etc.)
config.logging.enable_stack_trace  # Enable stack traces

# Environment
config.environment             # Environment name (dev, prod, etc.)
```

## Environment Variables

### AWS Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | None |
| `AWS_PROFILE` | AWS profile name | None |
| `AWS_ACCOUNT_ID` | AWS account ID | None |
| `AWS_ENDPOINT_URL` | Custom AWS endpoint | None |
| `ACCESS_KEY_ID` | AWS access key (local dev only) | None |
| `SECRET_ACCESS_KEY` | AWS secret key (local dev only) | None |

### DynamoDB Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DYNAMODB_SINGLE_TABLE` | Single table name | None |
| `AWS_DYNAMODB_ENDPOINT_URL` | DynamoDB endpoint (local dev) | None |
| `AWS_DYNAMODB_ACCESS_KEY_ID` | DynamoDB access key (local dev) | None |
| `AWS_DYNAMODB_SECRET_ACCESS_KEY` | DynamoDB secret key (local dev) | None |
| `RAISE_ON_DB_ERROR` | Raise exceptions on DB errors | `true` |
| `DYNAMODB_CONVERT_DECIMALS` | Auto-convert Decimal types | `true` |
| `LOG_DYNAMODB_ITEM_SIZE` | Log DynamoDB item sizes | `false` |

### S3 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_S3_SIGNATURE_VERSION` | S3 signature version | None |

### Cognito Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `COGNITO_USER_POOL` | Cognito user pool ID | None |

### Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENABLE_STACK_TRACE` | Enable stack traces | `false` |

### General Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | Empty string |

## Usage Patterns

### Pattern 1: Global Configuration

Use the global configuration singleton for simple applications:

```python
from boto3_assist.config import get_config
from boto3_assist.dynamodb import DynamoDB

# Get global configuration
config = get_config()

# Use throughout your application
db = DynamoDB(aws_region=config.aws.region)
```

### Pattern 2: Per-Module Configuration

Create configuration instances for different modules:

```python
from boto3_assist.config import Boto3AssistConfig

# Load configuration
config = Boto3AssistConfig.from_environment()

# Pass to modules
def setup_database(config):
    return DynamoDB(
        aws_region=config.aws.region,
        aws_end_point_url=config.dynamodb.endpoint_url
    )

db = setup_database(config)
```

### Pattern 3: Testing Configuration

Override configuration for testing:

```python
import unittest
from boto3_assist.config import Boto3AssistConfig, AWSConfig, DynamoDBConfig, set_config, reset_config

class TestMyService(unittest.TestCase):
    def setUp(self):
        # Set test configuration
        test_config = Boto3AssistConfig(
            aws=AWSConfig(region='us-east-1'),
            dynamodb=DynamoDBConfig(
                endpoint_url='http://localhost:8000',
                single_table='test-table'
            )
        )
        set_config(test_config)

    def tearDown(self):
        # Reset to environment configuration
        reset_config()

    def test_something(self):
        config = get_config()
        self.assertEqual(config.aws.region, 'us-east-1')
```

### Pattern 4: Multi-Environment Configuration

Handle different environments:

```python
from boto3_assist.config import get_config

config = get_config()

if config.environment == 'production':
    # Production-specific settings
    db = DynamoDB(aws_region='us-east-1')
elif config.environment == 'development':
    # Development-specific settings
    db = DynamoDB(
        aws_region='us-east-1',
        aws_end_point_url='http://localhost:8000'
    )
```

## Configuration in Different Environments

### Local Development

Create a `.env` file:

```bash
# .env
AWS_REGION=us-east-1
AWS_PROFILE=dev-profile
DYNAMODB_SINGLE_TABLE=local-table
AWS_DYNAMODB_ENDPOINT_URL=http://localhost:8000
AWS_DYNAMODB_ACCESS_KEY_ID=dummy_key
AWS_DYNAMODB_SECRET_ACCESS_KEY=dummy_secret
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

Load it in your application:

```python
from dotenv import load_dotenv
from boto3_assist.config import get_config

# Load .env file
load_dotenv()

# Configuration is now loaded from .env
config = get_config()
```

### Docker Containers

Set environment variables in `docker-compose.yml`:

```yaml
version: '3.8'
services:
  app:
    image: my-app
    environment:
      - AWS_REGION=us-east-1
      - DYNAMODB_SINGLE_TABLE=my-table
      - AWS_DYNAMODB_ENDPOINT_URL=http://dynamodb:8000
      - ENVIRONMENT=docker
```

### AWS Lambda

Set environment variables in your Lambda configuration:

```python
# Lambda handler
from boto3_assist.config import get_config
from boto3_assist.dynamodb import DynamoDB

def lambda_handler(event, context):
    # Configuration loaded from Lambda environment variables
    config = get_config()

    db = DynamoDB(aws_region=config.aws.region)
    # ... rest of handler
```

### Kubernetes

Set environment variables in your deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        env:
        - name: AWS_REGION
          value: "us-east-1"
        - name: DYNAMODB_SINGLE_TABLE
          value: "my-table"
        - name: ENVIRONMENT
          value: "production"
```

## Advanced Usage

### Inspecting Configuration

View current configuration:

```python
from boto3_assist.config import get_config

config = get_config()

# Convert to dictionary (safe - excludes credentials)
config_dict = config.to_dict()
print(config_dict)

# Output:
# {
#     'aws': {'region': 'us-east-1', 'profile': None, ...},
#     'dynamodb': {'single_table': 'my-table', ...},
#     ...
# }
```

### Reloading Configuration

Reload configuration after environment changes:

```python
import os
from boto3_assist.config import get_config, reset_config

# Initial configuration
config = get_config()
print(config.aws.region)  # us-east-1

# Change environment variable
os.environ['AWS_REGION'] = 'us-west-2'

# Reset and reload
reset_config()
config = get_config()
print(config.aws.region)  # us-west-2
```

### Partial Configuration

You can create partial configurations:

```python
from boto3_assist.config import Boto3AssistConfig, DynamoDBConfig

# Only configure DynamoDB
config = Boto3AssistConfig(
    dynamodb=DynamoDBConfig(
        single_table='my-table',
        raise_on_error=False
    )
)

# Other settings use defaults
print(config.aws.region)  # None
print(config.dynamodb.single_table)  # 'my-table'
```

## Migration from Direct Environment Access

### Before (Direct os.getenv)

```python
import os
from boto3_assist.dynamodb import DynamoDB

region = os.getenv('AWS_REGION')
profile = os.getenv('AWS_PROFILE')
table = os.getenv('DYNAMODB_SINGLE_TABLE')

db = DynamoDB(
    aws_region=region,
    aws_profile=profile
)
```

### After (Using Configuration)

```python
from boto3_assist.config import get_config
from boto3_assist.dynamodb import DynamoDB

config = get_config()

db = DynamoDB(
    aws_region=config.aws.region,
    aws_profile=config.aws.profile
)

# Access single table name
table = config.dynamodb.single_table
```

### Benefits of Configuration System

1. **Type Safety**: Configuration values have proper types
2. **Centralized**: All configuration in one place
3. **Testable**: Easy to mock and override for tests
4. **Discoverable**: IDE autocomplete shows available settings
5. **Documented**: Clear documentation of all settings
6. **Validated**: Can add validation logic in one place
7. **Flexible**: Supports both environment variables and programmatic configuration

## Best Practices

### 1. Use get_config() for Application Code

```python
# Good
from boto3_assist.config import get_config

config = get_config()
db = DynamoDB(aws_region=config.aws.region)
```

### 2. Use set_config() for Tests

```python
# Good - explicit test configuration
from boto3_assist.config import set_config, Boto3AssistConfig

test_config = Boto3AssistConfig(...)
set_config(test_config)
```

### 3. Don't Hardcode Configuration

```python
# Bad
db = DynamoDB(aws_region='us-east-1')

# Good
config = get_config()
db = DynamoDB(aws_region=config.aws.region)
```

### 4. Use Environment Variables for Secrets

```python
# Good - secrets from environment
config = get_config()
# config.aws.access_key_id loaded from environment

# Bad - hardcoded secrets
config.aws.access_key_id = 'AKIAIOSFODNN7EXAMPLE'
```

### 5. Document Required Environment Variables

Create a `.env.example` file:

```bash
# .env.example
AWS_REGION=us-east-1
AWS_PROFILE=
DYNAMODB_SINGLE_TABLE=
ENVIRONMENT=development
```

## Troubleshooting

### Configuration Not Loading

If configuration isn't loading from environment variables:

```python
from boto3_assist.config import get_config, reset_config

# Force reload
reset_config()
config = get_config()

# Check values
print(config.to_dict())
```

### Environment Variables Not Set

Check if environment variables are set:

```python
import os

print(f"AWS_REGION: {os.getenv('AWS_REGION')}")
print(f"DYNAMODB_SINGLE_TABLE: {os.getenv('DYNAMODB_SINGLE_TABLE')}")
```

### Configuration in Tests

If tests are using wrong configuration:

```python
def setUp(self):
    # Always reset before setting test config
    reset_config()
    set_config(test_config)

def tearDown(self):
    # Always reset after tests
    reset_config()
```

## Backward Compatibility

The configuration system is fully backward compatible:

- Existing code using `os.getenv()` continues to work
- Existing code using `EnvironmentVariables` class continues to work
- New configuration system is opt-in
- No breaking changes to existing APIs

You can gradually migrate to the new configuration system at your own pace.
