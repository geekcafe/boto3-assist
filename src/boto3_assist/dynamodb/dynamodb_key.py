"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import List, Dict, Any, Callable
from boto3.dynamodb.conditions import (
    ConditionBase,
    Key,
    Equals,
    ComparisonCondition,
)


class DynamoDbKey:
    """DynamoDb Key"""

    def __init__(self) -> None:
        self.index_name: str | None = None
        self.pk_name: str | None = None
        self.pk_value: str | None = None
        self.sk_name: str | None = None
        self.sk_value: str | None = None
        self.sk_value_2: str | None = None
        self.__pk: Equals | None = None
        self.__sk: Key | ConditionBase | ComparisonCondition | None = None
        self.__composite_key: Key | ConditionBase | ComparisonCondition | None = None
        self.condition: ConditionBase | None = None

    @property
    def pk(self) -> Equals:
        """Get the primary key"""
        if self.__pk is None:
            raise ValueError("Primary key not set")
        return self.__pk

    @pk.setter
    def pk(self, value: Equals):
        self.__pk = value

    @property
    def sk(self) -> Key | ConditionBase | ComparisonCondition | None:
        """Get the sort key"""
        return self.__sk

    @sk.setter
    def sk(self, value: Key | ConditionBase | ComparisonCondition):
        self.__sk = value

    @property
    def composite_key(self) -> Key | ConditionBase | ComparisonCondition | None:
        """Get the composite key"""
        return self.__composite_key

    @composite_key.setter
    def composite_key(self, value: Key | ConditionBase | ComparisonCondition):
        self.__composite_key = value

    def populate_key(
        self, key_configs: List[Dict[str, Any]], key: DynamoDbKey
    ) -> DynamoDbKey:
        """
        Populate a key with it's given value

        Args:
            sefl (_type_): _description_
            key_configs (dict): _description_
            key (DynamoDbKey): _description_

        Raises:
            ValueError: _description_

        Returns:
            DynamoDbKey: _description_
        """

        # should be in a list format
        if isinstance(key_configs, list) and len(key_configs) > 0:
            pass
        else:
            raise ValueError(
                f"Could not find key_configurations for DynamoDB index {key.index_name}"
            )
        # get the correct key

        k: dict
        found: bool = False
        for k in key_configs:
            if isinstance(k, dict):
                found, key = self._build_key(k, key)
                if found:
                    break

        return key

    def _build_key(
        self, key_config: dict, key: DynamoDbKey
    ) -> tuple[bool, DynamoDbKey]:
        value: str | Callable[[], str] | None = None
        for index, index_value in key_config.items():
            if index == key.index_name:
                if isinstance(index_value, dict):
                    pk_index_key: dict = index_value.get("pk", {})
                    if isinstance(pk_index_key, dict) and len(pk_index_key) > 0:
                        value = pk_index_key.get("value", None)

                        if callable(value):
                            value = value()
                        key.pk_value = value
                        key.pk_name = pk_index_key.get("attribute", None)

                    sk_index_key: dict = index_value.get("sk", {})
                    if isinstance(sk_index_key, dict) and len(sk_index_key) > 0:
                        value = sk_index_key.get("value", None)

                        if callable(value):
                            value = value()
                        key.sk_value = value
                        key.sk_name = sk_index_key.get("attribute", None)

                return True, key
        return False, key

    def build_key(
        self,
        condition: str = "begins_with",
    ) -> DynamoDbKey:
        """Get the GSI index name and key"""
        key = self

        key.pk = Key(f"{key.pk_name}").eq(key.pk_value)

        if key.sk_name and key.sk_value:
            if key.sk_value_2:
                match condition:
                    case "between":
                        key.composite_key = key.pk & Key(f"{key.sk_name}").between(
                            key.sk_value, key.sk_value_2
                        )

            else:
                match condition:
                    case "begins_with":
                        key.composite_key = key.pk & Key(f"{key.sk_name}").begins_with(
                            key.sk_value
                        )
                    case "eq":
                        key.composite_key = key.pk & Key(f"{key.sk_name}").eq(
                            key.sk_value
                        )
                    case "gt":
                        key.composite_key = key.pk & Key(f"{key.sk_name}").gt(
                            key.sk_value
                        )
                    case "gte":
                        key.composite_key = key.pk & Key(f"{key.sk_name}").gte(
                            key.sk_value
                        )
                    case "lt":
                        key.composite_key = key.pk & Key(f"{key.sk_name}").lt(
                            key.sk_value
                        )

        return key

    def get_keys(
        self, key_configs: List[Dict], exclude_pk: bool = False
    ) -> List[DynamoDbKey]:
        """_summary_

        Args:
            key_configs (List[Dict]): _description_
            index_name (str): _description_

        Returns:
            List[Dict]: _description_
        """
        keys: List[DynamoDbKey] = []
        for k in key_configs:
            if isinstance(k, dict):
                for index, _ in k.items():
                    # print(index, index_value)
                    if index == "primary_key" and exclude_pk:
                        continue
                    key: DynamoDbKey = DynamoDbKey()
                    key.index_name = index
                    key = self.populate_key(key_configs, key)
                    keys.append(key)

        return keys

    def keys_to_dictionary(self, keys: List[DynamoDbKey]) -> dict:
        """_summary_

        Args:
            keys (List[DynamoDbKey]): _description_

        Returns:
            dict: _description_
        """
        key_dict: dict = {}
        for key in keys:
            if key.pk_name and key.pk_value:
                key_dict[key.pk_name] = key.pk_value
            if key.sk_name and key.sk_value:
                key_dict[key.sk_name] = key.sk_value

        return key_dict
