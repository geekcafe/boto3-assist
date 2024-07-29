import os
import boto3
from aws_lambda_powertools import Logger
from boto_assist.environment_services.environment_variables import EnvironmentVariables

logger = Logger(__name__)


class Boto3SessionManager:
    """Manages Boto3 Sessions"""

    def __init__(
        self,
        service_name: str,
        *,
        aws_profile: str | None = None,
        aws_region: str | None = None,
        assume_role_arn: str | None = None,
        assume_role_session_name: str | None = None,
        cross_account_role_arn: str | None = None,
        config: boto3.session.Config | None = None,
        aws_endpoint_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
    ):
        self.service_name = service_name
        self.aws_profile = aws_profile
        self.aws_region = aws_region
        self.assume_role_arn = assume_role_arn
        self.assume_role_session_name = assume_role_session_name
        self.config = config
        self.cross_account_role_arn = cross_account_role_arn
        self.endpoint_url = aws_endpoint_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.__session = None
        self.__client = None
        self.__resource = None

        self.__setup()

    def __setup(self):
        """Setup AWS session, client, and resource."""
        self.__client = None
        self.__resource = None

        profile = self.aws_profile or EnvironmentVariables.AWS.profile()
        region = self.aws_profile or EnvironmentVariables.AWS.region()
        if self.assume_role_arn:
            self.__assume_role()
        else:
            logger.debug("Connecting without assuming a role.")
            self.__session = self.__get_aws_session(profile, region)

    def __assume_role(self):
        """Assume an AWS IAM role."""
        try:
            logger.debug(f"Assuming role {self.assume_role_arn}")
            sts_client = boto3.client("sts")
            session_name = (
                self.assume_role_session_name
                or f"AssumeRoleSessionFor{self.service_name}"
            )
            assumed_role_response = sts_client.assume_role(
                RoleArn=self.assume_role_arn,
                RoleSessionName=session_name,
            )
            credentials = assumed_role_response["Credentials"]
            self.__session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )

        except Exception as e:
            logger.error(f"Error assuming role: {e}")
            raise RuntimeError(f"Failed to assume role {self.assume_role_arn}") from e

    def __get_aws_session(self, aws_profile: str = None, aws_region: str = None):
        """Get a boto3 session for AWS."""
        logger.debug({"profile": aws_profile, "region": aws_region})
        try:
            self.aws_profile = aws_profile or EnvironmentVariables.AWS.profile()
            self.aws_region = aws_region or EnvironmentVariables.AWS.region()
            tmp_access_key_id = self.aws_access_key_id
            tmp_secret_access_key = self.aws_secret_access_key
            if not EnvironmentVariables.AWS.display_aws_access_key_id():
                tmp_access_key_id = (
                    "None" if tmp_access_key_id is None else "***************"
                )
            if not EnvironmentVariables.AWS.display_aws_secret_access_key():
                tmp_secret_access_key = (
                    "None" if tmp_secret_access_key is None else "***************"
                )

            logger.debug(
                {
                    "profile": self.aws_profile,
                    "region": self.aws_region,
                    "aws_access_key_id": tmp_access_key_id,
                    "aws_secret_access_key": tmp_secret_access_key,
                    "aws_session_token": "*******"
                    if self.aws_session_token is not None
                    else "",
                }
            )
            logger.debug("Creating boto3 session")
            session = boto3.Session(
                profile_name=self.aws_profile,
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
            )
        # if self.aws_profile or self.aws_region
        # else boto3.Session()

        except Exception as e:
            logger.error(e)
            raise RuntimeError("Failed to create a boto3 session.") from e

        logger.debug({"session": session})
        return session

    @property
    def client(self):
        """Return the boto3 client connection."""
        if not self.__client:
            self.__client = self.__session.client(
                self.service_name,
                config=self.config,
                endpoint_url=self.endpoint_url,
            )

        return self.__client

    @property
    def resource(self):
        """Return the boto3 resource connection."""
        if not self.__resource:
            self.__resource = self.__session.resource(
                self.service_name,
                config=self.config,
                endpoint_url=self.endpoint_url,
            )
        return self.__resource
