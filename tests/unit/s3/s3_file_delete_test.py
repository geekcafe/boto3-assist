import os
import unittest
from pathlib import Path

import moto

from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.s3.s3 import S3


@moto.mock_aws
class S3FileDeleteTest(unittest.TestCase):
    """Test S3 File Upload"""

    def setUp(self):
        """Setup"""
        ev: EnvironmentLoader = EnvironmentLoader()
        # NOTE: you need to make sure the the env file below exists or you will get an error
        ev.load_environment_file(file_name=".env.unittest")

    def test_delete_file(self):
        """Test uploading a file"""
        s3 = S3()
        bucket_name: str = "test-bucket"
        s3.bucket.create(bucket_name=bucket_name)
        s3.bucket.enable_versioning(bucket_name=bucket_name)
        local_file_path: Path = Path(
            os.path.join(os.path.dirname(__file__), "files", "test.txt")
        )
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"File not found: {local_file_path}")

        for _ in range(0, 5):
            # upload the same file over and over, it should create different versions
            s3.object.upload_file(
                bucket=bucket_name, key="test.txt", local_file_path=local_file_path
            )

        files = s3.object.delete_all_versions(bucket_name=bucket_name, key="test.txt")

        self.assertEqual(len(files), 5)

    def test_delete_file_including_delete_markers(self):
        """Test uploading a file"""
        s3 = S3()
        bucket_name: str = "unittest-bucket"
        test_file_name = "test.txt"
        key = "test_with_delete.txt"
        s3.bucket.create(bucket_name=bucket_name)
        s3.bucket.enable_versioning(bucket_name=bucket_name)
        local_file_path: Path = Path(
            os.path.join(os.path.dirname(__file__), "files", test_file_name)
        )
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"File not found: {local_file_path}")

        for _ in range(0, 5):
            # upload the same file over and over, it should create different versions
            s3.object.upload_file(
                bucket=bucket_name, key=key, local_file_path=local_file_path
            )

        files = s3.object.delete_all_versions(
            bucket_name=bucket_name, key=key, include_deleted=True
        )

        # we should have ten here, the original 5 and the deleted 5
        self.assertEqual(len(files), 5)

        files = s3.object.delete_all_versions(
            bucket_name=bucket_name, key=key, include_deleted=True
        )

        # we shouldn't have any more files here
        self.assertEqual(len(files), 0)

    def test_delete_file_including_delete_markers_2(self):
        """Test uploading a file"""
        s3 = S3()
        bucket_name: str = "unittest-bucket"
        test_file_name = "test.txt"
        key = "test_with_delete.txt"

        s3.bucket.create(bucket_name=bucket_name)

        s3.bucket.enable_versioning(bucket_name=bucket_name)
        local_file_path: Path = Path(
            os.path.join(os.path.dirname(__file__), "files", test_file_name)
        )
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"File not found: {local_file_path}")

        for _ in range(0, 5):
            # upload the same file over and over, it should create different versions
            s3.object.upload_file(
                bucket=bucket_name, key=key, local_file_path=local_file_path
            )

        # delete the latest which should add a deleted marker
        s3.object.delete(bucket_name=bucket_name, key=key)

        files = s3.object.delete_all_versions(
            bucket_name=bucket_name, key=key, include_deleted=True
        )

        # we should have ten here, the original 5 and the 1 deleted marker
        self.assertEqual(len(files), 6)

        files = s3.object.delete_all_versions(
            bucket_name=bucket_name, key=key, include_deleted=True
        )

        # we shouldn't have any more files here
        self.assertEqual(len(files), 0)


def main():
    """Main"""
    unittest.main()


if __name__ == "__main__":
    main()
