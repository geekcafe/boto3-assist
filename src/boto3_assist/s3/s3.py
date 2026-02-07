"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, cast

from aws_lambda_powertools import Logger

from boto3_assist.s3.s3_bucket import S3Bucket
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.s3.s3_object import S3Object

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
        use_connection_pool: bool = True,
    ) -> None:
        """_summary_

        Args:
            aws_profile (Optional[str], optional): _description_. Defaults to None.
            aws_region (Optional[str], optional): _description_. Defaults to None.
            aws_end_point_url (Optional[str], optional): _description_. Defaults to None.
            aws_access_key_id (Optional[str], optional): _description_. Defaults to None.
            aws_secret_access_key (Optional[str], optional): _description_. Defaults to None.
            use_connection_pool (bool, optional): Use connection pooling. Defaults to True.
        """
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            use_connection_pool=use_connection_pool,
        )

        self.__s3_object: S3Object | None = None
        self.__s3_bucket: S3Bucket | None = None

    @classmethod
    def from_pool(
        cls,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        **kwargs,
    ) -> "S3":
        """
        Create S3 connection using connection pool (recommended for Lambda).

        This is the recommended pattern for Lambda functions as it reuses
        boto3 sessions across invocations in warm containers.

        Args:
            aws_profile: AWS profile name (optional)
            aws_region: AWS region (optional)
            aws_end_point_url: Custom endpoint URL (optional, for moto testing)
            **kwargs: Additional S3 parameters

        Returns:
            S3 instance configured to use connection pool

        Example:
            >>> # Recommended pattern for Lambda
            >>> s3 = S3.from_pool()
            >>> s3.object.upload_file(file_path="/tmp/file.txt", bucket="my-bucket", key="file.txt")
            >>>
            >>> # Subsequent calls reuse the same connection
            >>> s3_2 = S3.from_pool()
            >>> assert s3.session is s3_2.session
        """
        return cls(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            use_connection_pool=True,
            **kwargs,
        )

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
