"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime as dt
from boto3_assist.utilities.string_utility import StringUtility
from boto3_assist.dynamodb.dynamodb_model_base import (
    DynamoDBModelBase,
    exclude_from_serialization,
)


class BaseCMSDBModel(DynamoDBModelBase):
    """
    The Base DB Model
    Sets a common set of properties for all models
    """

    def __init__(self) -> None:
        super().__init__()
        self.id: str = StringUtility.generate_uuid()
        self.created_utc: dt.datetime = dt.datetime.now(dt.UTC)
        self.updated_utc: dt.datetime = dt.datetime.now(dt.UTC)
        self.expires_utc: dt.datetime | None = None
        self.__content: str | None = None

    @property
    def expires_sk_friendly(self) -> str:
        """The expires sort key for an item"""
        if self.expires_utc is None:
            # a date in the far future
            return "9999-12-31T00:00:00Z"

        return self.expires_utc.isoformat()

    @expires_sk_friendly.setter
    def expires_sk_friendly(self, expires_sk_friendly: str):
        pass

    @property
    @exclude_from_serialization
    def content(self) -> str | None:
        """
        The content is runtime value.
        It is excluded from serialization to dynamodb.
        The actual content should be stored in S3, and pulled when needed.
        """
        return self.__content

    @content.setter
    def content(self, value: str) -> None:
        self.__content = value
