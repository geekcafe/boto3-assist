"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime as dt
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
from tests.unit.dynamodb_tests.db_models.cms.base import BaseCMSDBModel


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
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("site", self.site_id), ("block-type", self.block_type)
        )

        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("content", self.id))
        self.indexes.add_primary(primary)
