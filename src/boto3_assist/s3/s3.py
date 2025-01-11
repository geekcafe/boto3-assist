"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, cast

from aws_lambda_powertools import Logger

from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket

logger = Logger(child=True)


class S3(S3Connection):
    """Common S3 Actions"""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        """_summary_

        Args:
            aws_profile (Optional[str], optional): _description_. Defaults to None.
            aws_region (Optional[str], optional): _description_. Defaults to None.
            aws_end_point_url (Optional[str], optional): _description_. Defaults to None.
            aws_access_key_id (Optional[str], optional): _description_. Defaults to None.
            aws_secret_access_key (Optional[str], optional): _description_. Defaults to None.
        """
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.__s3_object: S3Object | None = None
        self.__s3_bucket: S3Bucket | None = None

    @property
    def object(self) -> S3Object:
        """s3 object"""
        if self.__s3_object is None:
            connection = cast(S3Connection, self)
            self.__s3_object = S3Object(connection)
        return self.__s3_object

    @property
    def bucket(self) -> S3Bucket:
        """s3 bucket"""
        if self.__s3_bucket is None:
            connection = cast(S3Connection, self)
            self.__s3_bucket = S3Bucket(connection)
        return self.__s3_bucket
