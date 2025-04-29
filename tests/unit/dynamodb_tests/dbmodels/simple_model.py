"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional

from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class Simple(DynamoDBModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        DynamoDBModelBase.__init__(self)
        self.id: Optional[str] = id

        self.__setup_indexes()

    def __setup_indexes(self):
        primary_key: DynamoDBIndex = DynamoDBIndex(
            index_name="primary_key",
            partition_key=DynamoDBKey(
                attribute_name="pk",
                value=lambda: DynamoDBKey.build_key((("user", self.id))),
            ),
            sort_key=DynamoDBKey(
                attribute_name="sk",
                value=lambda: DynamoDBKey.build_key(("user", self.id)),
            ),
        )
        self.indexes.add_primary(primary_key)
