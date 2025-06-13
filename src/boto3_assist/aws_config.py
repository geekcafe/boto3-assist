import os
from pathlib import Path
import configparser
from typing import Literal, Optional
from boto3_assist.utilities.serialization_utility import SerializableModel


class AWSConfigProfile(SerializableModel):
    def __init__(
        self, region: Optional[str] = "us-east-1", output: Optional[str] = "json"
    ):

        self.region: Optional[str] = region
        self.output: Optional[str] = output

        self.aws_access_key_id: Optional[str] = None
        self.aws_secret_access_key: Optional[str] = None
        self.aws_session_token: Optional[str] = None

        self.sso_session: Optional[str] = None
        self.sso_account_id: Optional[str] = None
        self.sso_role_name: Optional[str] = None

        self.credential_process: Optional[str] = None
        self.credential_source: Optional[str] = None
        self.role_arn: Optional[str] = None
        self.source_profile: Optional[str] = None
        self.external_id: Optional[str] = None
        self.role_session_name: Optional[str] = None
        self.duration_seconds: Optional[str] = None


class AWSConfigSSOSession(SerializableModel):
    def __init__(
        self,
        sso_start_url: Optional[str] = None,
        sso_region: Optional[str] = None,
        sso_registration_scopes: Optional[str] = None,
    ):
        self.sso_start_url: Optional[str] = sso_start_url
        self.sso_region: Optional[str] = sso_region
        self.sso_registration_scopes: Optional[str] = sso_registration_scopes


class AWSConfig:
    """
    Performs Operations on an AWS Config
    """

    def __init__(self):
        pass

    def get_path(self) -> Path:
        """
        Returns the path to the AWS config file, honoring AWS_CONFIG_FILE
        and falling back to ~/.aws/config (or %USERPROFILE%\.aws\config on Windows).
        """
        # 1) Check for explicit override
        env_path = os.environ.get("AWS_CONFIG_FILE")
        if env_path:
            return Path(env_path).expanduser()

        # 2) Default location
        return os.path.join(Path.home(), ".aws", "config")

    def path_exists(self) -> bool:
        path = self.get_path()

        return os.path.isfile(path)

    def has_profile(self, profile_name: str) -> bool:
        config = configparser.ConfigParser()
        self.read_section(profile_name, config)
        return profile_name in config.sections()

    def upsert_profile(
        self,
        name: str,
        profile: AWSConfigProfile,
        config_path: Optional[str] = None,
    ):
        self.write_section(name, profile, config_path)

    def upsert_sso_session(
        self,
        profile_name: str,
        sso_session: AWSConfigSSOSession,
        profile: AWSConfigProfile | None = None,
        config_path: Optional[str] = None,
    ):
        """
        Insert / Update the SSO Session block in the aws config
        Args:
            Name (str): Required.  Specifies the profile name.  This is the init key
                which is added to the section for both sso-session and profile
                e.g. [profile {profile_name}] or [sso-session {profile_name}]
            sso_session (AWSConfigSSOSession): Defines the values written to this session block
            profile (AWSConfigProfile): Defines the values written to the profile block.  Typically
                you will need a profile block along with a session block when using sso-session


        As a general rule you will typically need to build the following:
            [profile {profile-name}]
            sso_session = {optionally-use-profile-name}
            sso_account_id = {aws-acount-id}
            sso_role_name = {sso-role}
            region = {region}
            output = {output}

            [sso-session {profile-name}]
            sso_start_url = {sso_start_url} e.g. https://account-alias.awsapps.com/start
            sso_region = {region}
            sso_registration_scopes = {scopes}

        """

        if not profile_name:
            raise ValueError("Name is required")

        self.write_section(profile_name, sso_session, config_path)

        if profile:
            self.write_section(profile_name, profile, config_path)

    def write_section(
        self,
        profile_name: str | None,
        section: AWSConfigProfile | AWSConfigSSOSession,
        config_path: Optional[str] = None,
    ):
        config = configparser.ConfigParser()
        path = config_path or self.get_path()

        if self.path_exists():
            config.read(path)  # or any INI file path

        section_key = ""

        if profile_name.startswith("sso-session "):
            profile_name = profile_name.replace("sso-session ", "")
        if profile_name.startswith("profile "):
            profile_name = profile_name.replace("profile ", "")

        if isinstance(section, AWSConfigProfile):
            if profile_name:
                section_key = f"profile {profile_name}"
            else:
                section_key = "default"
        elif isinstance(section, AWSConfigSSOSession):
            section_key = f"sso-session {profile_name}"
        else:
            raise ValueError("Invalid section type")

        config = self._write_section(section_key, section, config)

        with open(path, "w", encoding="utf-8") as cfg_file:
            config.write(cfg_file)

    def _write_section(
        self,
        section_key: str,
        section: AWSConfigProfile | AWSConfigSSOSession,
        config: configparser.ConfigParser,
    ) -> configparser.ConfigParser:

        # always start with a "fresh" section
        config[section_key] = {}

        section_dictionary = section.to_dictionary()
        for key, value in section_dictionary.items():
            if value is not None:
                config[section_key][key] = value

        return config

    def read_section(
        self,
        profile_name: Optional[str] = None,
        config_path: Optional[str] = None,
        section_type: Literal["profile", "sso-session"] = "profile",
    ) -> configparser.SectionProxy:
        config = configparser.ConfigParser()
        if not config_path:
            config_path = self.get_path()

        if not os.path.isfile(config_path):
            return config

        config.read(config_path)
        profile_ini = f"{section_type} {profile_name}"
        if profile_ini in config:
            profile = config[profile_ini]
            return profile

        if profile_name in config:
            profile = config[profile_name]
            return profile

        return {}
