"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger


from boto3_assist.cloudwatch.cloudwatch_connection_tracker import (
    CloudWatchConnectionTracker,
)
from boto3_assist.connection import Connection

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch import CloudWatchClient, CloudWatchServiceResource
else:
    CloudWatchClient = object
    CloudWatchServiceResource = object


logger = Logger()
tracker: CloudWatchConnectionTracker = CloudWatchConnectionTracker()


class CloudWatchConnection(Connection):
    """CW Environment"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            service_name="cloudwatch",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.__client: CloudWatchClient | None = None
        self.__resource: CloudWatchServiceResource | None = None

        self.raise_on_error: bool = True

    @property
    def client(self) -> CloudWatchClient:
        """CloudWatch Client Connection"""
        if self.__client is None:
            logger.info("Creating CloudWatch Client")
            self.__client = self.session.client

        if self.raise_on_error and self.__client is None:
            raise RuntimeError("CloudWatch Client is not available")
        return self.__client

    @client.setter
    def client(self, value: CloudWatchClient):
        logger.info("Setting CloudWatch Client")
        self.__client = value

    @property
    def resource(self) -> CloudWatchServiceResource:
        """CloudWatch Resource Connection"""
        if self.__resource is None:
            logger.info("Creating CloudWatch Resource")
            self.__resource = self.session.resource

        if self.raise_on_error and self.__resource is None:
            raise RuntimeError("CloudWatch Resource is not available")

        return self.__resource

    @resource.setter
    def resource(self, value: CloudWatchServiceResource):
        logger.info("Setting CloudWatch Resource")
        self.__resource = value
