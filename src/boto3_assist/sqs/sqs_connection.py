"""
SQS Connection module.

Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

from typing import Optional, TYPE_CHECKING

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
    ) -> None:
        """
        Initialize SQS connection.

        Args:
            aws_profile: AWS profile name
            aws_region: AWS region
            aws_end_point_url: Custom endpoint URL (for LocalStack, etc.)
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
        """
        super().__init__(
            service_name="sqs",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_end_point_url=aws_end_point_url,
        )

        self.__client: SQSClient | None = None
        self.__resource: SQSServiceResource | None = None

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
