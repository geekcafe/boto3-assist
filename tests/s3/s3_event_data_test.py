import unittest

from boto3_assist.s3.s3_event_data import S3Event


class S3EventDataTests(unittest.TestCase):
    """Test S3 Event Data parsing"""

    def test_event_info(self):
        """Test the event information is parsed correctly"""
        event = self.helper_get_event_sample()
        s3_event: S3Event = S3Event(event=event)

        self.assertEqual(s3_event.version, "0")
        self.assertEqual(s3_event.id, "c576a9d9-edef-6aeb-cf6c-4fc0234bacdc")
        self.assertEqual(s3_event.detail_type, "Object Created")
        self.assertEqual(s3_event.source, "aws.s3")
        self.assertEqual(s3_event.account, "1111111111")
        self.assertEqual(s3_event.time, "2025-02-05T23:55:22Z")
        self.assertEqual(s3_event.region, "us-east-1")
        self.assertEqual(s3_event.resources, ["arn:aws:s3:::my_object_key"])
        self.assertEqual(s3_event.detail.version, "0")
        self.assertEqual(s3_event.detail.bucket.name, "my_object_key")
        self.assertEqual(
            s3_event.detail.object.key,
            "tenants/aaaaaaaaaaaaaa/users/bbbbbbbbbbbbbbbb/sample.json",
        )
        self.assertEqual(s3_event.detail.object.size, 6904)
        self.assertEqual(
            s3_event.detail.object.etag, "f50341a4fa42e09016e76d7878c4fdc5"
        )
        self.assertEqual(
            s3_event.detail.object.version_id, "58QKYNXF62Wo1y7CZUDrDM0ILh5ncSwf"
        )
        self.assertEqual(s3_event.detail.object.sequencer, "0067A3FA6A303C91A8")
        self.assertEqual(s3_event.detail.request_id, "F82R8XDNW8385Q6Y")
        self.assertEqual(s3_event.detail.requester, "959096737760")
        self.assertEqual(s3_event.detail.source_ip_address, "192.168.0.52")
        self.assertEqual(s3_event.detail.reason, "PutObject")

    def helper_get_event_sample(self):
        event = {
            "version": "0",
            "id": "c576a9d9-edef-6aeb-cf6c-4fc0234bacdc",
            "detail-type": "Object Created",
            "source": "aws.s3",
            "account": "1111111111",
            "time": "2025-02-05T23:55:22Z",
            "region": "us-east-1",
            "resources": ["arn:aws:s3:::my_object_key"],
            "detail": {
                "version": "0",
                "bucket": {"name": "my_object_key"},
                "object": {
                    "key": "tenants/aaaaaaaaaaaaaa/users/bbbbbbbbbbbbbbbb/sample.json",
                    "size": 6904,
                    "etag": "f50341a4fa42e09016e76d7878c4fdc5",
                    "version-id": "58QKYNXF62Wo1y7CZUDrDM0ILh5ncSwf",
                    "sequencer": "0067A3FA6A303C91A8",
                },
                "request-id": "F82R8XDNW8385Q6Y",
                "requester": "959096737760",
                "source-ip-address": "192.168.0.52",
                "reason": "PutObject",
            },
        }

        return event
