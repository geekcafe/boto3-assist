"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, List
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger
from boto3_assist.connection import Connection


if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
else:
    DynamoDBClient = object
    DynamoDBServiceResource = object


logger = Logger()


class DynamoDBConnection(Connection):
    """DB Environment"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        assume_role_arn: Optional[str] = None,
        assume_role_chain: Optional[List[str]] = None,
        assume_role_duration_seconds: Optional[int] = 3600,
    ) -> None:
        super().__init__(
            service_name="dynamodb",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_end_point_url=aws_end_point_url,
            assume_role_arn=assume_role_arn,
            assume_role_chain=assume_role_chain,
            assume_role_duration_seconds=assume_role_duration_seconds,
        )

        self.__dynamodb_client: DynamoDBClient | None = None
        self.__dynamodb_resource: DynamoDBServiceResource | None = None

        self.raise_on_error: bool = True

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
