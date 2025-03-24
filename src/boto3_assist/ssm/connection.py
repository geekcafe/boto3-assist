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
    from mypy_boto3_ssm import Client
else:
    Client = object


logger = Logger()


class SSMConnection(Connection):
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
            service_name="ssm",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_end_point_url=aws_end_point_url,
        )

        self.__client: Client | None = None

    @property
    def client(self) -> Client:
        """Client Connection"""
        if self.__client is None:
            self.__client = self.session.client

        return self.__client

    @client.setter
    def client(self, value: Client):
        logger.info("Setting Client")
        self.__client = value
