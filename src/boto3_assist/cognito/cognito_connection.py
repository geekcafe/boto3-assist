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
    from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
else:
    CognitoIdentityProviderClient = object


logger = Logger()


class CognitoConnection(Connection):
    """Connection"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            service_name="cognito-idp",
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.__client: CognitoIdentityProviderClient | None = None

        self.raise_on_error: bool = True

    @property
    def client(self) -> CognitoIdentityProviderClient:
        """Client Connection"""
        if self.__client is None:
            logger.info("Creating Client")
            self.__client = self.session.client

        if self.raise_on_error and self.__client is None:
            raise RuntimeError("Client is not available")
        return self.__client

    @client.setter
    def client(self, value: CognitoIdentityProviderClient):
        logger.info("Setting Client")
        self.__client = value
