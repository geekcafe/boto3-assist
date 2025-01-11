"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger

from boto3_assist.connection import Connection

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client, S3ServiceResource
else:
    S3Client = object
    S3ServiceResource = object


logger = Logger()


class S3Connection(Connection):
    """Connection"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            service_name="s3",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_end_point_url=aws_end_point_url,
        )

        self.__client: S3Client | None = None
        self.__resource: S3ServiceResource | None = None

    @property
    def client(self) -> S3Client:
        """Client Connection"""
        if self.__client is None:
            self.__client = self.session.client

        return self.__client

    @client.setter
    def client(self, value: S3Client):
        logger.info("Setting Client")
        self.__client = value

    @property
    def resource(self) -> S3ServiceResource:
        """Resource Connection"""
        if self.__resource is None:
            logger.info("Creating Resource")
            self.__resource = self.session.resource

        if self.raise_on_error and self.__resource is None:
            raise RuntimeError("Resource is not available")

        return self.__resource

    @resource.setter
    def resource(self, value: S3ServiceResource):
        logger.info("Setting Resource")
        self.__resource = value
