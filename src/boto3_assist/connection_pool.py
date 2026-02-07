"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.

Connection pooling for boto3 sessions to improve Lambda performance.
"""

from typing import Dict, Optional

from aws_lambda_powertools import Logger

from .boto3session import Boto3SessionManager

logger = Logger()


class ConnectionPool:
    """
    Singleton connection pool for reusing boto3 sessions.

    Recommended for Lambda functions to minimize connection overhead and
    improve performance in warm containers.

    Example:
        >>> pool = ConnectionPool.get_instance()
        >>> session = pool.get_session(service_name="dynamodb")
        >>> client = session.client

        # Subsequent calls reuse the same session
        >>> session2 = pool.get_session(service_name="dynamodb")
        >>> assert session is session2  # Same instance
    """

    _instance: Optional["ConnectionPool"] = None

    def __init__(self):
        """Initialize connection pool. Use get_instance() instead."""
        self._connections: Dict[str, Boto3SessionManager] = {}

    @classmethod
    def get_instance(cls) -> "ConnectionPool":
        """
        Get singleton instance of the connection pool.

        Returns:
            ConnectionPool: Singleton instance
        """
        if cls._instance is None:
            logger.debug("Creating new ConnectionPool instance")
            cls._instance = ConnectionPool()
        return cls._instance

    def get_session(
        self,
        service_name: str,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_endpoint_url: Optional[str] = None,
        **kwargs,
    ) -> Boto3SessionManager:
        """
        Get or create cached session for service.

        Sessions are cached based on service_name, profile, region, and endpoint.
        Subsequent calls with the same parameters return the cached session.

        Args:
            service_name: AWS service name (e.g., 's3', 'dynamodb', 'sqs')
            aws_profile: AWS profile name (optional)
            aws_region: AWS region (optional, defaults to environment/config)
            aws_endpoint_url: Custom endpoint URL (optional, useful for moto testing)
            **kwargs: Additional Boto3SessionManager parameters

        Returns:
            Boto3SessionManager: Cached or newly created session manager

        Example:
            >>> pool = ConnectionPool.get_instance()
            >>> # First call creates new session
            >>> s3_session = pool.get_session(service_name="s3")
            >>> # Second call returns cached session
            >>> s3_session2 = pool.get_session(service_name="s3")
            >>> assert s3_session is s3_session2
        """
        key = self._make_key(service_name, aws_profile, aws_region, aws_endpoint_url)

        if key not in self._connections:
            logger.debug(
                f"Creating new session for {service_name}",
                extra={
                    "service_name": service_name,
                    "aws_profile": aws_profile,
                    "aws_region": aws_region,
                    "cache_key": key,
                },
            )
            self._connections[key] = Boto3SessionManager(
                service_name=service_name,
                aws_profile=aws_profile,
                aws_region=aws_region,
                aws_endpoint_url=aws_endpoint_url,
                **kwargs,
            )
        else:
            logger.debug(
                f"Reusing cached session for {service_name}",
                extra={
                    "service_name": service_name,
                    "cache_key": key,
                    "total_cached_sessions": len(self._connections),
                },
            )

        return self._connections[key]

    def reset(self):
        """
        Reset all connections in the pool.

        This clears all cached sessions. Useful for testing or when you need
        to force recreation of all connections.

        Warning:
            This should only be used in testing scenarios. In production Lambda
            functions, connections should persist across invocations.

        Example:
            >>> pool = ConnectionPool.get_instance()
            >>> pool.get_session(service_name="s3")
            >>> pool.reset()  # Clear all cached sessions
            >>> # Next call will create new session
            >>> pool.get_session(service_name="s3")
        """
        logger.debug(f"Resetting connection pool ({len(self._connections)} sessions)")
        self._connections.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the connection pool.

        Returns:
            Dict with pool statistics:
                - total_connections: Number of cached sessions
                - services: Number of unique services

        Example:
            >>> pool = ConnectionPool.get_instance()
            >>> pool.get_session(service_name="s3")
            >>> pool.get_session(service_name="dynamodb")
            >>> stats = pool.get_stats()
            >>> print(stats)
            {'total_connections': 2, 'services': 2}
        """
        services = set()
        for key in self._connections.keys():
            service_name = key.split(":")[0]
            services.add(service_name)

        return {"total_connections": len(self._connections), "services": len(services)}

    @staticmethod
    def _make_key(
        service_name: str,
        profile: Optional[str],
        region: Optional[str],
        endpoint: Optional[str],
    ) -> str:
        """
        Create cache key from connection parameters.

        Args:
            service_name: AWS service name
            profile: AWS profile name (or None)
            region: AWS region (or None)
            endpoint: Custom endpoint URL (or None)

        Returns:
            str: Cache key for this combination of parameters
        """
        return f"{service_name}:{profile}:{region}:{endpoint}"
