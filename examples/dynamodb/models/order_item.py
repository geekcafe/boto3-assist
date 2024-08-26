"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class OrderItem(DynamoDBModelBase):
    """Order Model"""

    def __init__(self) -> None:
        super().__init__()
        self.id: Optional[str] = None
        self.order_id: Optional[str] = None

        self.product_id: Optional[str] = None
        self.product_name: Optional[str] = None
        self.quantity: Optional[int] = 0
        self.price: Optional[float] = 0.0
        self.is_taxable: bool = False
        self.is_discounted: bool = False
        self.created_utc: Optional[datetime.datetime] = None
        self.modified_utc: Optional[datetime.datetime] = None
        self.status: Optional[str] = None
        self.total: Optional[float] = None
        self.tax_total: Optional[float] = None
        self.__setup_indexes()

    def __setup_indexes(self):
        # user id
        primay: DynamoDBIndex = DynamoDBIndex()
        primay.name = "primary"
        primay.partition_key.attribute_name = "pk"
        primay.partition_key.value = lambda: DynamoDBKey.build_key(
            ("order", self.order_id)
        )

        primay.sort_key.attribute_name = "sk"
        primay.sort_key.value = lambda: DynamoDBKey.build_key(("item", self.id))
        self.indexes.add_primary(primay)
