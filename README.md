# boto3 assist

[![PyPI version](https://img.shields.io/pypi/v/boto3-assist.svg)](https://pypi.org/project/boto3-assist/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/boto3-assist)](https://pepy.tech/project/boto3-assist)
[![Tests](https://github.com/geekcafe/boto3-assist/actions/workflows/test.yml/badge.svg)](https://github.com/geekcafe/boto3-assist/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **Note**: This library is in beta and subject to changes before its initial 1.0.0 release.

This library was created to make life a little easier when using boto3. It provides higher-level abstractions and utilities for common AWS operations.

## Features

### Core Capabilities
- **DynamoDB Model Mapping** - Lightweight ORM-style mapping for Python objects to DynamoDB items with comprehensive docstrings
- **Session Management** - Simplified session management for local, dev, and production environments
- **Key Generation** - Automatic primary and sort key generation for DynamoDB
- **S3 Operations** - Simplified S3 bucket and object operations
- **Cognito Integration** - User authentication and management helpers
- **Error Handling** - Comprehensive exception hierarchy with 20+ specific exception types
- **Configuration Management** - Centralized, type-safe configuration system with environment variable support

### Quality & Developer Experience
- ✅ **231 passing tests** with pytest and 55% code coverage
- ✅ **Type hints** for better IDE support (PEP 561 compliant, improvements in progress)
- ✅ **Google-style docstrings** with 40+ practical examples across all core DynamoDB methods
- ✅ **Pre-commit hooks** for automated code quality (isort, black, flake8)
- ✅ **CI/CD pipeline** with GitHub Actions testing on Python 3.11, 3.12, and 3.13
- ✅ **Comprehensive documentation** for error handling, configuration, and security best practices

## Installation

**Requirements**: Python 3.11 or higher

```sh
pip install boto3-assist
```

## Quick Start

### DynamoDB Model Mapping

```python
from boto3_assist.dynamodb import DynamoDB, DynamoDBModelBase

class User(DynamoDBModelBase):
    def __init__(self, user_id: str, email: str, name: str):
        self.user_id = user_id
        self.email = email
        self.name = name

    def pk(self) -> str:
        return f"USER#{self.user_id}"

    def sk(self) -> str:
        return f"PROFILE#{self.user_id}"

# Save a user
db = DynamoDB(table_name="my-table")
user = User(user_id="123", email="user@example.com", name="John Doe")
db.save(user)

# Retrieve a user
retrieved_user = db.get(User, pk="USER#123", sk="PROFILE#123")
```

### Session Management

```python
from boto3_assist import Boto3Session

# Lazy-loaded session that works with python-dotenv
session = Boto3Session()
dynamodb = session.resource('dynamodb')
```

## Documentation

### Core Documentation
- **[Configuration Guide](docs/configuration.md)** - Centralized configuration management with environment variables
- **[Error Handling](docs/error-handling.md)** - 20+ specific exception types with error codes and structured details
- **[Security Best Practices](SECURITY.md)** - Security guidelines and vulnerability reporting

### Examples & Guides
- **[DynamoDB Examples](examples/dynamodb/)** - CRUD operations, batch operations, transactions, conditional writes, and more
- **[S3 Examples](examples/s3/)** - Bucket and object operations
- **[Cognito Examples](examples/cognito/)** - User authentication and management
- **[CloudWatch Examples](examples/cloudwatch/)** - Log reporting and metrics

### Development Documentation
- **[Progress Tracking](PROGRESS.md)** - Detailed progress on architectural improvements
- **[Breaking Changes](BREAKING_CHANGES.md)** - Log of breaking changes (currently: Python 3.11+ requirement)
- **[Type Hints Progress](docs/type-hints-progress.md)** - Type hint improvement tracking

## Development

### Setup Development Environment

```sh
# Clone the repository
git clone https://github.com/geekcafe/boto3-assist.git
cd boto3-assist

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements.dev.txt
pip install -e .
```

### Running Tests

```sh
# Run all unit tests with coverage
pytest tests/unit/ -v --cov=src/boto3_assist --cov-report=term

# Run specific test file
pytest tests/unit/dynamodb_tests/dynamodb_test.py -v

# Run with detailed coverage report
pytest tests/unit/ -v --cov=src/boto3_assist --cov-report=term-missing

# Run pre-commit hooks
pre-commit run --all-files
```

### Test Configuration

Tests use the `moto` library to mock AWS services. You'll need:

1. A `.env.unittest` file at the project root (already included)
2. A mock AWS profile in `~/.aws/config`:

```toml
[profile moto-mock-tests]
region = us-east-1
output = json
aws_access_key_id = test
aws_secret_access_key = test
```

### Code Quality

```sh
# Run pre-commit hooks
pre-commit run --all-files

# Format code
black --line-length 100 src/ tests/ examples/
isort --profile black --line-length 100 src/ tests/ examples/

# Type checking
mypy src/boto3_assist --ignore-missing-imports

# Linting
flake8 src/ --max-line-length=100
```

## Contributing

Contributions are welcome! Please ensure:
- All tests pass: `pytest tests/unit/ -v`
- Code is formatted: `black --line-length 100 src/ tests/ examples/`
- Imports are sorted: `isort --profile black --line-length 100 src/ tests/ examples/`
- Pre-commit hooks pass: `pre-commit run --all-files`
- New features include tests and documentation
- Follow existing patterns for docstrings (Google-style) and type hints

See [PROGRESS.md](PROGRESS.md) for current development priorities.

## Roadmap to 1.0.0

See [PROGRESS.md](PROGRESS.md) for detailed progress tracking.

### Completed ✅
- ✅ **Quick Wins** (8/8): Import organization, PEP 561 support, pre-commit hooks, security docs, GitHub Actions, pytest migration, Python 3.11+ requirement
- ✅ **Error Handling**: 20+ specific exception types with error codes and structured details
- ✅ **Configuration Management**: Centralized, type-safe configuration system
- ✅ **Docstrings**: Google-style docstrings with 40+ practical examples for all core DynamoDB methods

### In Progress 🔄
- 🔄 **Type Hints**: Adding comprehensive type hints to improve IDE support (30% → 90%+ coverage)

### Planned 📋
- 📋 **API Simplification**: Config objects for complex method parameters
- 📋 **Input Validation**: Pydantic schemas for runtime validation
- 📋 **Test Coverage**: Expand from 55% to 90%+ coverage
- 📋 **Performance Benchmarks**: Benchmark suite for performance tracking
- 📋 **Debugging Utilities**: Enhanced debugging helpers for DynamoDB operations

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/geekcafe/boto3-assist/issues)
- **Security**: See [SECURITY.md](SECURITY.md) for vulnerability reporting
- **PyPI**: [boto3-assist](https://pypi.org/project/boto3-assist/)
