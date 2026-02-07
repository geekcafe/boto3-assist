# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.41.x  | :white_check_mark: |
| < 0.41  | :x:                |

## Reporting a Vulnerability

We take the security of boto3-assist seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: boto3-assist@geekcafe.com

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will send you regular updates about our progress
- We will notify you when the vulnerability is fixed
- We may ask for additional information or guidance

## Security Best Practices

When using boto3-assist, we recommend following these security best practices:

### AWS Credentials

- **Never hardcode AWS credentials** in your code
- Use IAM roles for EC2 instances, Lambda functions, and ECS tasks
- Use environment variables or AWS credentials file for local development
- Rotate credentials regularly
- Use least-privilege IAM policies

### Connection Management

- Always use SSL/TLS for AWS connections (enabled by default)
- Validate SSL certificates (enabled by default)
- Use VPC endpoints when possible for private connectivity
- Implement connection timeouts to prevent resource exhaustion

### Data Protection

- Encrypt sensitive data at rest using AWS KMS
- Use encrypted S3 buckets for file storage
- Enable DynamoDB encryption at rest
- Sanitize user input before storing in databases
- Use parameter validation to prevent injection attacks

### Logging and Monitoring

- Enable AWS CloudTrail for API call auditing
- Use CloudWatch Logs for application logging
- Avoid logging sensitive information (credentials, PII, etc.)
- Implement log retention policies
- Monitor for unusual access patterns

### Dependency Management

- Keep boto3-assist and its dependencies up to date
- Regularly scan for known vulnerabilities using tools like `pip-audit`
- Review security advisories for boto3 and AWS SDK updates

### Code Security

- Validate and sanitize all user inputs
- Use parameterized queries for DynamoDB operations
- Implement proper error handling without exposing sensitive details
- Use type hints and static analysis tools (mypy) to catch potential issues
- Follow the principle of least privilege for all AWS operations

## Known Security Considerations

### Moto Testing Library

This library uses [moto](https://github.com/getmoto/moto) for testing AWS services. Moto is only intended for testing and should never be used in production environments.

### Decimal Conversion

When working with DynamoDB, be aware that Python's `Decimal` type is used for numeric values. Ensure proper validation when converting between `Decimal` and other numeric types to prevent precision loss or overflow issues.

### Connection Pooling

The library implements connection pooling for performance. Ensure proper cleanup of connections in long-running applications to prevent resource leaks.

## Security Updates

Security updates will be released as patch versions (e.g., 0.41.1, 0.41.2) and announced through:

- GitHub Security Advisories
- Release notes
- Email notifications to reporters

## Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors who report valid security issues will be acknowledged in our release notes (unless they prefer to remain anonymous).
