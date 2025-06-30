"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional

from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class User(DynamoDBModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        super().__init__(self)
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.age: Optional[int] = None
        self.__email: Optional[str] = None
        # known reserved words
        self.status: Optional[str] = None

        self.__setup_indexes()

    def __setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        self.indexes.add_primary(primary)

        gsi0: DynamoDBIndex = DynamoDBIndex(index_name="gsi0")
        gsi0.partition_key.attribute_name = "gsi0_pk"
        gsi0.partition_key.value = lambda: DynamoDBKey.build_key(("users", None))
        gsi0.sort_key.attribute_name = "gsi0_sk"
        gsi0.sort_key.value = lambda: DynamoDBKey.build_key(("email", self.email))
        self.indexes.add_secondary(gsi0)

        gsi1: DynamoDBIndex = DynamoDBIndex(index_name="gsi1")
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(("users", None))
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
            ("lastname", self.last_name), ("firstname", self.first_name)
        )
        self.indexes.add_secondary(gsi1)

        gsi0: DynamoDBIndex = DynamoDBIndex(index_name="gsi2")
        gsi0.partition_key.attribute_name = "gsi2_pk"
        gsi0.partition_key.value = lambda: DynamoDBKey.build_key(("users", None))
        gsi0.sort_key.attribute_name = "gsi2_sk"
        gsi0.sort_key.value = lambda: DynamoDBKey.build_key(
            ("firstname", self.first_name), ("lastname", self.last_name)
        )
        self.indexes.add_secondary(gsi0)

    @property
    def email(self) -> str:
        if not self.__email and not self.__actively_serializing_data__:
            raise ValueError("Email is required.")
        return self.__email

    @email.setter
    def email(self, value: str):
        self.__email = value.lower()
