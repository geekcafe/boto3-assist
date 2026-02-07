# boto3-assist 1.0 Action Checklist

This checklist provides a step-by-step guide to address all findings from the architectural review.

---

## Quick Wins (Do First - ~7 hours total)

### ✅ 1. Add Import Organization (1 hour)
```bash
# Install isort
pip install isort

# Add to pyproject.toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

# Run on codebase
isort src/ tests/ examples/

# Verify
isort --check-only src/
```

**Files to update:** All Python files
**Validation:** Run `isort --check-only`

---

### ✅ 2. Add py.typed Marker (5 minutes)
```bash
# Create marker file
touch src/boto3_assist/py.typed

# Add to pyproject.toml
[tool.hatch.build.targets.wheel]
packages = ["src/boto3_assist"]
include = ["src/boto3_assist/py.typed"]
```

**Files to create:** `src/boto3_assist/py.typed`
**Validation:** File exists in package

---

### ✅ 3. Add Pre-commit Hooks (1 hour)
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see design.md for full config)
# Run
pre-commit install
pre-commit run --all-files
```

**Files to create:** `.pre-commit-config.yaml`
**Validation:** Hooks run on commit

---

### ✅ 4. Create Security Documentation (2 hours)
```bash
# Create security guide
touch docs/security.md

# Add sections:
# - Credential management best practices
# - IAM role usage
# - Environment variables
# - Secrets Manager integration
# - Security checklist
```

**Files to create:** `docs/security.md`
**Validation:** Documentation complete and reviewed

---

### ✅ 5. Remove Duplicate File (30 minutes)
```bash
# Determine which file is canonical
# Likely: dynamodb_reindexer.py

# Search for imports
grep -r "dynamodb_re_indexer" src/ tests/

# Update imports if needed
# Remove duplicate file
rm src/boto3_assist/dynamodb/dynamodb_re_indexer.py

# Run tests
pytest tests/
```

**Files to update:**
- Remove: `src/boto3_assist/dynamodb/dynamodb_re_indexer.py`
- Update any imports

**Validation:** All tests pass

---

### ✅ 6. Add GitHub Actions (2 hours)
```bash
# Create workflow directory
mkdir -p .github/workflows

# Create test.yml (see design.md for full config)
touch .github/workflows/test.yml

# Test locally with act (optional)
act -j test
```

**Files to create:** `.github/workflows/test.yml`
**Validation:** Workflow runs on push

---

## Critical Fixes (Sprint 1-2)

### 🔴 7. Complete Type Hints (1 week)

**Day 1-2: Core Modules**
- [ ] `src/boto3_assist/dynamodb/dynamodb.py`
- [ ] `src/boto3_assist/dynamodb/dynamodb_model_base.py`
- [ ] `src/boto3_assist/dynamodb/dynamodb_connection.py`

**Day 3-4: Utilities**
- [ ] `src/boto3_assist/utilities/serialization_utility.py`
- [ ] `src/boto3_assist/utilities/decimal_conversion_utility.py`
- [ ] `src/boto3_assist/utilities/string_utility.py`

**Day 5: Other Services**
- [ ] `src/boto3_assist/s3/`
- [ ] `src/boto3_assist/cognito/`
- [ ] `src/boto3_assist/sqs/`

**Validation:**
```bash
# Run mypy
mypy src/boto3_assist --strict

# Should have no errors
```

---

### 🔴 8. Standardize Error Handling (1 week)

**Day 1: Create Exception Hierarchy**
```python
# Create src/boto3_assist/errors/exceptions.py
# Define:
# - Boto3AssistError (base)
# - DynamoDBError
# - ValidationError
# - SerializationError
# - ItemNotFoundError
# - ConditionalCheckFailedError
```

**Day 2-3: Update DynamoDB Module**
- [ ] Replace generic exceptions with custom ones
- [ ] Add error codes
- [ ] Improve error messages
- [ ] Update tests

**Day 4-5: Update Other Modules**
- [ ] S3 module
- [ ] Cognito module
- [ ] Utilities

**Validation:**
```bash
# All tests pass
pytest tests/

# Error messages are clear
# Error codes are consistent
```

---

### 🔴 9. Add Configuration Management (3 hours)

**Step 1: Create Config Class**
```python
# Create src/boto3_assist/config.py
# Use Pydantic BaseSettings
# Define all configuration options
```

**Step 2: Update Modules**
- [ ] Replace `os.getenv()` calls with `get_config()`
- [ ] Update DynamoDB module
- [ ] Update other modules

**Step 3: Documentation**
- [ ] Document configuration options
- [ ] Add examples
- [ ] Update README

**Validation:**
```bash
# All tests pass
pytest tests/

# Configuration works
python -c "from boto3_assist.config import get_config; print(get_config())"
```

---

## High Priority (Sprint 3-4)

### 🟡 10. API Simplification (1 week)

**Day 1-2: Create Config Objects**
```python
# Create src/boto3_assist/dynamodb/config.py
# Define:
# - GetItemConfig
# - QueryConfig
# - SaveItemConfig
```

**Day 3-4: Update Methods**
- [ ] Update `get()` method
- [ ] Update `query()` method
- [ ] Update `save()` method
- [ ] Maintain backward compatibility

**Day 5: Documentation & Tests**
- [ ] Update documentation
- [ ] Add examples
- [ ] Update tests

**Validation:**
```bash
# All tests pass
pytest tests/

# New API works
# Old API still works (deprecated)
```

---

### 🟡 11. Standardize Docstrings (Ongoing)

**Week 1: Core Methods (5 methods/day)**
- [ ] `DynamoDB.get()`
- [ ] `DynamoDB.save()`
- [ ] `DynamoDB.query()`
- [ ] `DynamoDB.update_item()`
- [ ] `DynamoDB.delete()`

**Week 2: Model Methods**
- [ ] `DynamoDBModelBase.map()`
- [ ] `DynamoDBModelBase.merge()`
- [ ] `DynamoDBModelBase.to_resource_dictionary()`
- [ ] `DynamoDBModelBase.to_client_dictionary()`

**Week 3: Utilities**
- [ ] All utility functions
- [ ] Helper methods

**Template:**
```python
def method_name(self, param: Type) -> ReturnType:
    """
    One-line summary.

    Detailed description explaining what the method does,
    when to use it, and any important considerations.

    Args:
        param: Description of parameter including type,
            constraints, and examples.

    Returns:
        Description of return value including type and
        possible values.

    Raises:
        ExceptionType: When this exception is raised.

    Examples:
        >>> # Simple example
        >>> result = obj.method_name("value")
        >>> print(result)
        'expected output'

        >>> # Complex example
        >>> result = obj.method_name("complex")
        >>> assert result.success

    Note:
        Any important notes or warnings.
    """
```

**Validation:**
```bash
# Check docstring coverage
pydocstyle src/boto3_assist

# Generate docs
sphinx-build -b html docs/ docs/_build/
```

---

### 🟡 12. Add Input Validation (1 week)

**Day 1: Create Validation Schemas**
```python
# Create src/boto3_assist/validation/schemas.py
# Define Pydantic models for common inputs
```

**Day 2-3: Add to Services**
- [ ] UserService validation
- [ ] Other service validations

**Day 4-5: Tests & Documentation**
- [ ] Add validation tests
- [ ] Document validation
- [ ] Add examples

**Validation:**
```bash
# Tests pass
pytest tests/

# Invalid input raises clear errors
```

---

### 🟡 13. Expand Test Coverage (1 week)

**Day 1: Identify Gaps**
```bash
# Run coverage report
pytest --cov=src/boto3_assist --cov-report=html

# Open htmlcov/index.html
# Identify uncovered lines
```

**Day 2-3: Add Unit Tests**
- [ ] Cover edge cases
- [ ] Test error conditions
- [ ] Add property-based tests

**Day 4-5: Add Integration Tests**
- [ ] DynamoDB integration tests
- [ ] S3 integration tests
- [ ] End-to-end scenarios

**Validation:**
```bash
# Coverage should be 90%+
pytest --cov=src/boto3_assist --cov-report=term

# All tests pass
pytest tests/
```

---

## Polish & Documentation (Sprint 5)

### 🟢 14. Add Debugging Utilities (2 days)

**Create Debug Module**
```python
# Create src/boto3_assist/debug.py
# Add:
# - DynamoDBDebugger.explain_key()
# - DynamoDBDebugger.estimate_item_size()
# - DynamoDBDebugger.validate_gsi_projection()
```

**Validation:**
```bash
# Tests pass
pytest tests/unit/test_debug.py

# Debug utilities work
python -c "from boto3_assist.debug import DynamoDBDebugger; ..."
```

---

### 🟢 15. Performance Benchmarks (2 days)

**Create Benchmark Suite**
```python
# Create tests/benchmarks/
# Add benchmarks for:
# - Serialization
# - Connection pooling
# - Batch operations
```

**Run Benchmarks**
```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Generate report
pytest tests/benchmarks/ --benchmark-json=benchmark.json
```

**Validation:**
- Benchmarks run successfully
- Results documented

---

### 🟢 16. Final Documentation Review (3 days)

**Day 1: API Reference**
- [ ] Generate API docs with Sphinx
- [ ] Review all docstrings
- [ ] Fix any issues

**Day 2: Guides**
- [ ] Review all guides
- [ ] Update examples
- [ ] Add missing sections

**Day 3: Migration Guide**
- [ ] Document breaking changes
- [ ] Provide migration examples
- [ ] Create upgrade checklist

**Validation:**
- All documentation builds without errors
- Examples run successfully
- Migration guide is complete

---

## Pre-Release Checklist

### Code Quality
- [ ] All tests pass (100%)
- [ ] Test coverage ≥ 90%
- [ ] Type hints complete (100% of public API)
- [ ] No mypy errors in strict mode
- [ ] All pre-commit hooks pass
- [ ] No critical security issues (bandit, safety)

### Documentation
- [ ] All public methods have docstrings
- [ ] API reference generated
- [ ] All guides reviewed and updated
- [ ] Examples tested and working
- [ ] Migration guide complete
- [ ] CHANGELOG updated

### CI/CD
- [ ] GitHub Actions workflows passing
- [ ] Coverage reporting working
- [ ] Automated releases configured
- [ ] PyPI publishing tested

### Security
- [ ] Security documentation complete
- [ ] Credential handling documented
- [ ] No hardcoded secrets
- [ ] Dependencies up to date
- [ ] Security audit passed

### Performance
- [ ] Benchmarks run and documented
- [ ] No performance regressions
- [ ] Connection pooling working
- [ ] Memory usage acceptable

---

## Release Process

### 1. Version Bump
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Commit changes
git commit -m "Bump version to 1.0.0"
```

### 2. Create Release
```bash
# Tag release
git tag -a v1.0.0 -m "Release 1.0.0"

# Push tag
git push origin v1.0.0
```

### 3. Publish to PyPI
```bash
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### 4. Announce Release
- [ ] GitHub release notes
- [ ] Update documentation site
- [ ] Social media announcement
- [ ] Email to users (if applicable)

---

## Progress Tracking

Use this section to track progress:

**Quick Wins:** ☐ Not Started | ☐ In Progress | ☐ Complete
**Critical Fixes:** ☐ Not Started | ☐ In Progress | ☐ Complete
**High Priority:** ☐ Not Started | ☐ In Progress | ☐ Complete
**Polish:** ☐ Not Started | ☐ In Progress | ☐ Complete
**Release:** ☐ Not Started | ☐ In Progress | ☐ Complete

**Target 1.0 Date:** _____________
**Actual 1.0 Date:** _____________

---

## Notes

Use this space for notes, blockers, or decisions:

```
[Date] [Note]
Example: 2026-02-06 - Decided to use Pydantic for validation
```
