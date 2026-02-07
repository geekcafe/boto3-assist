"""
SQS Connection module.

Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

from typing import TYPE_CHECKING, Optional

from aws_lambda_powertools import Logger

from boto3_assist.connection import Connection

if TYPE_CHECKING:
    from mypy_boto3_sqs import SQSClient, SQSServiceResource
else:
    SQSClient = object
    SQSServiceResource = object


logger = Logger(child=True)


class SQSConnection(Connection):
    """SQS Connection wrapper."""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        use_connection_pool: bool = True,
    ) -> None:
        """
        Initialize SQS connection.

        Args:
            aws_profile: AWS profile name
            aws_region: AWS region
            aws_end_point_url: Custom endpoint URL (for LocalStack, etc.)
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            use_connection_pool: Use connection pooling (recommended for Lambda)
        """
        super().__init__(
            service_name="sqs",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_end_point_url=aws_end_point_url,
            use_connection_pool=use_connection_pool,
        )

        self.__client: SQSClient | None = None
        self.__resource: SQSServiceResource | None = None

    @classmethod
    def from_pool(
        cls,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        **kwargs,
    ) -> "SQSConnection":
        """
        Create SQS connection using connection pool (recommended for Lambda).

        This is the recommended pattern for Lambda functions as it reuses
        boto3 sessions across invocations in warm containers.

        Args:
            aws_profile: AWS profile name (optional)
            aws_region: AWS region (optional)
            aws_end_point_url: Custom endpoint URL (optional, for LocalStack/moto)
            **kwargs: Additional SQS parameters

        Returns:
            SQSConnection instance configured to use connection pool

        Example:
            >>> # Recommended pattern for Lambda
            >>> sqs = SQSConnection.from_pool()
            >>> queue = SQSQueue(sqs, queue_url="https://...")
            >>>
            >>> # Subsequent calls reuse the same connection
            >>> sqs2 = SQSConnection.from_pool()
            >>> assert sqs.session is sqs2.session
        """
        return cls(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            use_connection_pool=True,
            **kwargs,
        )

    @property
    def client(self) -> SQSClient:
        """Get SQS client."""
        if self.__client is None:
            self.__client = self.session.client
        return self.__client

    @client.setter
    def client(self, value: SQSClient) -> None:
        """Set SQS client."""
        logger.info("Setting SQS Client")
        self.__client = value

    @property
    def resource(self) -> SQSServiceResource:
        """Get SQS resource."""
        if self.__resource is None:
            logger.info("Creating SQS Resource")
            self.__resource = self.session.resource

        if self.raise_on_error and self.__resource is None:
            raise RuntimeError("SQS Resource is not available")

        return self.__resource

    @resource.setter
    def resource(self, value: SQSServiceResource) -> None:
        """Set SQS resource."""
        logger.info("Setting SQS Resource")
        self.__resource = value
