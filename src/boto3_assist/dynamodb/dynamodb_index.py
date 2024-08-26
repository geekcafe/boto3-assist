"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import Optional
from boto3.dynamodb.conditions import (
    ConditionBase,
    Key,
    Equals,
    ComparisonCondition,
    And,
)
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class DynamoDBIndexes:
    """Track the indexes"""

    PRIMARY_INDEX = "primary"

    def __init__(self) -> None:
        self.__indexes: dict[str, DynamoDBIndex] = {}

    def add_primary(self, index: DynamoDBIndex):
        """Add an index"""
        index.name = DynamoDBIndexes.PRIMARY_INDEX
        self.__indexes[DynamoDBIndexes.PRIMARY_INDEX] = index

    def add_secondary(self, index: DynamoDBIndex):
        """Add a GSI/LSI index"""
        if index.name is None:
            raise ValueError("Index name cannot be None")
        self.__indexes[index.name] = index

    def get(self, index_name: str) -> DynamoDBIndex:
        """Get an index"""
        if index_name not in self.__indexes:
            raise ValueError(f"Index {index_name} not found")
        return self.__indexes[index_name]

    @property
    def primary(self) -> DynamoDBIndex | None:
        """Get the primary index"""
        if DynamoDBIndexes.PRIMARY_INDEX not in self.__indexes:
            return None
            # raise ValueError("Primary index not found")
        return self.__indexes[DynamoDBIndexes.PRIMARY_INDEX]

    @property
    def secondaries(self) -> dict[str, DynamoDBIndex]:
        """Get the secondary indexes"""
        # get all indexes that are not the primary index
        indexes = {
            k: v
            for k, v in self.__indexes.items()
            if k != DynamoDBIndexes.PRIMARY_INDEX
        }

        return indexes

    def values(self) -> list[DynamoDBIndex]:
        """Get the values of the indexes"""
        return list(self.__indexes.values())


class DynamoDBIndex:
    """A DynamoDB Index"""

    def __init__(
        self,
        index_name: Optional[str] = None,
        partition_key: Optional[DynamoDBKey] = None,
        sort_key: Optional[DynamoDBKey] = None,
        description: Optional[str] = None,
    ):
        self.name: Optional[str] = index_name
        self.description: Optional[str] = description
        """Optional description information.  Used for self documentation."""
        self.__pk: Optional[DynamoDBKey] = partition_key
        self.__sk: Optional[DynamoDBKey] = sort_key

    @property
    def partition_key(self) -> DynamoDBKey:
        """Get the primary key"""
        if not self.__pk:
            self.__pk = DynamoDBKey()
        return self.__pk

    @partition_key.setter
    def partition_key(self, value: DynamoDBKey):
        self.__pk = value

    @property
    def sort_key(self) -> DynamoDBKey:
        """Get the sort key"""
        if not self.__sk:
            self.__sk = DynamoDBKey()
        return self.__sk

    @sort_key.setter
    def sort_key(self, value: DynamoDBKey | None):
        self.__sk = value

    def key(
        self,
        *,
        include_sort_key: bool = True,
        condition: str = "begins_with",
        high_value: Optional[DynamoDBKey] = None,
        # sk_value_2: Optional[str | int | float] = None,
    ) -> dict | Key | ConditionBase | ComparisonCondition | Equals:
        """Get the key for a given index"""
        key: dict | Key | ConditionBase | ComparisonCondition | Equals
        if self.name == DynamoDBIndexes.PRIMARY_INDEX and include_sort_key:
            # this is a direct primary key which is used in a get call
            # this is differenet than query keys
            key = {}
            key[self.partition_key.attribute_name] = self.partition_key.value

            if self.sort_key and self.sort_key.attribute_name:
                key[self.sort_key.attribute_name] = self.sort_key.value

            return key
        else:
            key = self._build_query_key(
                include_sort_key=include_sort_key,
                condition=condition,
                high_value=high_value,
            )
            return key

    def _build_query_key(
        self,
        *,
        include_sort_key: bool = True,
        condition: str = "begins_with",
        high_value: Optional[DynamoDBKey] = None,
    ) -> And | Equals:
        """Get the GSI index name and key"""

        key: And | Equals = Key(f"{self.partition_key.attribute_name}").eq(
            self.partition_key.value
        )

        if include_sort_key and self.sort_key.attribute_name and self.sort_key.value:
            # if self.sk_value_2:
            if high_value:
                match condition:
                    case "between":
                        key = key & Key(f"{self.sort_key.attribute_name}").between(
                            self.sort_key.value, high_value.value
                        )

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
