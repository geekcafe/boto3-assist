"""
Tests for ConnectionPool functionality.
"""

import pytest
import warnings
from boto3_assist.connection_pool import ConnectionPool
from boto3_assist import Connection
from boto3_assist.dynamodb import DynamoDB
from boto3_assist.s3 import S3
from boto3_assist.sqs import SQSConnection


class TestConnectionPool:
    """Test ConnectionPool singleton and session caching."""

    def setup_method(self):
        """Reset connection pool before each test."""
        pool = ConnectionPool.get_instance()
        pool.reset()

    def test_singleton_instance(self):
        """Test that ConnectionPool is a singleton."""
        pool1 = ConnectionPool.get_instance()
        pool2 = ConnectionPool.get_instance()
        assert pool1 is pool2

    def test_session_caching(self):
        """Test that sessions are cached and reused."""
        pool = ConnectionPool.get_instance()

        # First call creates new session
        session1 = pool.get_session(service_name="dynamodb")

        # Second call with same params returns cached session
        session2 = pool.get_session(service_name="dynamodb")

        assert session1 is session2

    def test_different_services_different_sessions(self):
        """Test that different services get different sessions."""
        pool = ConnectionPool.get_instance()

        dynamodb_session = pool.get_session(service_name="dynamodb")
        s3_session = pool.get_session(service_name="s3")

        assert dynamodb_session is not s3_session

    def test_different_regions_different_sessions(self):
        """Test that different regions get different sessions."""
        pool = ConnectionPool.get_instance()

        us_east_session = pool.get_session(
            service_name="dynamodb", aws_region="us-east-1"
        )
        us_west_session = pool.get_session(
            service_name="dynamodb", aws_region="us-west-2"
        )

        assert us_east_session is not us_west_session

    def test_reset_clears_cache(self):
        """Test that reset() clears all cached sessions."""
        pool = ConnectionPool.get_instance()

        # Create a session
        session1 = pool.get_session(service_name="dynamodb")

        # Reset pool
        pool.reset()

        # Next call creates new session
        session2 = pool.get_session(service_name="dynamodb")

        assert session1 is not session2

    def test_get_stats(self):
        """Test pool statistics."""
        pool = ConnectionPool.get_instance()

        # Initially empty
        stats = pool.get_stats()
        assert stats["total_connections"] == 0
        assert stats["services"] == 0

        # Add some sessions
        pool.get_session(service_name="dynamodb")
        pool.get_session(service_name="s3")
        pool.get_session(service_name="dynamodb", aws_region="us-west-2")

        stats = pool.get_stats()
        assert stats["total_connections"] == 3
        assert stats["services"] == 2  # dynamodb and s3


class TestConnectionWithPool:
    """Test Connection class with connection pool."""

    def setup_method(self):
        """Reset connection pool before each test."""
        pool = ConnectionPool.get_instance()
        pool.reset()

    def test_from_pool_factory_method(self):
        """Test Connection.from_pool() factory method."""
        conn1 = Connection.from_pool(service_name="dynamodb")
        conn2 = Connection.from_pool(service_name="dynamodb")

        # Should reuse same session
        assert conn1.session is conn2.session

    def test_use_connection_pool_parameter(self):
        """Test explicit use_connection_pool parameter."""
        conn1 = Connection(service_name="dynamodb", use_connection_pool=True)
        conn2 = Connection(service_name="dynamodb", use_connection_pool=True)

        # Should reuse same session
        assert conn1.session is conn2.session

    def test_legacy_behavior_without_pool(self):
        """Test that legacy behavior still works without pool."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            conn1 = Connection(service_name="dynamodb")
            conn2 = Connection(service_name="dynamodb")

            # Should see deprecation warnings
            assert len(w) == 2
            assert all(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )
            assert "connection pooling" in str(w[0].message).lower()

            # Should create separate sessions (legacy behavior)
            assert conn1.session is not conn2.session

    def test_no_warning_with_pool(self):
        """Test that no warning is issued when using pool."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            conn = Connection.from_pool(service_name="dynamodb")

            # Should not see any warnings
            assert len(w) == 0


class TestDynamoDBWithPool:
    """Test DynamoDB class with connection pool."""

    def setup_method(self):
        """Reset connection pool before each test."""
        pool = ConnectionPool.get_instance()
        pool.reset()

    def test_dynamodb_from_pool(self):
        """Test DynamoDB.from_pool() factory method."""
        db1 = DynamoDB.from_pool()
        db2 = DynamoDB.from_pool()

        # Should reuse same session
        assert db1.session is db2.session

    def test_dynamodb_with_endpoint_url(self):
        """Test DynamoDB.from_pool() with custom endpoint (for moto)."""
        db1 = DynamoDB.from_pool(aws_end_point_url="http://localhost:5000")
        db2 = DynamoDB.from_pool(aws_end_point_url="http://localhost:5000")

        # Should reuse same session with same endpoint
        assert db1.session is db2.session

        # Different endpoint should create different session
        db3 = DynamoDB.from_pool(aws_end_point_url="http://localhost:5001")
        assert db1.session is not db3.session

    def test_dynamodb_legacy_behavior(self):
        """Test that legacy DynamoDB() still works."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            db1 = DynamoDB()
            db2 = DynamoDB()

            # Should see deprecation warnings
            assert len(w) == 2
            assert all(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )

            # Should create separate sessions (legacy behavior)
            assert db1.session is not db2.session

    def test_dynamodb_explicit_pool_parameter(self):
        """Test DynamoDB with explicit use_connection_pool parameter."""
        db1 = DynamoDB(use_connection_pool=True)
        db2 = DynamoDB(use_connection_pool=True)

        # Should reuse same session
        assert db1.session is db2.session


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def setup_method(self):
        """Reset connection pool before each test."""
        pool = ConnectionPool.get_instance()
        pool.reset()

    def test_existing_code_still_works(self):
        """Test that existing code patterns continue to work."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            # Old pattern - should still work
            db = DynamoDB()
            assert db is not None
            assert db.session is not None

            # Old pattern with parameters
            db2 = DynamoDB(aws_region="us-east-1")
            assert db2 is not None
            assert db2.session is not None

    def test_connection_parameters_preserved(self):
        """Test that connection parameters work with pool."""
        db = DynamoDB.from_pool(
            aws_region="us-west-2", aws_end_point_url="http://localhost:5000"
        )

        assert db is not None
        assert db.session is not None


class TestS3WithPool:
    """Test S3 class with connection pool."""

    def setup_method(self):
        """Reset connection pool before each test."""
        pool = ConnectionPool.get_instance()
        pool.reset()

    def test_s3_from_pool(self):
        """Test S3.from_pool() factory method."""
        s3_1 = S3.from_pool()
        s3_2 = S3.from_pool()

        # Should reuse same session
        assert s3_1.session is s3_2.session

    def test_s3_with_endpoint_url(self):
        """Test S3.from_pool() with custom endpoint (for moto)."""
        s3_1 = S3.from_pool(aws_end_point_url="http://localhost:5000")
        s3_2 = S3.from_pool(aws_end_point_url="http://localhost:5000")

        # Should reuse same session with same endpoint
        assert s3_1.session is s3_2.session

        # Different endpoint should create different session
        s3_3 = S3.from_pool(aws_end_point_url="http://localhost:5001")
        assert s3_1.session is not s3_3.session

    def test_s3_legacy_behavior(self):
        """Test that legacy S3() still works."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            s3_1 = S3()
            s3_2 = S3()

            # Should see deprecation warnings
            assert len(w) == 2
            assert all(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )

            # Should create separate sessions (legacy behavior)
            assert s3_1.session is not s3_2.session


class TestSQSWithPool:
    """Test SQS class with connection pool."""

    def setup_method(self):
        """Reset connection pool before each test."""
        pool = ConnectionPool.get_instance()
        pool.reset()

    def test_sqs_from_pool(self):
        """Test SQSConnection.from_pool() factory method."""
        sqs1 = SQSConnection.from_pool()
        sqs2 = SQSConnection.from_pool()

        # Should reuse same session
        assert sqs1.session is sqs2.session

    def test_sqs_with_endpoint_url(self):
        """Test SQSConnection.from_pool() with custom endpoint."""
        sqs1 = SQSConnection.from_pool(aws_end_point_url="http://localhost:9324")
        sqs2 = SQSConnection.from_pool(aws_end_point_url="http://localhost:9324")

        # Should reuse same session with same endpoint
        assert sqs1.session is sqs2.session

        # Different endpoint should create different session
        sqs3 = SQSConnection.from_pool(aws_end_point_url="http://localhost:9325")
        assert sqs1.session is not sqs3.session

    def test_sqs_legacy_behavior(self):
        """Test that legacy SQSConnection() still works."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            sqs1 = SQSConnection()
            sqs2 = SQSConnection()

            # Should see deprecation warnings
            assert len(w) == 2
            assert all(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )

            # Should create separate sessions (legacy behavior)
            assert sqs1.session is not sqs2.session
