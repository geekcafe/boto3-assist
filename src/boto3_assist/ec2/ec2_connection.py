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
    from mypy_boto3_ec2 import Client
else:
    Client = object

SERVICE_NAME = "ec2"
logger = Logger()
tracker: ConnectionTracker = ConnectionTracker(service_name=SERVICE_NAME)


class EC2Connection:
    """DB Environment"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        self.aws_profile = aws_profile
        self.aws_region = aws_region

        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.__session: Boto3SessionManager | None = None
        self.__client: Client | None = None

        self.raise_on_error: bool = True

    def setup(self, setup_source: Optional[str] = None) -> None:
        """
        Setup the environment.  Automatically called via init.
        You can run setup at anytime with new parameters.
        Args: setup_source: Optional[str] = None
            Defines the source of the setup.  Useful for logging.
        Returns: None
        """

        logger.info(
            {
                "metric_filter": "connection_setup",
                "source": "setup",
                "aws_profile": self.aws_profile,
                "aws_region": self.aws_region,
                "setup_source": setup_source,
            }
        )

        # lazy load the session
        self.__session = Boto3SessionManager(
            service_name=SERVICE_NAME,
            aws_profile=self.aws_profile,
            aws_region=self.aws_region or EnvironmentVariables.AWS.region(),
            aws_access_key_id=self.aws_access_key_id
            or EnvironmentVariables.AWS.aws_access_key_id(),
            aws_secret_access_key=self.aws_secret_access_key
            or EnvironmentVariables.AWS.aws_secret_access_key(),
        )

        tracker.increment_connection()

        self.raise_on_error = EnvironmentVariables.AWS.DynamoDB.raise_on_error_setting()

    @property
    def session(self) -> Boto3SessionManager:
        """Session"""
        if self.__session is None:
            self.setup(setup_source="session init")

        if self.__session is None:
            raise RuntimeError("Session is not available")
        return self.__session

    @property
    def client(self) -> Client:
        """Client Connection"""
        if self.__client is None:
            logger.info("Creating Client")
            self.__client = self.session.client

        if self.raise_on_error and self.__client is None:
            raise RuntimeError("Client is not available")
        return self.__client

    @client.setter
    def client(self, value: Client):
        logger.info("Setting Client")
        self.__client = value
