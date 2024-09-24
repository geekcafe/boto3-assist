"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import json
import gzip
from typing import List
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_helpers import DynamoDBHelpers

logger = Logger()


class DynamoDBImporter:
    """
    Import files to your database
    Currently supports json files
    """

    def __init__(
        self,
        *,
        table_name: str,
        db: DynamoDB,
    ):
        self.table_name = table_name
        self.db = db

    def import_json_file(self, json_file_path: str) -> None:
        """Import a json or gzip-compressed json file into the database"""

        if os.path.exists(json_file_path) is False:
            raise FileNotFoundError(f"File not found: {json_file_path}")
        if json_file_path.endswith(".gz"):
            data = self.read_gzip_file(json_file_path)
        elif json_file_path.endswith(".json"):
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        else:
            raise ValueError(f"Unsupported file type: {json_file_path}")

        # table = self.db.dynamodb_resource.Table(self.table_name)
        # with table.batch_writer() as batch:
        for item in data:
            try:
                item = DynamoDBHelpers.clean_null_values(item=item)

                self.db.save(item=item, table_name=self.table_name)
                # batch.put_item(Item=item)

            except ClientError as e:
                logger.exception(str(e))
                raise e

    def import_json_files(self, json_file_paths: list[str]) -> None:
        """Import multiple json files into the database"""
        for json_file_path in json_file_paths:
            if os.path.exists(json_file_path) is False:
                raise FileNotFoundError(f"File not found: {json_file_path}")
            else:
                if json_file_path.endswith(".gz") or json_file_path.endswith(".json"):
                    self.import_json_file(json_file_path)
                else:
                    if os.path.isdir(json_file_path):
                        logger.warning(
                            f"Unsupported sub directory import {json_file_path}. "
                            "Skipping import on this file."
                        )
                    else:
                        logger.warning(
                            f"Unsupported file type: {json_file_path}. "
                            "Skipping import on this file.  Files should end with .gz or .json"
                        )

    def read_gzip_file(self, file_path: str) -> List[dict]:
        """
        Reads a gzip file
        Args:
            file_path (str): path to the gzip file

        Returns:
            List[dict]: list of items
        """
        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [item["Item"] for item in data]
        except json.JSONDecodeError:
            pass

        # If not a valid array, read line by line
        items = []
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                items.append(json.loads(line)["Item"])
        return items
