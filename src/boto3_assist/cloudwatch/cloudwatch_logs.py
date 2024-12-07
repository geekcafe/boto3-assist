"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, List, Dict, Any
from boto3_assist.cloudwatch.cloudwatch_log_connection import CloudWatchConnection


class CloudWatchLogs(CloudWatchConnection):
    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def list_log_groups(self):
        """Retrieve all log groups in the AWS account."""
        log_groups: List[Dict[str, Any]] = []
        paginator = self.client.get_paginator("describe_log_groups")
        for page in paginator.paginate():
            log_groups.extend(page["logGroups"])  # type: ignore[arg-type]
        return log_groups


def main():
    query: CloudWatchLogs = CloudWatchLogs()
    result = query.list_log_groups()
    print(result)
