# boto3-assist Overview

**Version**: 0.30.0
**Status**: Beta (Pre-1.0.0)
**License**: MIT
**Python**: >=3.10

## What is boto3-assist?

boto3-assist is a comprehensive Python library that simplifies AWS service interactions by providing enhanced wrappers around boto3. It focuses on making common AWS operations easier, more Pythonic, and less error-prone, with a particular emphasis on DynamoDB single-table design patterns and serverless application development.

## Project Mission

To provide developers with production-ready, well-tested utilities that reduce boilerplate code when working with AWS services, while maintaining flexibility and following AWS best practices.

## Core Features

### 1. **DynamoDB Model Mapping** 🗄️

Advanced ORM-like functionality for DynamoDB with single-table design support:

- **Model Base Classes**: `DynamoDBModelBase` for automatic serialization/deserialization
- **Index Management**: Automatic primary key and GSI key generation
- **Type Conversion**: Automatic Decimal ↔ float/int conversion
- **Reserved Word Handling**: Automatic handling of DynamoDB reserved words
- **Projection Expressions**: Auto-generated projection expressions

```python
from boto3_assist.dynamodb import DynamoDB, DynamoDBModelBase

class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.email: str = ""
        self.name: str = ""

db = DynamoDB()
user = User().map(db.get(table_name="users", key={"pk": "user#123"}))
```

### 2. **Session Management** 🔑

Simplified AWS session and credential management:

- **Multi-Environment Support**: Dev, staging, production configurations
- **Role Assumption**: Built-in support for role chaining
- **Profile Management**: Easy switching between AWS profiles
- **Lazy Loading**: Sessions created on-demand for optimal performance

```python
from boto3_assist.dynamodb import DynamoDB

# Automatic profile/region detection from environment
db = DynamoDB()

# Explicit configuration
db = DynamoDB(
    aws_profile="production",
    aws_region="us-west-2",
    assume_role_arn="arn:aws:iam::123:role/AppRole"
)
```

### 3. **AWS Service Wrappers** ☁️

Production-ready wrappers for common AWS services:

- **DynamoDB**: CRUD operations, query, scan, batch operations
- **S3**: File upload/download, presigned URLs, event processing
- **Lambda**: Event parsing, context utilities
- **Cognito**: User authentication and management
- **CloudWatch**: Logging and metrics
- **SSM Parameter Store**: Configuration management
- **Security Hub**: Security findings management
- **EC2**: Instance management utilities

### 4. **Utilities** 🛠️

Comprehensive utility modules:

- **Serialization**: Object ↔ Dictionary conversion with type safety
- **Decimal Conversion**: Seamless DynamoDB Decimal handling
- **DateTime**: UTC-aware datetime operations
- **String**: UUID generation, case conversion
- **Numbers**: Numeric operations and validation
- **File Operations**: Safe file I/O operations

## Architecture Principles

### Layered Architecture

```
┌─────────────────────────────────────────┐
│        Frontend Applications            │
│         (React, Angular, etc.)          │
└─────────────────┬───────────────────────┘
                  │ API Gateway
┌─────────────────▼───────────────────────┐
│         AWS Lambda Handlers             │
│    (Authentication, Routing, CORS)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Service Layer                  │
│  (Business Logic, Validation, Rules)    │
│        Uses: boto3-assist               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Model Layer                    │
│      (Data Models, Serialization)       │
│        Uses: DynamoDBModelBase          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         AWS Services                    │
│  (DynamoDB, S3, Cognito, CloudWatch)    │
└─────────────────────────────────────────┘
```

### Design Patterns

1. **Single Table Design**: All DynamoDB entities in one table with composite keys
2. **Service Factory**: Centralized service creation with dependency injection
3. **Repository Pattern**: Services abstract data access from business logic
4. **DTO Pattern**: Models are data transport objects, not active records
5. **Multi-Tenancy**: Built-in tenant isolation at the model level

## Project Structure

```
boto3-assist/
├── src/boto3_assist/          # Source code
│   ├── dynamodb/              # DynamoDB utilities
│   ├── s3/                    # S3 utilities
│   ├── aws_lambda/            # Lambda utilities
│   ├── cognito/               # Cognito utilities
│   ├── cloudwatch/            # CloudWatch utilities
│   ├── ssm/                   # SSM Parameter Store
│   ├── utilities/             # Common utilities
│   └── models/                # Base model classes
├── tests/                     # Test suite
│   └── unit/                  # Unit tests
│       ├── dynamodb_tests/    # DynamoDB tests
│       ├── models_tests/      # Model tests
│       └── utilities/         # Utility tests
├── examples/                  # Usage examples
│   ├── dynamodb/              # DynamoDB examples
│   ├── cloudwatch/            # CloudWatch examples
│   └── ec2/                   # EC2 examples
├── docs/                      # Documentation
│   ├── design-patterns.md     # Architecture patterns
│   ├── defining-models.md     # Model development guide
│   ├── defining-services.md   # Service development guide
│   ├── unit-test-patterns.md  # Testing guidelines
│   ├── overview.md            # This file
│   ├── tech-debt.md           # Technical debt tracking
│   ├── roadmap.md             # Development roadmap
│   └── issues/                # Design documents
└── pyproject.toml             # Project configuration
```

## Key Statistics

- **Source Files**: 59 Python modules
- **Test Files**: 47 test modules
- **Test Coverage**: Comprehensive unit and integration tests
- **Dependencies**: Minimal, production-focused
- **Python Version**: 3.10+
- **Status**: Active development, beta stage

## Installation

### PyPI (Recommended)

```bash
pip install boto3-assist
```

### Development Installation

```bash
git clone https://github.com/geekcafe/boto3-assist.git
cd boto3-assist
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start Examples

### DynamoDB Operations

```python
from boto3_assist.dynamodb import DynamoDB, DynamoDBModelBase

# Initialize
db = DynamoDB()

# Define a model
class Product(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id: str = None
        self.name: str = ""
        self.price: float = 0.0

# Save
product = Product()
product.id = "prod_123"
product.name = "Widget"
product.price = 19.99
db.save(item=product, table_name="products")

# Retrieve
result = db.get(
    table_name="products",
    key={"pk": "product#prod_123", "sk": "product#prod_123"}
)
product = Product().map(result)

# Query
from boto3.dynamodb.conditions import Key
results = db.query(
    table_name="products",
    key=Key("pk").eq("products#") & Key("sk").begins_with("product#")
)
```

### S3 Operations

```python
from boto3_assist.s3 import S3

s3 = S3()

# Upload file
s3.object.upload_file(
    file_path="/path/to/file.txt",
    bucket_name="my-bucket",
    key="files/file.txt"
)

# Download file
s3.object.download_file(
    bucket_name="my-bucket",
    key="files/file.txt",
    file_path="/path/to/download.txt"
)

# Generate presigned URL
url = s3.object.generate_presigned_url(
    bucket_name="my-bucket",
    key="files/file.txt",
    expiration=3600
)
```

### Lambda Event Processing

```python
from boto3_assist.aws_lambda import EventInfo

def lambda_handler(event, context):
    event_info = EventInfo(event)

    # Parse API Gateway event
    body = event_info.get_body()
    headers = event_info.get_headers()

    # Parse S3 event
    if event_info.is_s3_event():
        s3_records = event_info.get_s3_records()

    # Parse DynamoDB Stream event
    if event_info.is_dynamodb_stream_event():
        records = event_info.get_dynamodb_records()
```

## Core Concepts

### Automatic Decimal Conversion

boto3-assist automatically converts DynamoDB's `Decimal` types to Python's native `int` and `float` types, eliminating common TypeErrors:

```python
# DynamoDB returns Decimals
result = db.get(...)  # {'price': Decimal('19.99'), 'quantity': Decimal('5')}

# boto3-assist converts automatically
product = Product().map(result)
product.price      # 19.99 (float)
product.quantity   # 5 (int)

# Arithmetic just works
total = product.price * product.quantity  # No TypeError!
```

### Index Management

Automatic composite key generation for single-table design:

```python
class User(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self.id: str = None
        self.email: str = ""
        self.__setup_indexes()

    def __setup_indexes(self):
        # Primary key
        primary = DynamoDBIndex()
        primary.partition_key.value = lambda: f"user#{self.id}"
        primary.sort_key.value = lambda: f"user#{self.id}"
        self.indexes.add_primary(primary)

        # GSI for email lookup
        gsi = DynamoDBIndex(index_name="gsi1")
        gsi.partition_key.value = lambda: "users#"
        gsi.sort_key.value = lambda: f"email#{self.email}"
        self.indexes.add_secondary(gsi)
```

### Service Layer Pattern

```python
from boto3_assist.dynamodb import DynamoDB

class UserService:
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name

    def get_user(self, user_id: str) -> User:
        """Get user by ID"""
        key = {"pk": f"user#{user_id}", "sk": f"user#{user_id}"}
        result = self.db.get(table_name=self.table_name, key=key)
        return User().map(result)

    def get_user_by_email(self, email: str) -> User:
        """Get user by email using GSI"""
        from boto3.dynamodb.conditions import Key
        result = self.db.query(
            table_name=self.table_name,
            index_name="gsi1",
            key=Key("gsi1_pk").eq("users#") & Key("gsi1_sk").eq(f"email#{email}")
        )
        items = result.get("Items", [])
        return User().map(items[0]) if items else None

    def create_user(self, user: User) -> User:
        """Create new user"""
        self.db.save(item=user, table_name=self.table_name, fail_if_exists=True)
        return user
```

## Testing

boto3-assist includes comprehensive test coverage using pytest and moto for AWS service mocking:

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/unit/dynamodb/

# Run with coverage
pytest --cov=src/boto3_assist

# Run with verbose output
pytest -v
```

## Configuration

### Environment Variables

boto3-assist respects standard AWS environment variables plus custom configurations:

```bash
# AWS Configuration
AWS_PROFILE=default
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# boto3-assist Configuration
DYNAMODB_CONVERT_DECIMALS=True        # Enable automatic decimal conversion
LOG_DYNAMODB_ITEM_SIZE=False          # Log item sizes for monitoring
LOG_LEVEL=INFO                        # Logging level
```

### Profile Management

Create AWS profiles in `~/.aws/config`:

```ini
[profile development]
region = us-east-1
output = json

[profile production]
region = us-west-2
output = json
role_arn = arn:aws:iam::123456789012:role/ProductionRole
source_profile = development
```

## Use Cases

### 1. Serverless SaaS Applications

Perfect for multi-tenant serverless applications using:
- API Gateway + Lambda
- DynamoDB single-table design
- Cognito authentication
- S3 for file storage

### 2. Data Processing Pipelines

Ideal for ETL and data processing:
- S3 event-driven processing
- DynamoDB Streams processing
- CloudWatch logging and metrics
- Batch operations

### 3. Microservices Architecture

Well-suited for microservices:
- Service layer abstraction
- Shared model definitions
- Centralized configuration
- Multi-environment support

### 4. Rapid Prototyping

Accelerate development with:
- Reduced boilerplate code
- Type-safe models
- Built-in best practices
- Comprehensive examples

## Community and Support

- **GitHub**: [github.com/geekcafe/boto3-assist](https://github.com/geekcafe/boto3-assist)
- **PyPI**: [pypi.org/project/boto3-assist](https://pypi.org/project/boto3-assist)
- **Documentation**: See `/docs` directory
- **Examples**: See `/examples` directory
- **Issues**: GitHub Issues for bug reports and feature requests

## Contributing

Contributions are welcome! Please:

1. Follow existing code style and patterns
2. Add tests for new features
3. Update documentation
4. Follow the design patterns outlined in `docs/design-patterns.md`

## License

MIT License - See LICENSE.txt for details

## Roadmap

See `docs/roadmap.md` for planned features and improvements.

## Version History

- **0.30.0** (Current): Enhanced decimal conversion, comprehensive testing patterns
- **0.29.0**: Improved serialization, additional AWS service support
- **Pre-1.0**: Beta stage - API subject to change

---

**Next Steps**:
- Review [Design Patterns](design-patterns.md) for architecture guidance
- See [Defining Models](defining-models.md) for model development
- Check [Unit Test Patterns](unit-test-patterns.md) for testing guidelines
- Explore `/examples` directory for practical examples
