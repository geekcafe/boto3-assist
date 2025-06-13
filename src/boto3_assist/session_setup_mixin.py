"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import boto3
from typing import Optional
from boto3_assist.aws_config import AWSConfig


class SessionSetupMixin:
    def _create_base_session(
        self,
        aws_profile: Optional[str],
        aws_region: Optional[str],
        aws_access_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
        aws_session_token: Optional[str],
    ) -> boto3.Session:
        try:
            return boto3.Session(
                profile_name=aws_profile,
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        except Exception as e:

            error_message = f"Failed to create boto3 session "
            if "profile" in str(e).lower():
                error_message += " due to a profile error "

                error_message += f" with profile '{aws_profile}'."
                config: AWSConfig = AWSConfig()
                if not config.path_exists():
                    error_message += (
                        f" The AWS config file '{config.get_path()}' was not found. "
                        "Please ensure that the AWS CLI is installed and configured correctly. "
                        "You can install the AWS CLI by running 'pip install awscli' or 'pip install awscli --upgrade'. "
                    )

                    if (
                        os.getenv("HOME") == "/tmp"
                        or os.getenv("AWS_CONFIG_FILE") == "/tmp"
                    ):
                        error_message += (
                            f'The environment HOME path is set to {os.getenv("HOME")}. '
                        )
                        if os.getenv("AWS_CONFIG_FILE"):
                            error_message += (
                                f"The environment AWS_CONFIG_FILE is set to {os.getenv('AWS_CONFIG_FILE')}. "
                                "The AWS_CONFIG_FILE overrides the HOME directory and path. "
                            )

                        error_message += (
                            "If you are running this locally and expecting it to be in your users home "
                            "directory, you may need to set the HOME or AWS_CONFIG_FILE environment variable manually. "
                            "There could be other actions such as a Lambda environment resetting the path to /tmp. "
                            "If you are running in a GitHub Actions environment, "
                            "you may need to set the HOME or AWS_CONFIG_FILE environment variable to '/home/runner'. "
                        )
                elif not config.has_profile(aws_profile):
                    error_message += f" The profile '{aws_profile}' was not found in the AWS config file in {config.get_path()}."

            # check for the existence of the profile and the path to the profile

            raise RuntimeError(error_message) from e
