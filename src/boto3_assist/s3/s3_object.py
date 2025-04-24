"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import tempfile
import time
import io
from typing import Any, Dict, Optional, List

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from boto3_assist.errors.custom_exceptions import InvalidHttpMethod
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.utilities.datetime_utility import DatetimeUtility
from boto3_assist.utilities.file_operations import FileOperations
from boto3_assist.utilities.http_utility import HttpUtility
from boto3_assist.errors.custom_exceptions import FileNotFound

logger = Logger(child=True)


class S3Object:
    """S3 Object Actions"""

    def __init__(self, connection: S3Connection):
        self.connection = connection or S3Connection()

    def delete(self, *, bucket_name: str, key: str) -> Dict[str, Any]:
        """
        Deletes an object key

        Args:
            bucket_name (str): The AWS Bucket Name
            key (str): The Object Key
        """
        s3 = self.connection.client
        # see if the object exists
        try:
            response = s3.head_object(Bucket=bucket_name, Key=key)
            response = s3.delete_object(Bucket=bucket_name, Key=key)
        except s3.exceptions.NoSuchKey:
            response = {"ResponseMetadata": {"HTTPStatusCode": 404}}
        except s3.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                response = {"ResponseMetadata": {"HTTPStatusCode": 404}}
            else:
                raise e

        return dict(response)

    def delete_all_versions(
        self, *, bucket_name: str, key: str, include_deleted: bool = False
    ) -> List[str]:
        """
        Deletes an object key and all the versions for that object key

        Args:
            bucket_name (str): The AWS Bucket Name
            key (str): The Object Kuye
            include_deleted (bool, optional): Should deleted files be removed as well.
                If True it will look for the object keys with the deleted marker and remove it.
                Defaults to False.
        """
        s3 = self.connection.client
        paginator = s3.get_paginator("list_object_versions")
        files: List[str] = []

        for page in paginator.paginate(Bucket=bucket_name, Prefix=key):
            # Delete object versions
            if "Versions" in page:
                for version in page["Versions"]:
                    s3.delete_object(
                        Bucket=bucket_name,
                        Key=version["Key"],
                        VersionId=version["VersionId"],
                    )

                    files.append(f"{version['Key']} - {version['VersionId']}")

                if include_deleted:
                    # delete a previous files that may have just been a soft delete.
                    if "DeleteMarkers" in page:
                        for marker in page["DeleteMarkers"]:
                            s3.delete_object(
                                Bucket=bucket_name,
                                Key=marker["Key"],
                                VersionId=marker["VersionId"],
                            )

                            files.append(
                                f"{marker['Key']}:{marker['VersionId']}:delete-marker"
                            )
            else:
                response = self.delete(bucket_name=bucket_name, key=key)
                if response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                    return files

                files.append(key)

        return files

    def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        key_path: str,
        file_name: str,
        meta_data: Optional[dict] = None,
        expiration: int = 3600,
        method_type: str = "POST",
        user_id: Optional[str] = None,
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
            signed_url = self.connection.client.generate_presigned_url(
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
            signed_url = self.connection.client.generate_presigned_post(
                bucket_name,
                key,
                ExpiresIn=expiration,  # URL is valid for x seconds
            )
        elif method_type == "GET":
            signed_url = self.connection.client.generate_presigned_url(
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
        logger.debug(f"Signed URL created in {end - start}")

        response = {
            "signed_url": signed_url,
            "key": key,
            "meta_data": meta_data,
        }

        return response

    def put(self, *, bucket: str, key: str, data: bytes | str) -> str:
        """
        Uploads a file object to s3. Returns the full s3 path s3://<bucket>/<key>
        """
        return self.upload_file_obj(bucket=bucket, key=key, file_obj=data)

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
            file_obj = (
                file_obj.encode("utf-8") if isinstance(file_obj, str) else file_obj
            )
            self.connection.client.upload_fileobj(
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
            self.connection.client.upload_file(local_file_path, bucket, key)

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
        return self.get_object(bucket_name=bucket_name, key=key)

    def get_object(self, bucket_name: str, key: str) -> Dict[str, Any]:
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
            response = dict(
                self.connection.client.get_object(Bucket=bucket_name, Key=key)
            )

            logger.debug(
                {"metric_filter": "s3_download_response", "response": str(response)}
            )

        except Exception as e:  # pylint: disable=W0718
            error = str(e)
            error_info = {
                "metric_filter": "s3_download_error",
                "error": str(e),
                "bucket": bucket_name,
                "key": key,
            }

            logger.error(error_info)
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object.html
            error = str(e)
            if "An error occurred (AccessDenied)" in error:
                if (
                    "is not authorized to perform: s3:ListBucket on resource" in error
                    and "because no identity-based policy allows the s3:ListBucket action"
                    in error
                ):
                    # the file is not found but you're getting a access error since you don't
                    # have s3:ListBucket.  To make life easier, we're just going to return a 404 error
                    raise FileNotFound("File Not Found") from e

            # last ditch
            raise RuntimeError(error_info) from e

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
            self.connection.client.download_file(bucket, key, local_path)

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
        return FileOperations.get_tmp_directory()

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

    def list_versions(self, bucket: str, prefix: str = "") -> List[str]:
        """
        List all versions of objects in an S3 bucket with a given prefix.

        Args:
            bucket (str): The name of the S3 bucket.
            prefix (str, optional): The prefix to filter objects by. Defaults to "".

        Returns:
            list: A list of dictionaries containing information about each object version.
        """
        versions = []
        paginator = self.connection.client.get_paginator("list_object_versions")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        for page in page_iterator:
            if "Versions" in page:
                versions.extend(page["Versions"])

        return versions

    def copy(
        self,
        source_bucket: str,
        source_key: str,
        destination_bucket: str,
        destination_key: str,
    ) -> Dict[str, Any]:
        """
        Copies an object from one location to another.
        The original is kept.
        """

        if source_key.startswith("/"):
            # remove the first slash
            source_key = source_key[1:]

        if destination_key.startswith("/"):
            # remove the first slash
            destination_key = destination_key[1:]

        response = self.connection.client.copy_object(
            CopySource={"Bucket": source_bucket, "Key": source_key},
            Bucket=destination_bucket,
            Key=destination_key,
        )

        return dict(response)

    def move(
        self,
        source_bucket: str,
        source_key: str,
        destination_bucket: str,
        destination_key: str,
    ) -> Dict[str, Any]:
        """
        Copies an object from one location to another then deletes the source.
        The source is only deleted if the copy is successful
        """

        copy_response = self.connection.client.copy_object(
            CopySource={"Bucket": source_bucket, "Key": source_key},
            Bucket=destination_bucket,
            Key=destination_key,
        )

        status_code = copy_response.get("statusCode")
        delete_response = {}
        if status_code == 200:
            if source_key.startswith("/"):
                source_key = source_key[1:]
            delete_response = self.delete(bucket_name=source_bucket, key=source_key)
            status_code = copy_response.get("statusCode", status_code)

        response = {
            "status_code": status_code,
            "copy": copy_response,
            "delete": delete_response,
        }

        return response
