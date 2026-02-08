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
- **User Authentication / Session Mapping** - Simplified session management for local, dev, and production environments
- **DynamoDB Model Mapping** - Lightweight ORM-style mapping for Python objects to DynamoDB items
- **Key Generation** - Automatic primary and sort key generation for DynamoDB
- **S3 Operations** - Simplified S3 bucket and object operations
- **Cognito Integration** - User authentication and management helpers
- **Error Handling** - Comprehensive exception hierarchy with structured error details
- **Configuration Management** - Centralized, type-safe configuration system

### Quality & Developer Experience
- ✅ **231 passing tests** with pytest
- ✅ **55% code coverage** (expanding to 90%+)
- ✅ **Type hints** for better IDE support (PEP 561 compliant)
- ✅ **Pre-commit hooks** for code quality
- ✅ **CI/CD pipeline** with GitHub Actions
- ✅ **Comprehensive documentation** for all major features

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

- **[Configuration Guide](docs/configuration.md)** - Centralized configuration management
- **[Error Handling](docs/error-handling.md)** - Exception hierarchy and usage patterns
- **[Examples](examples/)** - Comprehensive examples for DynamoDB, S3, Cognito, and more
- **[Security Best Practices](SECURITY.md)** - Security guidelines and vulnerability reporting

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
```

### Test Configuration

Several tests use the `moto` library to mock AWS services. You'll need a `.env.unittest` file at the project root (already included in the repository).

You should also create a mock AWS profile in `~/.aws/config`:

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
- All tests pass (`pytest tests/unit/`)
- Code is formatted (`black` and `isort`)
- Pre-commit hooks pass
- New features include tests and documentation

## Roadmap to 1.0.0

See [PROGRESS.md](PROGRESS.md) for detailed progress tracking.

### Completed ✅
- Import organization with isort
- PEP 561 type hint support
- Pre-commit hooks
- Security documentation
- GitHub Actions CI/CD
- Pytest migration with coverage
- Standardized error handling
- Configuration management system

### In Progress 🔄
- Complete type hints for all modules
- Standardize docstrings (Google-style)

### Planned 📋
- API simplification with config objects
- Input validation with Pydantic
- Expand test coverage to 90%+
- Performance benchmarks
- Debugging utilities

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/geekcafe/boto3-assist/issues)
- **Security**: See [SECURITY.md](SECURITY.md) for vulnerability reporting
- **PyPI**: [boto3-assist](https://pypi.org/project/boto3-assist/)
