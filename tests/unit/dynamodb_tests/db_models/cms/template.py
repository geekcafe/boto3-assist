"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import List
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from tests.unit.dynamodb_tests.db_models.cms.base import BaseCMSDBModel


class Template(BaseCMSDBModel):
    """
    A site template

    """

    def __init__(self) -> None:
        super().__init__()

        self.site_id: str | None = None
        self.title: str | None = None
        self.type: str | None = None
        """Page,Blog Post, etc."""
        self.description: str | None = None
        self.blocks: List[str] = []
        """List of block id's"""
        self.__setup_indexes()

    def __setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("site", self.site_id), ("templates", None)
        )

        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("template", self.title))
        self.indexes.add_primary(primary)

        gsi1: DynamoDBIndex = DynamoDBIndex()
        gsi1.name = "gsi1"
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(("site", self.id))
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
            ("template-type", self.type)
        )
        self.indexes.add_secondary(gsi1)

    @property
    def s3_object_key(self) -> str:
        """The s3 object key for the template"""
        return f"{self.site_id}/template/{self.type}/{self.title}"

    @s3_object_key.setter
    def s3_object_key(self, value: str):
        # we don't set this field, but we also don't
        # want an error during the serialization process
        pass
