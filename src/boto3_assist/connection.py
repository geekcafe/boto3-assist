"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, List
import warnings

from aws_lambda_powertools import Logger
from botocore.config import Config
from boto3_assist.boto3session import Boto3SessionManager
from boto3_assist.environment_services.environment_variables import (
    EnvironmentVariables,
)
from boto3_assist.connection_tracker import ConnectionTracker
from boto3_assist.connection_pool import ConnectionPool


logger = Logger()
tracker: ConnectionTracker = ConnectionTracker()


class Connection:
    """Base Boto 3 Connection"""

    def __init__(
        self,
        *,
        service_name: Optional[str] = None,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        assume_role_arn: Optional[str] = None,
        assume_role_chain: Optional[List[str]] = None,
        assume_role_duration_seconds: Optional[int] = 3600,
        config: Optional[Config] = None,
        use_connection_pool: bool = False,
    ) -> None:
        self.__aws_profile = aws_profile
        self.__aws_region = aws_region
        self.__aws_access_key_id = aws_access_key_id
        self.__aws_secret_access_key = aws_secret_access_key
        self.end_point_url = aws_end_point_url
        self.__session: Boto3SessionManager | None = None
        self.__assume_role_arn: Optional[str] = assume_role_arn
        self.__service_name: str | None = service_name
        self.__assume_role_chain = assume_role_chain
        self.__assume_role_duration_seconds = assume_role_duration_seconds
        self.__config = config
        self.__use_connection_pool = use_connection_pool

        if self.__service_name is None:
            raise RuntimeError(
                "Service Name is not available. The service name is required."
            )

        self.raise_on_error: bool = True

        # Issue deprecation warning if not using connection pool
        if not use_connection_pool:
            warnings.warn(
                f"Creating {service_name} Connection without connection pooling. "
                "This creates a new boto3 session on each instantiation, which can impact "
                "Lambda performance. Consider using Connection.from_pool() or "
                "use_connection_pool=True for better performance in Lambda functions. "
                "The default will change to use_connection_pool=True in boto3-assist v2.0.0.",
                DeprecationWarning,
                stacklevel=2,
            )

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
            aws_endpoint_url=self.end_point_url,
            assume_role_arn=self.__assume_role_arn,
            assume_role_chain=self.__assume_role_chain,
            assume_role_duration_seconds=self.__assume_role_duration_seconds,
            config=self.__config,
        )

        tracker.add(service_name=self.service_name)

    @property
    def asw_profile(self) -> str | None:
        """The AWS Profile"""
        return self.__aws_profile or EnvironmentVariables.AWS.profile()

    @asw_profile.setter
    def aws_profile(self, value: str | None):
        self.__aws_profile = value

    @property
    def aws_region(self) -> str | None:
        """The AWS Region"""
        return self.__aws_region or EnvironmentVariables.AWS.region()

    @aws_region.setter
    def aws_region(self, value: str | None):
        self.__aws_region = value

    @property
    def aws_access_key_id(self) -> str | None:
        """The AWS Access Key"""
        return self.__aws_access_key_id or EnvironmentVariables.AWS.aws_access_key_id()

    @aws_access_key_id.setter
    def aws_access_key_id(self, value: str | None):
        self.__aws_access_key_id = value

    @property
    def aws_secret_access_key(self) -> str | None:
        """The AWS Access Key"""
        return (
            self.__aws_secret_access_key
            or EnvironmentVariables.AWS.aws_secret_access_key()
        )

    @aws_secret_access_key.setter
    def aws_secret_access_key(self, value: str | None):
        self.__aws_secret_access_key = value

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

    @classmethod
    def from_pool(
        cls,
        service_name: str,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        config: Optional[Config] = None,
        **kwargs,
    ) -> "Connection":
        """
        Create connection using connection pool (recommended for Lambda).

        This is the recommended pattern for Lambda functions as it reuses
        boto3 sessions across invocations in warm containers, reducing
        connection overhead and improving performance.

        Args:
            service_name: AWS service name (e.g., 's3', 'dynamodb', 'sqs')
            aws_profile: AWS profile name (optional)
            aws_region: AWS region (optional)
            aws_end_point_url: Custom endpoint URL (optional, for moto testing)
            config: Botocore Config object (optional)
            **kwargs: Additional Connection parameters

        Returns:
            Connection instance configured to use connection pool

        Example:
            >>> # Recommended pattern for Lambda
            >>> conn = Connection.from_pool(service_name="dynamodb")
            >>> client = conn.session.client
            >>>
            >>> # Subsequent calls reuse the same session
            >>> conn2 = Connection.from_pool(service_name="dynamodb")
            >>> assert conn.session is conn2.session
        """
        return cls(
            service_name=service_name,
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            config=config,
            use_connection_pool=True,
            **kwargs,
        )

    @property
    def session(self) -> Boto3SessionManager:
        """Session"""
        if self.__use_connection_pool:
            # Use connection pool for session management
            pool = ConnectionPool.get_instance()
            return pool.get_session(
                service_name=self.service_name,
                aws_profile=self.aws_profile,
                aws_region=self.aws_region,
                aws_endpoint_url=self.end_point_url,
                config=self.__config,
                assume_role_arn=self.__assume_role_arn,
                assume_role_chain=self.__assume_role_chain,
                assume_role_duration_seconds=self.__assume_role_duration_seconds,
            )
        else:
            # Legacy behavior: create session on demand
            if self.__session is None:
                self.setup(setup_source="session init")

            if self.__session is None:
                raise RuntimeError("Session is not available")
            return self.__session
