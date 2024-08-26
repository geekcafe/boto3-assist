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

    def __init__(self, id: Optional[str] = None) -> None:
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

    def __setup_indexes(self):
        # user id
        primay: DynamoDBIndex = DynamoDBIndex()
        primay.name = "primary"
        primay.partition_key.attribute_name = "pk"
        primay.partition_key.value = lambda: DynamoDBKey.build_key(("order", self.id))
        primay.sort_key.attribute_name = "sk"
        primay.sort_key.value = lambda: DynamoDBKey.build_key(("order", self.id))
        self.indexes.add_primary(primay)

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value=lambda: DynamoDBKey.build_key(
                        ("orders", ""), ("user", self.user_id)
                    ),
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: DynamoDBKey.build_key(
                        ("completed_utc", self.created_utc)
                    ),
                ),
            )
        )
