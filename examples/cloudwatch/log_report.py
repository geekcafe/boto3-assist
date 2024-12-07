import os
import json
import csv
from typing import List, Dict, Any
from pathlib import Path
from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.ec2.ec2_connection import EC2Connection
from boto3_assist.cloudwatch.cloudwatch_query import CloudWatchQuery


class LogReport(CloudWatchQuery):
    def __init__(self) -> None:
        super().__init__()

    def export(self, regions: List[Dict[str, Any]], file_format: str = "csv"):
        """
        Export the regions to a file
        Args:
            regions (List[Dict[str, Any]]): _description_
            file_format (str, optional): _description_. Defaults to "csv".
        """
        if file_format == "csv":
            self.__export_regions_to_csv(regions)
        elif file_format == "json":
            self.__export_regions_to_json(regions)

    def __export_regions_to_csv(self, regions, filename="aws_regions_with_status.csv"):
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["RegionName", "OptInStatus"])
            for region in regions:
                writer.writerow([region["RegionName"], region["OptInStatus"]])

    def __export_regions_to_json(
        self, regions, filename="aws_regions_with_status.json"
    ):
        with open(filename, "w", encoding="utf-8") as jsonfile:
            json.dump(regions, jsonfile, indent=4)


def main():
    """Main"""

    env_file_name: str = os.getenv("ENVRIONMENT_FILE", ".env")
    path = os.path.join(str(Path(__file__).parents[2].absolute()), env_file_name)
    el: EnvironmentLoader = EnvironmentLoader()
    if not os.path.exists(path=path):
        raise FileNotFoundError("Failed to find the environmetn file")
    loaded: bool = el.load_environment_file(path=path)
    if not loaded:
        raise RuntimeError("Failed to load my local environment")

    report: CloudWatchQuery = CloudWatchQuery()

    # Retrieve AWS regions with their status
    logs = report.get_log_sizes()

    print(logs)


if __name__ == "__main__":
    main()
