"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os

from aws_lambda_powertools import Logger

logger = Logger(__name__)


class EnvironmentVariables:
    """
    Easy access to allo the environment variables we use in the appliction.
    It's a best practice to use this vs doing and os.getevn in each application.
    This helps us track all the enviroment variables in use
    """

    class AWS:
        """AWS Specific Environment Vars"""

        @staticmethod
        def region() -> str | None:
            """
            gets the aws region from an environment var
            """
            value = os.getenv("AWS_REGION")
            if not value:
                value = None
            return value

        @staticmethod
        def profile() -> str | None:
            """
            Get the aws profile used for cli/boto3 commands
            This should only be set with temporty creds and only for development purposes
            """
            value = os.getenv("AWS_PROFILE")
            if not value:
                value = None
            return value

        @staticmethod
        def account_id() -> str | None:
            """
            gets the aws account id from an environment var
            """
            value = os.getenv("AWS_ACCOUNT_ID")
            return value

        @staticmethod
        def amazon_trace_id() -> str:
            """
            gets the amazon trace id from an environment var
            """
            value = os.getenv("_X_AMZN_TRACE_ID", "NA")
            return value

        @staticmethod
        def endpoint_url() -> str | None:
            """
            Gets the AWS_ENDPOINT_URL environment var
            """
            value = os.getenv("AWS_ENDPOINT_URL")
            return value

        @staticmethod
        def display_aws_access_key_id() -> bool:
            """
            Determines if you want to display the aws access key
            """
            value = (
                str(os.getenv("DISPLAY_AWS_ACCESS_KEY_ID", "false")).lower() == "true"
            )
            return value

        @staticmethod
        def display_aws_secret_access_key() -> bool:
            """
            Determines if you want to display the aws access key
            """
            value = (
                str(os.getenv("DISPLAY_AWS_SECRET_ACCESS_KEY", "false")).lower()
                == "true"
            )
            return value

        @staticmethod
        def aws_access_key_id() -> str | None:
            """
            The aws_access_key_id.  Often used for local development.
            """
            value = os.getenv("ACCESS_KEY_ID")
            return value

        @staticmethod
        def aws_secret_access_key() -> str | None:
            """
            The aws_secret_access_key.  Often used for local development.
            """
            value = os.getenv("SECRET_ACCESS_KEY")
            return value

        class SES:
            """SES Settings"""

            @staticmethod
            def user_name() -> str | None:
                """
                gets the ses user-name from an environment var
                """
                value = os.getenv("SES_USER_NAME")
                return value

            @staticmethod
            def password() -> str | None:
                """
                gets the ses password from an environment var
                """
                value = os.getenv("SES_PASSWORD")
                return value

            @staticmethod
            def endpoint() -> str | None:
                """
                gets the ses endpoint from an environment var
                """
                value = os.getenv("SES_END_POINT")
                return value

        class Cognito:
            """Cognito Settings"""

            @staticmethod
            def user_pool() -> str | None:
                """
                gets the cognito user pool from an environment var
                """
                value = os.getenv("COGNITO_USER_POOL")
                return value

        class DynamoDB:
            """DynamoDB Settings"""

            @staticmethod
            def raise_on_error_setting() -> bool:
                """
                determines if we raise errors on saves, gets, etc
                this is useful to turn off for some local testing. but otherwise I
                would recommend to leave it on
                """
                value = str(os.getenv("RAISE_ON_DB_ERROR", "true")).lower() == "true"

                return value

            @staticmethod
            def single_table() -> str | None:
                """
                If a single table design is used this can be a usefull way to send it around
                """
                value = os.getenv("DYNAMODB_SINGLE_TABLE")
                return value

            @staticmethod
            def endpoint_url() -> str | None:
                """
                The DynamoDB Endpoint url.  Often used for local development.
                For example a docker containers defaults to http://localhost:8000
                """
                value = os.getenv("AWS_DYNAMODB_ENDPOINT_URL")
                return value

            @staticmethod
            def aws_access_key_id() -> str | None:
                """
                The DynamoDB aws_access_key_id.  Often used for local development.
                For example a docker containers defaults to dummy_access_key
                """
                value = os.getenv("AWS_DYNAMODB_ACCESS_KEY_ID")
                return value

            @staticmethod
            def aws_secret_access_key() -> str | None:
                """
                The DynamoDB aws_secret_access_key.  Often used for local development.
                For example a docker containers defaults to dummy_secret_key
                """
                value = os.getenv("AWS_DYNAMODB_SECRET_ACCESS_KEY")
                return value

    @staticmethod
    def get_integration_tests_setting() -> bool:
        """
        deteremine if integration tests are run from an environment var
        """
        value = str(os.getenv("RUN_INTEGRATION_TESTS", "False")).lower() == "true"
        env = EnvironmentVariables.get_environment_setting()

        if env.lower().startswith("prod"):
            value = False

        return value

    @staticmethod
    def get_environment_setting() -> str:
        """
        gets the environment name from an environment var
        """
        value = os.getenv("ENVIRONMENT")

        if not value:
            logger.warning(
                "ENVIRONMENT var is not set. A future version will throw an error."
            )
            return ""

        return value
