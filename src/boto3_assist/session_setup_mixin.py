"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import boto3
from typing import Optional


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
            raise RuntimeError(f"Failed to create boto3 session: {e}") from e
