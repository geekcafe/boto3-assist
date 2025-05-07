"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import boto3
from typing import List


class RoleAssumptionMixin:
    def _assume_roles_in_chain(
        self,
        base_session: boto3.Session,
        role_chain: List[str],
        session_name: str,
        duration_seconds: int,
        region: str,
    ) -> boto3.Session:
        session = base_session

        for role_arn in role_chain:
            sts_client = session.client("sts")
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration_seconds,
            )
            creds = response["Credentials"]

            session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
                region_name=region,
            )

        return session
