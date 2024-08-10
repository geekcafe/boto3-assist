"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import Optional, Mapping, Callable
from boto3.dynamodb.conditions import (
    ConditionBase,
    Key,
    Equals,
    ComparisonCondition,
    And,
)
from boto3_assist.dynamodb.dynamodb_key_v2 import DynamoDbKey


class DynamoDbIndexes:
    """Track the indexes"""

    PRIMARY_INDEX = "primary"

    def __init__(self) -> None:
        self.__indexes: dict[str, DynamoDbIndex] = {}

    def add_primary(self, index: DynamoDbIndex):
        """Add an index"""
        index.name = DynamoDbIndexes.PRIMARY_INDEX
        self.__indexes[DynamoDbIndexes.PRIMARY_INDEX] = index

    def add_secondary(self, index: DynamoDbIndex):
        """Add a GSI/LSI index"""
        if index.name is None:
            raise ValueError("Index name cannot be None")
        self.__indexes[index.name] = index

    def get(self, index_name: str) -> DynamoDbIndex:
        """Get an index"""
        if index_name not in self.__indexes:
            raise ValueError(f"Index {index_name} not found")
        return self.__indexes[index_name]

    @property
    def primary(self) -> DynamoDbIndex | None:
        """Get the primary index"""
        if DynamoDbIndexes.PRIMARY_INDEX not in self.__indexes:
            return None
            # raise ValueError("Primary index not found")
        return self.__indexes[DynamoDbIndexes.PRIMARY_INDEX]

    @property
    def secondaries(self) -> dict[str, DynamoDbIndex]:
        """Get the secondary indexes"""
        # get all indexes that are not the primary index
        indexes = {
            k: v
            for k, v in self.__indexes.items()
            if k != DynamoDbIndexes.PRIMARY_INDEX
        }

        return indexes


class DynamoDbIndex:
    """A DynamoDb Index"""

    def __init__(
        self,
        index_name: Optional[str] = None,
        # pk_attribute_name: Optional[str] = None,
        # pk_value: Optional[Mapping[str, Callable[[], str]]] = None,
        # sk_attribute_name: Optional[str] = None,
        # sk_value: Optional[Mapping[str, Callable[[], str]]] = None,
        partition_key: Optional[DynamoDbKey] = None,
        sort_key: Optional[DynamoDbKey] = None,
    ):
        self.name: Optional[str] = index_name
        self.__pk: Optional[DynamoDbKey] = partition_key
        self.__sk: Optional[DynamoDbKey] = sort_key

    @property
    def partition_key(self) -> DynamoDbKey:
        """Get the primary key"""
        if not self.__pk:
            self.__pk = DynamoDbKey()
        return self.__pk

    @partition_key.setter
    def partition_key(self, value: DynamoDbKey):
        self.__pk = value

    @property
    def sort_key(self) -> DynamoDbKey:
        """Get the sort key"""
        if not self.__sk:
            self.__sk = DynamoDbKey()
        return self.__sk

    @sort_key.setter
    def sort_key(self, value: DynamoDbKey | None):
        self.__sk = value

    @property
    def key(self) -> dict | Key | ConditionBase | ComparisonCondition | Equals:
        """Get the key for a given index"""

        if self.name == DynamoDbIndexes.PRIMARY_INDEX:
            key = {}
            key[self.partition_key.attribute_name] = self.partition_key.value

            if self.sort_key and self.sort_key.attribute_name and self.sort_key.value:
                key[self.sort_key.attribute_name] = self.sort_key.value

            return key
        else:
            key = self._build_key()
            return key

    def _build_key(
        self,
        condition: str = "begins_with",
    ) -> And | Equals:
        """Get the GSI index name and key"""

        key = Key(f"{self.partition_key.attribute_name}").eq(self.partition_key.value)

        if self.sort_key.attribute_name and self.sort_key.value:
            # if self.sk_value_2:
            if False:
                match condition:
                    case "between":
                        key.composite_key = key.partition_key & Key(
                            f"{key.sk_name}"
                        ).between(key.sk_value, key.sk_value_2)

            else:
                match condition:
                    case "begins_with":
                        key = key & Key(f"{self.sort_key.attribute_name}").begins_with(
                            self.sort_key.value
                        )
                    case "eq":
                        key = key & Key(f"{self.sort_key.attribute_name}").eq(
                            self.sort_key.value
                        )
                    case "gt":
                        key = key & Key(f"{self.sort_key.attribute_name}").gt(
                            self.sort_key.value
                        )
                    case "gte":
                        key = key & Key(f"{self.sort_key.attribute_name}").gte(
                            self.sort_key.value
                        )
                    case "lt":
                        key = key & Key(f"{self.sort_key.attribute_name}").lt(
                            self.sort_key.value
                        )

        return key
