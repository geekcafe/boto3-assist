"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional

from aws_lambda_powertools import Logger
from boto3_assist.boto3session import Boto3SessionManager
from boto3_assist.environment_services.environment_variables import (
    EnvironmentVariables,
)
from boto3_assist.cloudwatch.cloudwatch_connection_tracker import (
    CloudWatchConnectionTracker,
)


logger = Logger()
tracker: CloudWatchConnectionTracker = CloudWatchConnectionTracker()


class Connection:
    """Boto 3 Connection"""

    def __init__(
        self,
        *,
        service_name: Optional[str] = None,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        self.aws_profile = aws_profile or EnvironmentVariables.AWS.profile()
        self.aws_region = aws_region or EnvironmentVariables.AWS.region()

        self.aws_access_key_id = (
            aws_access_key_id or EnvironmentVariables.AWS.DynamoDB.aws_access_key_id()
        )
        self.aws_secret_access_key = (
            aws_secret_access_key
            or EnvironmentVariables.AWS.DynamoDB.aws_secret_access_key()
        )
        self.__session: Boto3SessionManager | None = None

        self.__service_name: str | None = service_name
        self.raise_on_error: bool = True

    def setup(self, setup_source: Optional[str] = None) -> None:
        """
        Setup the environment.  Automatically called via init.
        You can run setup at anytime with new parameters.
        Args: setup_source: Optional[str] = None
            Defines the source of the setup.  Useful for logging.
        Returns: None
        """

        logger.debug(
            {
                "metric_filter": f"{self.service_name}_connection_setup",
                "source": f"{self.service_name} Connection",
                "aws_profile": self.aws_profile,
                "aws_region": self.aws_region,
                "setup_source": setup_source,
            }
        )

        self.__session = Boto3SessionManager(
            service_name=self.service_name,
            aws_profile=self.aws_profile,
            aws_region=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

        tracker.increment_connection()

        self.raise_on_error = EnvironmentVariables.AWS.DynamoDB.raise_on_error_setting()

    @property
    def service_name(self) -> str:
        """Service Name"""
        if self.__service_name is None:
            raise RuntimeError("Service Name is not available")
        return self.__service_name

    @service_name.setter
    def service_name(self, value: str):
        logger.debug("Setting Service Name")
        self.__service_name = value

    @property
    def session(self) -> Boto3SessionManager:
        """Session"""
        if self.__session is None:
            self.setup(setup_source="session init")

        if self.__session is None:
            raise RuntimeError("Session is not available")
        return self.__session
