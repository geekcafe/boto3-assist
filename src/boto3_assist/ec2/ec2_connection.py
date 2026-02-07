"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import TYPE_CHECKING, Optional

from aws_lambda_powertools import Logger

from boto3_assist.connection import Connection

if TYPE_CHECKING:
    from mypy_boto3_ec2 import Client
else:
    Client = object


logger = Logger()


class EC2Connection(Connection):
    """EC2 Connection"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            service_name="ec2",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.__client: Client | None = None

        self.raise_on_error: bool = True

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
