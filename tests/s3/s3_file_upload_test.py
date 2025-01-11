import os
import unittest
from pathlib import Path

import moto

from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.s3.s3 import S3
from boto3_assist.utilities.file_operations import FileOperations


@moto.mock_aws
class S3FileUploadTest(unittest.TestCase):
    """Test S3 File Upload"""

    def setUp(self):
        """Setup"""
        ev: EnvironmentLoader = EnvironmentLoader()
        # NOTE: you need to make sure the the env file below exists or you will get an error
        ev.load_environment_file(file_name=".env.unittest")

    def test_upload_file(self):
        """Test uploading a file"""
        s3 = S3()
        bucket_name: str = "test-bucket"
        s3.bucket.create(bucket_name=bucket_name)
        local_file_path: Path = Path(
            os.path.join(os.path.dirname(__file__), "files", "test.txt")
        )
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"File not found: {local_file_path}")

        s3.object.upload_file(
            bucket=bucket_name, key="test.txt", local_file_path=local_file_path
        )

    def test_upload_file_obj(self):
        """Test uploading a file"""
        s3 = S3()
        bucket_name: str = "test-bucket"
        s3.bucket.create(bucket_name=bucket_name)
        local_file_path: Path = Path(
            os.path.join(os.path.dirname(__file__), "files", "test.txt")
        )
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"File not found: {local_file_path}")

        data = FileOperations.read_file(local_file_path)

        s3.object.upload_file_obj(bucket=bucket_name, key="test.txt", file_obj=data)
