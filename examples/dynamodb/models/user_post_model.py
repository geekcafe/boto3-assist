"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional

from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class UserPost(DynamoDBModelBase):
    """Database Model for the User Posts Entity"""

    def __init__(
        self,
        slug: Optional[str] = None,  # pylint: disable=w0622
        title: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.slug: Optional[str] = slug
        self.user_id: Optional[str] = user_id
        self.title: Optional[str] = title

        self.data: Optional[str] = None
        self.status: Optional[str] = None
        self.type: Optional[str] = None
        self.timestamp: str = str(datetime.datetime.now(datetime.UTC).timestamp())
        self.modified_datetime_utc: str = str(datetime.datetime.now(datetime.UTC))
        self.__setup_indexes()

    def __setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex(
            index_name="primary",
            partition_key=DynamoDBKey(
                attribute_name="pk",
                value=lambda: f"post#{self.slug if self.slug else ''}",
            ),
            sort_key=DynamoDBKey(
                attribute_name="sk",
                value=lambda: f"post#{self.slug if self.slug else ''}",
            ),
        )
        self.indexes.add_primary(primary)

        gsi0: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi0",
            partition_key=DynamoDBKey(attribute_name="gsi0_pk", value="posts#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi0_sk",
                value=lambda: f"title#{self.title if self.title else ''}",
            ),
        )

        self.indexes.add_secondary(gsi0)

        gsi1: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi1",
            partition_key=DynamoDBKey(attribute_name="gsi1_pk", value="posts#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi1_sk",
                value=lambda: f"ts#{self.timestamp if self.timestamp else ''}",
            ),
        )
        self.indexes.add_secondary(gsi1)

        gsi2: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi2",
            partition_key=DynamoDBKey(attribute_name="gsi2_pk", value="posts#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi2_sk",
                value=lambda: f"slug#{self.slug if self.slug else ''}",
            ),
        )

        self.indexes.add_secondary(gsi2)

        self.projection_expression = (
            "id,user_id,title,data,timestamp,modified_datetime_utc,#status,#type"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type",
        }
