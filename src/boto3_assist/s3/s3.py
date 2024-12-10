"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import tempfile
import time
import io
from typing import Any, Dict, List, Optional

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from boto3_assist.errors.custom_exceptions import InvalidHttpMethod
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.utilities.datetime_utility import DatetimeUtility
from boto3_assist.utilities.file_operations import FileOperations
from boto3_assist.utilities.http_utility import HttpUtility

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

    def create_bucket(self, *, bucket_name: str) -> None:
        """
        Create an S3 bucket
        :param bucket_name: Bucket to create
        :return: True if bucket is created, else False
        """
        try:
            self.client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} created")
        except ClientError as e:
            logger.exception(e)
            raise e

    def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        key_path: str,
        user_id: str,
        file_name: str,
        meta_data: dict | None = None,
        expiration=3600,
        method_type="POST",
    ) -> Dict[str, Any]:
        """
        Create a signed URL for uploading a file to S3.
        :param bucket_name: The name of the S3 bucket.
        :param user_id: The user ID of the user uploading the file.
        :param file_name: The file name of the file being uploaded.
        :param aws_profile: The name of the AWS profile to use.
        :param aws_region: The name of the AWS region to use.
        :param expiration: The number of seconds the URL is valid for.
        :return: The signed URL.
        """
        start = DatetimeUtility.get_utc_now()
        logger.debug(
            f"Creating signed URL for bucket {bucket_name} for user {user_id} and file {file_name} at {start} UTC"
        )

        file_extension = FileOperations.get_file_extension(file_name)

        local_meta = {
            "user_id": f"{user_id}",
            "file_name": f"{file_name}",
            "extension": f"{file_extension}",
            "method": "pre-signed-upload",
        }

        if not meta_data:
            meta_data = local_meta
        else:
            meta_data.update(local_meta)

        key = key_path
        method_type = method_type.upper()

        signed_url: str | Dict[str, Any]
        if method_type == "PUT":
            signed_url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": f"{bucket_name}",
                    "Key": f"{key}",
                    # NOTE: if you include the ContentType or Metadata then its required in the when they upload the file
                    # Otherwise you will get a `SignatureDoesNotMatch` error
                    # for now I'm commenting it out.
                    #'ContentType': 'application/octet-stream',
                    #'ACL': 'private',
                    # "Metadata": meta_data,
                },
                ExpiresIn=expiration,  # URL is valid for x seconds
            )
        elif method_type == "POST":
            signed_url = self.client.generate_presigned_post(
                bucket_name,
                key,
                ExpiresIn=expiration,  # URL is valid for x seconds
            )
        elif method_type == "GET":
            signed_url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": f"{bucket_name}",
                    "Key": f"{key}",
                },
                ExpiresIn=expiration,  # URL is valid for x seconds
            )
        else:
            raise InvalidHttpMethod(
                f'Unknown method type was referenced.  valid types are "PUT", "POST", "GET" , "{method_type}" as used '
            )

        end = DatetimeUtility.get_utc_now()
        logger.debug(f"Signed URL created in {end-start}")

        response = {
            "signed_url": signed_url,
            "key": key,
            "meta_data": meta_data,
        }

        return response

    def upload_file_obj(self, *, bucket: str, key: str, file_obj: bytes | str) -> str:
        """
        Uploads a file object to s3. Returns the full s3 path s3://<bucket>/<key>
        """

        if key.startswith("/"):
            # remove the first slash
            key = key[1:]

        logger.debug(
            {
                "metric_filter": "upload_file_to_s3",
                "bucket": bucket,
                "key": key,
            }
        )
        try:
            # convert if necessary
            file_obj: bytes = (
                file_obj.encode("utf-8") if isinstance(file_obj, str) else file_obj
            )
            self.client.upload_fileobj(
                Fileobj=io.BytesIO(file_obj), Bucket=bucket, Key=key
            )

        except ClientError as ce:
            error = {
                "metric_filter": "upload_file_to_s3_failure",
                "s3 upload": "failure",
                "bucket": bucket,
                "key": key,
            }
            logger.error(error)
            raise RuntimeError(error) from ce

        return f"s3://{bucket}/{key}"

    def upload_file(
        self,
        *,
        bucket: str,
        key: str,
        local_file_path: str,
        throw_error_on_failure: bool = False,
    ) -> str | None:
        """
        Uploads a file to s3. Returns the full s3 path s3://<bucket>/<key>
        """

        if key.startswith("/"):
            # remove the first slash
            key = key[1:]

        # build the path
        s3_path = f"s3://{bucket}/{key}"

        logger.debug(
            {
                "metric_filter": "upload_file_to_s3",
                "bucket": bucket,
                "key": key,
                "local_file_path": local_file_path,
            }
        )
        try:
            self.client.upload_file(local_file_path, bucket, key)

        except ClientError as ce:
            error = {
                "metric_filter": "upload_file_to_s3_failure",
                "s3 upload": "failure",
                "bucket": bucket,
                "key": key,
                "local_file_path": local_file_path,
            }
            logger.error(error)

            if throw_error_on_failure:
                raise RuntimeError(error) from ce

            return None

        return s3_path

    def download_file(
        self,
        *,
        bucket: str,
        key: str,
        local_directory: str | None = None,
        local_file_path: str | None = None,
        retry_attempts: int = 3,
        retry_sleep: int = 5,
    ) -> str:
        """Download a file from s3"""
        exception: Exception | None = None

        if retry_attempts == 0:
            retry_attempts = 1

        for i in range(retry_attempts):
            exception = None
            try:
                path = self.download_file_no_retries(
                    bucket=bucket,
                    key=key,
                    local_directory=local_directory,
                    local_file_path=local_file_path,
                )
                if path and os.path.exists(path):
                    return path

            except Exception as e:  # pylint: disable=w0718
                logger.warning(
                    {
                        "action": "download_file",
                        "result": "failure",
                        "exception": str(e),
                        "attempt": i + 1,
                        "retry_attempts": retry_attempts,
                    }
                )

                exception = e

                # sleep for a bit
                attempt = i + 1
                time.sleep(attempt * retry_sleep)

        if exception:
            logger.exception(
                {
                    "action": "download_file",
                    "result": "failure",
                    "exception": str(exception),
                    "retry_attempts": retry_attempts,
                }
            )

            raise exception from exception

        raise RuntimeError("Unable to download file")

    def download_file_no_retries(
        self,
        bucket: str,
        key: str,
        local_directory: str | None = None,
        local_file_path: str | None = None,
    ) -> str:
        """
        Downloads a file from s3

        Args:
            bucket (str): s3 bucket
            key (str): the s3 object key
            local_directory (str, optional): Local directory to download to. Defaults to None.
            If None, we'll use a local tmp directory.

        Raises:
            e:

        Returns:
            str: Path to the downloaded file.
        """

        decoded_object_key: str
        try:
            logger.debug(
                {
                    "action": "downloading file",
                    "bucket": bucket,
                    "key": key,
                    "local_directory": local_directory,
                }
            )
            return self.__download_file(bucket, key, local_directory, local_file_path)
        except FileNotFoundError:
            logger.warning(
                {
                    "metric_filter": "download_file_error",
                    "error": "FileNotFoundError",
                    "message": "attempting to find it decoded",
                    "bucket": bucket,
                    "key": key,
                }
            )

            # attempt to decode the key
            decoded_object_key = HttpUtility.decode_url(key)

            logger.error(
                {
                    "metric_filter": "download_file_error",
                    "error": "FileNotFoundError",
                    "message": "attempting to find it decoded",
                    "bucket": bucket,
                    "key": key,
                    "decoded_object_key": decoded_object_key,
                }
            )

            return self.__download_file(bucket, decoded_object_key, local_directory)

        except Exception as e:
            logger.error(
                {
                    "metric_filter": "download_file_error",
                    "error": str(e),
                    "bucket": bucket,
                    "decoded_object_key": decoded_object_key,
                }
            )
            raise e

    def stream_file(self, bucket_name: str, key: str) -> Dict[str, Any]:
        """
        Gets a file from s3 and returns the response.
        The "Body" is a streaming body object.  You can read it like a file.
        For example:

        with response["Body"] as f:
            data = f.read()
            print(data)

        """

        logger.debug(
            {
                "source": "download_file",
                "action": "downloading a file from s3",
                "bucket": bucket_name,
                "key": key,
            }
        )

        response: Dict[str, Any] = {}
        error = None

        try:
            response = dict(self.client.get_object(Bucket=bucket_name, Key=key))

            logger.debug(
                {"metric_filter": "s3_download_response", "response": str(response)}
            )

        except Exception as e:  # pylint: disable=W0718
            error = str(e)
            logger.error({"metric_filter": "s3_download_error", "error": str(e)})
            raise RuntimeError(
                {
                    "metric_filter": "s3_download_error",
                    "error": str(e),
                    "bucket": bucket_name,
                    "key": key,
                }
            ) from e

        finally:
            logger.debug(
                {
                    "source": "download_file",
                    "action": "downloading a file from s3",
                    "bucket": bucket_name,
                    "key": key,
                    "response": response,
                    "errors": error,
                }
            )

        return response

    def __download_file(
        self,
        bucket: str,
        key: str,
        local_directory: str | None = None,
        local_file_path: str | None = None,
    ):
        if local_directory and local_file_path:
            raise ValueError(
                "Only one of local_directory or local_file_path can be provided"
            )

        if local_directory and not os.path.exists(local_directory):
            FileOperations.makedirs(local_directory)

        if local_file_path and not os.path.exists(os.path.dirname(local_file_path)):
            FileOperations.makedirs(os.path.dirname(local_file_path))

        file_name = self.__get_file_name_from_path(key)
        if local_directory is None and local_file_path is None:
            local_path = self.get_local_path_for_file(file_name)
        elif local_directory:
            local_path = os.path.join(local_directory, file_name)
        else:
            local_path = local_file_path

        logger.debug(
            {
                "source": "download_file",
                "action": "downloading a file from s3",
                "bucket": bucket,
                "key": key,
                "file_name": file_name,
                "local_path": local_path,
            }
        )

        error: str | None = None
        try:
            self.client.download_file(bucket, key, local_path)

        except Exception as e:  # pylint: disable=W0718
            error = str(e)
            logger.error({"metric_filter": "s3_download_error", "error": str(e)})

        file_exist = os.path.exists(local_path)

        logger.debug(
            {
                "source": "download_file",
                "action": "downloading a file from s3",
                "bucket": bucket,
                "key": key,
                "file_name": file_name,
                "local_path": local_path,
                "file_downloaded": file_exist,
                "errors": error,
            }
        )

        if not file_exist:
            raise FileNotFoundError("File Failed to download (does not exist) from S3.")

        return local_path

    def __get_file_name_from_path(self, path: str) -> str:
        """
        Get a file name from the path

        Args:
            path (str): a file path

        Returns:
            str: the file name
        """
        return path.rsplit("/")[-1]

    def get_local_path_for_file(self, file_name: str):
        """
        Get a local temp location for a file.
        This is designed to work with lambda functions.
        The /tmp directory is the only writeable location for lambda functions.
        """
        temp_dir = self.get_temp_directory()
        # use /tmp it's the only writeable location for lambda
        local_path = os.path.join(temp_dir, file_name)
        return local_path

    def get_temp_directory(self):
        """
        Determines the appropriate temporary directory based on the environment.
        If running in AWS Lambda, returns '/tmp'.
        Otherwise, returns the system's standard temp directory.
        """
        if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
            # In AWS Lambda environment
            return "/tmp"
        else:
            # Not in AWS Lambda, use the system's default temp directory
            return tempfile.gettempdir()

    def encode(
        self, text: str, encoding: str = "utf-8", errors: str = "strict"
    ) -> bytes:
        """
        Encodes a string for s3
        """
        return text.encode(encoding=encoding, errors=errors)

    def decode(
        self, file_obj: bytes, encoding: str = "utf-8", errors: str = "strict"
    ) -> str:
        """
        Decodes bytes to a string
        """
        return file_obj.decode(encoding=encoding, errors=errors)
