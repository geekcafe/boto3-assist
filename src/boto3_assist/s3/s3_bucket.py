"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Any, Dict

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError


from boto3_assist.s3.s3_connection import S3Connection

logger = Logger(child=True)


class S3Bucket:
    """Common S3 Actions"""

    def __init__(self, connection: S3Connection):
        self.connection = connection or S3Connection()

    def create(self, *, bucket_name: str) -> Dict[str, Any]:
        """
        Create an S3 bucket
        :param bucket_name: Bucket to create
        :return: True if bucket is created, else False
        """
        try:
            response = self.connection.client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} created")

            return dict(response)
        except ClientError as e:
            logger.exception(e)
            raise e

    def enable_versioning(self, *, bucket_name: str) -> None:
        """
        Enable versioning on an S3 bucket
        :param bucket_name: Bucket to enable versioning on
        :return: None
        """
        try:
            self.connection.client.put_bucket_versioning(
                Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"}
            )
            logger.info(f"Versioning enabled on bucket {bucket_name}")
        except ClientError as e:
            logger.exception(e)
            raise e

    def disable_versioning(self, *, bucket_name: str) -> None:
        """
        Disable versioning on an S3 bucket
        :param bucket_name: Bucket to disable versioning on
        :return: None
        """
        try:
            self.connection.client.put_bucket_versioning(
                Bucket=bucket_name, VersioningConfiguration={"Status": "Suspended"}
            )
            logger.info(f"Versioning disabled on bucket {bucket_name}")
        except ClientError as e:
            logger.exception(e)
            raise e
