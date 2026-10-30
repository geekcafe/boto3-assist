"""
Tests for the optional POST-policy ``conditions`` on S3Object.generate_presigned_url.

moto does not enforce POST policies, so the policy document content is what we verify.
"""

import base64
import json
import unittest

import moto

from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.s3.s3 import S3


def _decode_policy(response: dict) -> dict:
    fields = response["signed_url"]["fields"]
    return json.loads(base64.b64decode(fields["policy"]).decode("utf-8"))


@moto.mock_aws
class S3PresignedPostConditionsTest(unittest.TestCase):
    """POST policy conditions pass-through."""

    def setUp(self):
        ev: EnvironmentLoader = EnvironmentLoader()
        ev.load_environment_file(file_name=".env.unittest")
        self.s3 = S3()
        self.bucket_name = "test-bucket"
        self.s3.bucket.create(bucket_name=self.bucket_name)

    def _presign(self, **kwargs) -> dict:
        return self.s3.object.generate_presigned_url(
            bucket_name=self.bucket_name,
            key_path="uploads/test.docx",
            file_name="test.docx",
            **kwargs,
        )

    def test_conditions_are_in_policy(self):
        response = self._presign(conditions=[["content-length-range", 1, 10485760]])
        policy = _decode_policy(response)
        self.assertIn(["content-length-range", 1, 10485760], policy["conditions"])

    def test_no_conditions_has_no_content_length_range(self):
        response = self._presign()
        policy = _decode_policy(response)
        for condition in policy["conditions"]:
            if isinstance(condition, list):
                self.assertNotEqual(condition[0], "content-length-range")
        # Default policy only carries bucket + key conditions (same as before).
        self.assertEqual(
            sorted(json.dumps(c, sort_keys=True) for c in policy["conditions"]),
            sorted(
                json.dumps(c, sort_keys=True)
                for c in [{"bucket": self.bucket_name}, {"key": "uploads/test.docx"}]
            ),
        )

    def test_conditions_with_put_raises(self):
        with self.assertRaises(ValueError):
            self._presign(method_type="PUT", conditions=[["content-length-range", 1, 10]])

    def test_conditions_with_get_raises(self):
        with self.assertRaises(ValueError):
            self._presign(method_type="GET", conditions=[["content-length-range", 1, 10]])


if __name__ == "__main__":
    unittest.main()
