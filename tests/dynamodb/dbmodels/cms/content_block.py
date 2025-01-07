"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime as dt
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
from tests.dynamodb.models.cms.base import BaseCMSDBModel


class ContentBlock(BaseCMSDBModel):
    """
    Defines a content block.  Content blocks are used to store:
        - html
        - scripts
        - markdown
        - text
        - images
        - videos
        - etc
    """

    def __init__(self) -> None:
        super().__init__()
        self.id: str = StringUtility.generate_uuid()
        self.site_id: str | None = None
        """the site this content block belongs to"""
        self.created_utc: dt.datetime = dt.datetime.now(dt.UTC)
        self.updated_utc: dt.datetime = dt.datetime.now(dt.UTC)

        """if/when it expires"""
        self.title: str | None = None
        """title of the content block"""
        self.description: str | None = None
        """description of the content block"""
        self.block_type: str | None = None
        """type of content block"""

        self.__setup_indexes()

    def __setup_indexes(self):
        primay: DynamoDBIndex = DynamoDBIndex()
        primay.name = "primary"
        primay.partition_key.attribute_name = "pk"
        primay.partition_key.value = lambda: DynamoDBKey.build_key(
            ("site", self.site_id), ("block-type", self.block_type)
        )

        primay.sort_key.attribute_name = "sk"
        primay.sort_key.value = lambda: DynamoDBKey.build_key(("content", self.id))
        self.indexes.add_primary(primay)
