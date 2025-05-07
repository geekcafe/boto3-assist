"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, List, Any
import boto3
from botocore.config import Config
from .session_setup_mixin import SessionSetupMixin
from .role_assumption_mixin import RoleAssumptionMixin


class Boto3SessionManager(SessionSetupMixin, RoleAssumptionMixin):
    def __init__(
        self,
        service_name: str,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        assume_role_arn: Optional[str] = None,
        assume_role_chain: Optional[List[str]] = None,
        assume_role_session_name: Optional[str] = None,
        assume_role_duration_seconds: Optional[int] = 3600,
        config: Optional[Config] = None,
        aws_endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
    ):
        self.service_name = service_name
        self.aws_profile = aws_profile
        self.aws_region = aws_region
        self.config = config
        self.endpoint_url = aws_endpoint_url
        self.assume_role_chain = assume_role_chain or (
            [assume_role_arn] if assume_role_arn else []
        )
        self.assume_role_session_name = (
            assume_role_session_name or f"AssumeRoleSessionFor{service_name}"
        )
        self.assume_role_duration_seconds = assume_role_duration_seconds
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token

        self.__session: Optional[boto3.Session] = None
        self.__client: Any = None
        self.__resource: Any = None

        self.__initialize()

    def __initialize(self):
        base_session = self._create_base_session(
            self.aws_profile,
            self.aws_region,
            self.aws_access_key_id,
            self.aws_secret_access_key,
            self.aws_session_token,
        )

        if self.assume_role_chain:
            self.__session = self._assume_roles_in_chain(
                base_session,
                self.assume_role_chain,
                self.assume_role_session_name,
                self.assume_role_duration_seconds,
                self.aws_region,
            )
        else:
            self.__session = base_session

    @property
    def client(self) -> Any:
        if not self.__client:
            self.__client = self.__session.client(
                self.service_name, config=self.config, endpoint_url=self.endpoint_url
            )
        return self.__client

    @property
    def resource(self) -> Any:
        if not self.__resource:
            self.__resource = self.__session.resource(
                self.service_name, config=self.config, endpoint_url=self.endpoint_url
            )
        return self.__resource
