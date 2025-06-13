import unittest
from pathlib import Path


class AWSConfigTest(unittest.TestCase):

    def setUp(self):
        config_path_dir = (
            Path(__file__).parent.joinpath(".outputs", "aws_config").resolve()
        )

        if not config_path_dir.exists():
            config_path_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = config_path_dir.joinpath("config")

    def test_import(self):
        from boto3_assist.aws_config import AWSConfig

        self.assertTrue(AWSConfig)

    def test_init(self):
        from boto3_assist.aws_config import AWSConfig
        import os

        aws_config = AWSConfig()
        self.assertTrue(aws_config)

    def test_path(self):
        from boto3_assist.aws_config import AWSConfig
        import os

        aws_config = AWSConfig()
        path = aws_config.get_path()

        self.assertTrue(os.path.exists(path))

    def test_config_upsert_profile(self):
        from boto3_assist.aws_config import AWSConfig
        from boto3_assist.aws_config import AWSConfigProfile

        aws_config = AWSConfig()
        profile = AWSConfigProfile("us-east-2", "json")
        profile.aws_access_key_id = "111111111111"
        profile.aws_secret_access_key = "22222222222"
        aws_config.upsert_profile("unit-test-profile", profile)

    def test_config_upsert_sso(self):
        from boto3_assist.aws_config import AWSConfig
        from boto3_assist.aws_config import AWSConfigSSOSession

        aws_config = AWSConfig()
        sso = AWSConfigSSOSession("us-east-1", "json")
        sso.sso_start_url = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        sso.sso_region = "us-east-2"
        sso.sso_registration_scopes = "scopes"
        aws_config.upsert_sso_session("unit-test-sso", sso)

    def test_config_upsert_sso_with_profile(self):
        from boto3_assist.aws_config import AWSConfig
        from boto3_assist.aws_config import AWSConfigSSOSession
        from boto3_assist.aws_config import AWSConfigProfile

        aws_config = AWSConfig()
        sso = AWSConfigSSOSession("us-east-1", "json")
        sso.sso_start_url = "https://<account-domain>.awsapps.com/start/#/?tab=accounts"
        sso.sso_region = "us-east-1"
        sso.sso_registration_scopes = "sso:account:access"

        section_name = "test-tenant-001"

        profile = AWSConfigProfile("us-east-1", "json")
        profile.sso_session = section_name
        profile.sso_account_id = "AAAAAAAAAAAAAAAAAA"
        profile.sso_role_name = "SomeRoleName"
        profile.region = "us-east-1"
        profile.output = "json"

        aws_config.upsert_sso_session(
            section_name, sso_session=sso, profile=profile, config_path=self.config_path
        )
