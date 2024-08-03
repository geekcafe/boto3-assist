"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from aws_lambda_powertools import Logger

from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from boto3_assist.boto3session import Boto3SessionManager
from boto3_assist.environment_services.environment_variables import (
    EnvironmentVariables,
)


logger = Logger()


class DynamoDbConnection:
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
            aws_end_point_url or EnvironmentVariables.AWS.DynamoDb.endpoint_url()
        )
        self.aws_access_key_id = (
            aws_access_key_id or EnvironmentVariables.AWS.DynamoDb.aws_access_key_id()
        )
        self.aws_secret_access_key = (
            aws_secret_access_key
            or EnvironmentVariables.AWS.DynamoDb.aws_secret_access_key()
        )
        self.session: Boto3SessionManager
        self.dynamodb_client: DynamoDBClient
        self.dynamodb_resource: DynamoDBServiceResource

        self.raise_on_error: bool = True

        self.setup(reset_source="__init__")

    def setup(self, reset_source: Optional[str] = None):
        """
        Setup the environment.  Automatically called via init.
        You can run setup at anytime with new parameters
        """

        logger.debug(
            {
                "metric_filter": "db_connection_setup",
                "source": "DynamoDbConnection",
                "aws_profile": self.aws_profile,
                "aws_region": self.aws_region,
                "setup_source": reset_source,
            }
        )

        self.session = Boto3SessionManager(
            service_name="dynamodb",
            aws_profile=self.aws_profile,
            aws_region=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_endpoint_url=self.end_point_url,
        )

        self.dynamodb_client = self.session.client
        self.dynamodb_resource = self.session.resource

        self.raise_on_error = EnvironmentVariables.AWS.DynamoDb.raise_on_error_setting()
