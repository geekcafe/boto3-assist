"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import Optional, Any
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

    def remove_primary(self):
        """Remove the primary index"""
        if DynamoDBIndexes.PRIMARY_INDEX in self.__indexes:
            del self.__indexes[DynamoDBIndexes.PRIMARY_INDEX]

    def add_primary(self, index: DynamoDBIndex):
        """Add an index"""
        index.name = DynamoDBIndexes.PRIMARY_INDEX

        if index.name in self.__indexes:
            raise ValueError(
                f"The index {index.name} is already defined in your model somewhere. "
                "This error is generated to protect you from unforseen issues. "
                "If you models are inheriting from other models, you may have the primary defined twice."
            )

        self.__indexes[DynamoDBIndexes.PRIMARY_INDEX] = index

    def add_secondary(self, index: DynamoDBIndex):
        """Add a GSI/LSI index"""
        if index.name is None:
            raise ValueError("Index name cannot be None")

        # if the index already exists, raise an exception
        if index.name in self.__indexes:
            raise ValueError(
                f"The index {index.name} is already defined in your model somewhere. "
                "This error is generated to protect you from unforseen issues. "
                "If you models are inheriting from other models, you may have the primary defined twice."
            )
        if index.name == DynamoDBIndexes.PRIMARY_INDEX:
            raise ValueError(f"Index {index.name} is reserved for the primary index")
        if index.partition_key is None:
            raise ValueError("Index must have a partition key")

        # check if the index.partition_key.attribute_name is already in the index
        for _, v in self.__indexes.items():
            if v.partition_key.attribute_name == index.partition_key.attribute_name:
                raise ValueError(
                    f"The attrubute {index.partition_key.attribute_name} is already being used by index "
                    f"{v.name}. "
                    f"Reusing this attribute would over write the value on index {v.name}"
                )
        # check if the gsi1.sort_key.attribute_name exists
        if index.sort_key is not None:
            for _, v in self.__indexes.items():
                if v.sort_key.attribute_name == index.sort_key.attribute_name:
                    raise ValueError(
                        f"The attrubute {index.sort_key.attribute_name} is already being used by index "
                        f"{v.name}. "
                        f"Reusing this attribute would over write the value on index {v.name}"
                    )

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
        low_value: Any = None,
        high_value: Any = None,
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
                low_value=low_value,
                high_value=high_value,
            )
            return key

    def _build_query_key(
        self,
        *,
        include_sort_key: bool = True,
        condition: str = "begins_with",
        low_value: Any = None,
        high_value: Any = None,
    ) -> And | Equals:
        """Get the GSI index name and key"""

        key: And | Equals = Key(f"{self.partition_key.attribute_name}").eq(
            self.partition_key.value
        )

        if (
            include_sort_key
            and self.sort_key.attribute_name
            and (
                self.sort_key.value
                or (low_value is not None and high_value is not None)
            )
        ):
            # if self.sk_value_2:
            if low_value is not None and high_value is not None:
                match condition:
                    case "between":
                        low = f"{self.sort_key.value}{low_value}"
                        high = f"{self.sort_key.value}{high_value}"
                        key = key & Key(f"{self.sort_key.attribute_name}").between(
                            low, high
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
