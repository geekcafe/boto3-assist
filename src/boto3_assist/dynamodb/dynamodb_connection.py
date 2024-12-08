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
from boto3_assist.dynamodb.dynamodb_connection_tracker import DynamoDBConnectionTracker

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
else:
    DynamoDBClient = object
    DynamoDBServiceResource = object


logger = Logger()
tracker: DynamoDBConnectionTracker = DynamoDBConnectionTracker()


class DynamoDBConnection:
    """DB Environment"""

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
            aws_end_point_url or EnvironmentVariables.AWS.DynamoDB.endpoint_url()
        )
        self.aws_access_key_id = (
            aws_access_key_id or EnvironmentVariables.AWS.DynamoDB.aws_access_key_id()
        )
        self.aws_secret_access_key = (
            aws_secret_access_key
            or EnvironmentVariables.AWS.DynamoDB.aws_secret_access_key()
        )
        self.__session: Boto3SessionManager | None = None
        self.__dynamodb_client: DynamoDBClient | None = None
        self.__dynamodb_resource: DynamoDBServiceResource | None = None

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
                "metric_filter": "db_connection_setup",
                "source": "DynamoDBConnection",
                "aws_profile": self.aws_profile,
                "aws_region": self.aws_region,
                "setup_source": setup_source,
            }
        )

        self.__session = Boto3SessionManager(
            service_name="dynamodb",
            aws_profile=self.aws_profile,
            aws_region=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_endpoint_url=self.end_point_url,
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
    def client(self) -> DynamoDBClient:
        """DynamoDB Client Connection"""
        if self.__dynamodb_client is None:
            logger.info("Creating DynamoDB Client")
            self.__dynamodb_client = self.session.client

        if self.raise_on_error and self.__dynamodb_client is None:
            raise RuntimeError("DynamoDB Client is not available")
        return self.__dynamodb_client

    @client.setter
    def client(self, value: DynamoDBClient):
        logger.info("Setting DynamoDB Client")
        self.__dynamodb_client = value

    @property
    def dynamodb_client(self) -> DynamoDBClient:
        """
        DynamoDB Client Connection
            - Backward Compatible.  You should use client instead
        """
        return self.client

    @dynamodb_client.setter
    def dynamodb_client(self, value: DynamoDBClient):
        logger.info("Setting DynamoDB Client")
        self.__dynamodb_client = value

    @property
    def resource(self) -> DynamoDBServiceResource:
        """DynamoDB Resource Connection"""
        if self.__dynamodb_resource is None:
            logger.info("Creating DynamoDB Resource")
            self.__dynamodb_resource = self.session.resource

        if self.raise_on_error and self.__dynamodb_resource is None:
            raise RuntimeError("DynamoDB Resource is not available")

        return self.__dynamodb_resource

    @resource.setter
    def resource(self, value: DynamoDBServiceResource):
        logger.info("Setting DynamoDB Resource")
        self.__dynamodb_resource = value

    @property
    def dynamodb_resource(self) -> DynamoDBServiceResource:
        """
        DynamoDB Resource Connection
            - Backward Compatible.  You should use resource instead
        """
        return self.resource

    @dynamodb_resource.setter
    def dynamodb_resource(self, value: DynamoDBServiceResource):
        logger.info("Setting DynamoDB Resource")
        self.__dynamodb_resource = value
