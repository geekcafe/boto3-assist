"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Dict, Any, List
from boto3_assist.utilities.numbers_utility import NumberUtility


class EventData:
    """An Event Data Object"""

    def __init__(self, event: Dict[str, Any]):
        self.__event = event

    @property
    def version(self) -> str | None:
        """Event Version"""
        return self.__event.get("version")

    @property
    def id(self) -> str | None:
        """Event Id"""
        return self.__event.get("id")

    @property
    def detail_type(self) -> str | None:
        """Event Detail Type"""
        return self.__event.get("detail-type")

    @property
    def source(self) -> str | None:
        """Event Source"""
        return self.__event.get("source")

    @property
    def account(self) -> str | None:
        """Event Account"""
        return self.__event.get("account")

    @property
    def time(self) -> str | None:
        """Event Time"""
        return self.__event.get("time")

    @property
    def region(self) -> str | None:
        """Event Region"""
        return self.__event.get("region")

    @property
    def resources(self) -> List[str]:
        """Event Resources"""
        return self.__event.get("resources", [])


class S3BucketData:
    """S3 Bucket Data"""

    def __init__(self, bucket_event_data: Dict[str, Any]):
        self.__bucket = bucket_event_data

    @property
    def name(self) -> str | None:
        """Bucket Name Key"""

        return self.__bucket.get("name")


class S3ObjectData:
    """S3 Object"""

    def __init__(self, object_data: Dict[str, Any]):
        self.__s3_object_data = object_data

    @property
    def key(self) -> str | None:
        """Object Key"""
        return self.__s3_object_data.get("key")

    @property
    def size(self) -> int:
        """Object size in bytes"""
        size = NumberUtility.to_number(self.__s3_object_data.get("size"))
        return size

    @property
    def etag(self) -> str | None:
        """Object eTag"""
        return self.__s3_object_data.get("etag")

    @property
    def version_id(self) -> str | None:
        """Object Version Id"""
        return self.__s3_object_data.get("version-id")

    @property
    def sequencer(self) -> str | None:
        """Object eTag"""
        return self.__s3_object_data.get("sequencer")


class S3EventDetail:
    """The Event Detail"""

    def __init__(self, event: Dict[str, Any]):
        self.__event = event
        self.__s3_object_data: S3ObjectData | None = None
        self.__s3_bucket_data: S3BucketData | None = None

    @property
    def version(self) -> str | None:
        """Object Key"""

        return self.__event.get("version")

    @property
    def bucket(self) -> S3BucketData:
        """S# Bucket Information"""
        if not self.__s3_bucket_data:
            self.__s3_bucket_data = S3BucketData(self.__event.get("bucket", {}))
        return self.__s3_bucket_data

    @property
    def object(self) -> S3ObjectData:
        """S3 Object Information"""
        if not self.__s3_object_data:
            self.__s3_object_data = S3ObjectData(self.__event.get("object", {}))

        return self.__s3_object_data

    @property
    def request_id(self) -> str | None:
        """Detail Request Id"""

        return self.__event.get("request-id")

    @property
    def requester(self) -> str | None:
        """Detail Requestor"""

        return self.__event.get("requester")

    @property
    def source_ip_address(self) -> str | None:
        """Source IP Address"""

        return self.__event.get("source-ip-address")

    @property
    def reason(self) -> str | None:
        """Reason"""

        return self.__event.get("reason")


class S3Event(EventData):
    """S3 Data Event"""

    def __init__(self, event):
        super().__init__(event)
        self.__detail: S3EventDetail = S3EventDetail(event=event.get("detail", {}))

    @property
    def detail(self) -> S3EventDetail:
        """S3 Specific Detail"""
        return self.__detail
