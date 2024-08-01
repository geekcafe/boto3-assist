"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Tuple, Callable, Mapping
from boto3.dynamodb.conditions import Key, And
from boto_assist.dynamodb.dynamodb_model_serialization import (
    DynamoDbSerializer,
    exclude_from_serialization,
)
from boto_assist.dynamodb.dynamodb_model_base_gsi import DynamoDbModelBaseGSI
from boto_assist.dynamodb.dynamodb_model_base_lsi import DynamoDbModelBaseLSI


class DynamoDbModelBase(DynamoDbModelBaseGSI, DynamoDbModelBaseLSI):
    """DyanmoDb Model Base"""

    def __init__(self) -> None:
        self.__key_configs: Mapping[str, Mapping[str, Callable[[], str]]] | str = {}
        self.__projection_expression: str | None = None
        self.__projection_expression_attribute_names: dict | None = None

    @property
    @exclude_from_serialization
    def key_configs(self) -> Mapping[str, Mapping[str, Callable[[], str]]] | str:
        """Gets the key configs"""
        keys = self.__key_configs or {}
        return keys

    @key_configs.setter
    def key_configs(self, value: Mapping[str, Mapping[str, Callable[[], str]]] | str):
        self.__key_configs = value

    @property
    @exclude_from_serialization
    def projection_expression(self) -> str | None:
        """Gets the projection expression"""
        return self.__projection_expression

    @projection_expression.setter
    def projection_expression(self, value: str | None):
        self.__projection_expression = value

    @property
    @exclude_from_serialization
    def projection_expression_attribute_names(self) -> dict | None:
        """Gets the projection expression attribute names"""
        return self.__projection_expression_attribute_names

    @projection_expression_attribute_names.setter
    def projection_expression_attribute_names(self, value: dict | None):
        self.__projection_expression_attribute_names = value

    @property
    def pk(self) -> str:
        """The primary key"""
        pk = self.get_pk("pk_sk")
        if pk is None:
            raise ValueError("Primary key not set")
        return pk

    @property
    def sk(self) -> str:
        """The key"""
        sk = self.get_sk("pk_sk")
        if sk is None:
            raise ValueError("Sort key not set")
        return sk

    def pk_sk_key(self) -> dict:  # pylint: disable=w0622
        """Gets the key for the primay pk and sk key pair"""
        pk = self.pk
        sk = self.sk

        key = {
            "pk": pk,
            "sk": sk,
        }

        return key

    def map(self, item: dict) -> object | None:
        """Map the item to the instance"""
        return DynamoDbSerializer.map(source=item, target=self)

    def to_client_dictionary(self):
        """
        Convert the instance to a dictionary suitable for DynamoDB client.
        """
        return DynamoDbSerializer.to_client_dictionary(self)

    def to_resource_dictionary(self):
        """
        Convert the instance to a dictionary suitable for DynamoDB resource.
        """
        return DynamoDbSerializer.to_resource_dictionary(self)

    def get_gsi_key(self, index_name: str) -> Tuple[str, And]:
        """Get the GSI index name and key"""

        pk_value = self.get_pk(index_name)
        sk_value = self.get_sk(index_name)

        key = Key(f"{index_name}_pk").eq(pk_value) & Key(
            f"{index_name}_sk"
        ).begins_with(sk_value)

        return index_name, key

    def get_pk(self, index_name: str) -> str | None:
        """Get the partition key for a given GSI index"""
        return self.get_key(index_name, "pk")

    def get_sk(self, index_name: str) -> str | None:
        """Get the sort key for a given GSI index"""
        return self.get_key(index_name, "sk")

    def get_key(self, index_name: str, key_name: str | None) -> str | None:
        """Get the partition key for a given GSI index"""
        keys = self.key_configs
        config: Mapping[str, Callable[[], str]] | str | None = None

        if isinstance(keys, str):
            config = keys
        elif isinstance(keys, dict):
            config = keys.get(index_name)

        if not config:
            return None
        value: str | Callable[[], str] | None = None

        if isinstance(config, str):
            value = config
        elif isinstance(config, dict):
            if key_name is not None:
                value = config[key_name]

        if callable(value):
            return value()
        return value
