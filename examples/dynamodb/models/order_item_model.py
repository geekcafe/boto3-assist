"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from examples.dynamodb.models.product_model import Product


class OrderItem(DynamoDBModelBase):
    """Order Model"""

    def __init__(self) -> None:
        super().__init__()
        self.id: Optional[str] = None
        self.order_id: Optional[str] = None
        self.product: Optional[Product] = None
        # self.product_id: Optional[str] = None
        # self.product_name: Optional[str] = None
        self.quantity: Optional[int] = 0
        # self.price: Optional[float] = 0.0
        # self.is_taxable: bool = False
        self.is_discounted: bool = False
        self.created_utc: Optional[datetime.datetime] = None
        self.modified_utc: Optional[datetime.datetime] = None
        self.status: Optional[str] = None
        self.total: Optional[float] = None
        self.tax_total: Optional[float] = None
        self.__setup_indexes()

    def __setup_indexes(self):
        # the primary key will be made off of the
        # order.id and this item.id
        # this will allow for a 1 to many search on the items related to an order
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        # create a partition key off of the order key
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("order", self.order_id)
        )

        # create the sort key off of this items id
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("item", self.id))
        self.indexes.add_primary(primary)
