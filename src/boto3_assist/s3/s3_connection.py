"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger
from boto3_assist.boto3session import Boto3SessionManager
from boto3_assist.environment_services.environment_variables import (
    EnvironmentVariables,
)
from boto3_assist.connection_tracker import ConnectionTracker

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client, S3ServiceResource
else:
    S3Client = object
    S3ServiceResource = object


logger = Logger()
tracker: ConnectionTracker = ConnectionTracker(service_name="s3")


class S3Connection:
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
        self.aws_profile = aws_profile or EnvironmentVariables.AWS.profile()
        self.aws_region = aws_region or EnvironmentVariables.AWS.region()
        self.end_point_url = (
            aws_end_point_url or EnvironmentVariables.AWS.endpoint_url()
        )
        self.aws_access_key_id = (
            aws_access_key_id or EnvironmentVariables.AWS.aws_access_key_id()
        )
        self.aws_secret_access_key = (
            aws_secret_access_key or EnvironmentVariables.AWS.aws_secret_access_key()
        )
        self.__session: Boto3SessionManager | None = None
        self.__client: S3Client | None = None
        self.__resource: S3ServiceResource | None = None

        self.raise_on_error: bool = True

    def setup(self, setup_source: Optional[str] = None) -> None:
        """
        Setup the environment.  Automatically called via init.
        You can run setup at anytime with new parameters.
        Args: setup_source: Optional[str] = None
            Defines the source of the setup.  Useful for logging.
        Returns: None
        """

        self.__session = Boto3SessionManager(
            service_name="s3",
            aws_profile=self.aws_profile,
            aws_region=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_endpoint_url=self.end_point_url,
        )

        tracker.increment_connection()

        self.raise_on_error = False

    @property
    def session(self) -> Boto3SessionManager:
        """Session"""
        if self.__session is None:
            self.setup(setup_source="session init")

        if self.__session is None:
            raise RuntimeError("Session is not available")
        return self.__session

    @property
    def client(self) -> S3Client:
        """Client Connection"""
        if self.__client is None:
            logger.info("Creating Client")
            self.__client = self.session.client

        if self.raise_on_error and self.__client is None:
            raise RuntimeError("Client is not available")
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
