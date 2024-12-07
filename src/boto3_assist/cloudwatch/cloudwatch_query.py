"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
from boto3_assist.cloudwatch.cloudwatch_connection import CloudWatchConnection
from boto3_assist.cloudwatch.cloudwatch_logs import CloudWatchLogs


class CloudWatchQuery(CloudWatchConnection):
    """Query Cloud Watch"""

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

        self.__cw_logs: CloudWatchLogs | None = None

    @property
    def cw_logs(self) -> CloudWatchLogs:
        """CloudWatch Logs Connection"""
        if self.__cw_logs is None:
            self.__cw_logs = CloudWatchLogs(
                aws_profile=self.aws_profile,
                aws_region=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            )
        return self.__cw_logs

    def get_log_group_size(
        self, log_group_name: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        Get the log group size for a given period of time
        Args:
            log_group_name (str): _description_
            start_time (datetime): _description_
            end_time (datetime): _description_

        Returns:
            _type_: _description_
        """
        response = self.client.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "storedBytes",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/Logs",
                            # "MetricName": "StoredBytes",
                            "MetricName": "IncomingBytes",
                            "Dimensions": [
                                {"Name": "LogGroupName", "Value": log_group_name}
                            ],
                        },
                        "Period": 86400,  # Daily data
                        "Stat": "Sum",
                    },
                    "ReturnData": True,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
        )

        # Extract the total size in bytes for the period
        size: float = 0.0
        if response["MetricDataResults"]:
            # Access the first MetricDataResult
            metric_data_result = response["MetricDataResults"][0]
            # Sum the values if they exist
            size = (
                sum(metric_data_result["Values"]) if metric_data_result["Values"] else 0
            )
        else:
            size = 0

        size_mb = size / (1024 * 1024)
        size_gb = size_mb / 1024
        resp: Dict[str, Any] = {
            "LogGroupName": log_group_name,
            "Size": {
                "Bytes": size,
                "MB": size_mb,
                "GB": size_gb,
            },
            "StartDate": start_time.isoformat(),
            "EndDate": end_time.isoformat(),
        }

        return resp

    def get_log_sizes(
        self,
        start_date_time: datetime | None = None,
        end_date_time: datetime | None = None,
        days: int | None = 7,
        top: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Gets the log sizes for all log groups

        Args:
            start_date_time (datetime | None, optional): The Start Date. Defaults to None.
                If None it's set to now in UTC time - the days field
            end_date_time (datetime | None, optional): he Start Date. Defaults to None.
                If None it's set to not in UTC time
            days (int | None, optional): The days offset. Defaults to 7.
            top (int, optional): If greater than zero it will return the top x after sorting
                Defaults to 0.

        Returns:
            list: _description_
        """
        if not days:
            days = 7
        start_time = start_date_time or (datetime.now(UTC) - timedelta(days=days))
        end_time = end_date_time or datetime.now(UTC)

        # Step 1: List all log groups
        log_groups = self.cw_logs.list_log_groups()
        log_group_sizes = []

        # Step 2: Get sizes for each log group
        for log_group in log_groups:
            log_group_name = log_group["logGroupName"]

            size_info = self.get_log_group_size(log_group_name, start_time, end_time)
            log_group_sizes.append(size_info)

        # Step 3: Sort by size
        # top_log_groups = sorted(log_group_sizes, key=lambda x: x[1], reverse=True)
        top_log_groups = sorted(
            log_group_sizes,
            key=lambda x: x.get("Size", {}).get("Bytes", 0),
            reverse=True,
        )
        if top and top > 0:
            # find the top x if provided
            top_log_groups = top_log_groups[:top]

        return top_log_groups


def main():
    log_group = os.environ.get("LOG_GROUP_QUERY_SAMPLE", "<enter-log-group-here>")
    start = datetime.now() - timedelta(days=7)  # Last 30 days
    end = datetime.now()
    cw_query: CloudWatchQuery = CloudWatchQuery()
    result = cw_query.get_log_group_size(log_group, start, end)
    print(result)

    top = 25
    days = 7
    top_log_groups = cw_query.get_log_sizes(top=top, days=days)
    print(f"Top {top} log groups by size for the last week:")

    for top_log_group in top_log_groups:
        log_group_name = top_log_group["LogGroupName"]
        size_in_bytes = top_log_group.get("Size", {}).get("Bytes", 0)
        size_in_megs = top_log_group.get("Size", {}).get("MB", 0)
        size_in_gigs = top_log_group.get("Size", {}).get("GB", 0)
        size: str = ""
        if size_in_gigs > 1:
            size = f"{size_in_gigs:.2f} GB"
        elif size_in_megs > 1:
            size = f"{size_in_megs:.2f} MB"
        else:
            size = f"{size_in_bytes} bytes"

        print(f"{size}: {log_group_name}")


if __name__ == "__main__":
    main()
