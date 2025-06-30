"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Product(DynamoDBModelBase):
    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=w0622
        name: Optional[str] = None,
        price: float = 0.0,
        description: Optional[str] = None,
        sku: Optional[str] = None,
    ):
        super().__init__()

        self.id: Optional[str] = id
        self.name: Optional[str] = name
        self.price: float = price
        self.description: Optional[str] = description
        self.sku: Optional[str] = sku

        self.__setup_indexes()

    def __str__(self):
        return f"{self.name} - ${self.price}"

    def __setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("product", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("product", self.id))
        self.indexes.add_primary(primary)

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    # hot key warning
                    value=lambda: DynamoDBKey.build_key(("products", "")),
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: DynamoDBKey.build_key(("name", self.name)),
                ),
            )
        )
