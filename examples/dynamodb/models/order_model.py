"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Order(DynamoDBModelBase):
    """Order Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=w0622
    ) -> None:
        super().__init__()
        self.id: Optional[str] = id
        self.user_id: Optional[str] = None
        self.created_utc: Optional[datetime.datetime] = None
        self.modified_utc: Optional[datetime.datetime] = None
        self.completed_utc: Optional[datetime.datetime] = None
        self.status: Optional[str] = None
        self.total: float = 0
        self.tax_total: float = 0
        self.__setup_indexes()

    def get_completed_utc_ts(self) -> float | str:
        """Get a time stamp representation of the completed date"""
        if self.completed_utc is None:
            return ""
        return self.completed_utc.timestamp()

    def get_completed_utc_yyyymmdd(self) -> str:
        """Get a time stamp representation of the completed date"""
        if self.completed_utc is None:
            return "yyyymmdd"
        value = f"{self.completed_utc.year}{str(self.completed_utc.month).zfill(2)}{str(self.completed_utc.day).zfill(2)}"
        return value

    def __setup_indexes(self):
        # user id
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("order", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("order", self.id))
        self.indexes.add_primary(primary)

        # all orders on a given day, sort by created date
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value=lambda: DynamoDBKey.build_key(
                        (
                            "yyyymmdd",
                            f"{self.get_completed_utc_yyyymmdd()}",
                        )
                    ),
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: DynamoDBKey.build_key(
                        # when dealing with things like timestamps (or any numberfields)
                        # you may want to exclude a prefix key
                        # e.g. instead of: ("completed_utc_ts", self.get_completed_utc_ts())
                        # do the following by passing an empty string
                        ("", self.get_completed_utc_ts())
                    ),
                ),
            )
        )

        # all user orders, sort by completed date
        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi1",
                partition_key=DynamoDBKey(
                    attribute_name="gsi1_pk",
                    value=lambda: DynamoDBKey.build_key(
                        ("user", self.user_id), ("orders", "")
                    ),
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi1_sk",
                    value=lambda: DynamoDBKey.build_key(
                        # when dealing with things like timestamps (or any numberfields)
                        # you may want to exclude a prefix key
                        # e.g. instead of: ("completed_utc_ts", self.get_completed_utc_ts())
                        # do the following by passing an empty string
                        (None, self.get_completed_utc_ts())
                    ),
                ),
            )
        )
