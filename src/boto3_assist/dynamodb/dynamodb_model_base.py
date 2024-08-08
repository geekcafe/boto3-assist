"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime as dt
import decimal
import inspect
import uuid
from typing import Tuple, Callable, Mapping, TypeVar, Dict, List
from boto3.dynamodb.conditions import And, Equals
from boto3.dynamodb.types import TypeSerializer
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_helpers import DynamoDbHelpers, DynamoDbKeys


def exclude_from_serialization(method):
    """
    Decorator to mark methods or properties to be excluded from serialization.
    """
    method.exclude_from_serialization = True
    return method


class DynamoDbModelBase:
    """DyanmoDb Model Base"""

    T = TypeVar("T", bound="DynamoDbModelBase")

    def __init__(self) -> None:
        self.__key_configs: Mapping[str, Mapping[str, Callable[[], str]]] | str = {}
        self.__projection_expression: str | None = None
        self.__projection_expression_attribute_names: dict | None = None
        self.__helpers: DynamoDbHelpers | None = None

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
        pk = self.get_pk("primary_key")
        if pk is None:
            raise ValueError("Primary key not set")
        return pk

    @property
    def sk(self) -> str:
        """The key"""
        sk = self.get_sk("primary_key")
        if sk is None:
            raise ValueError("Sort key not set")
        return sk

    def get_primary_key(self) -> dict:  # pylint: disable=w0622
        """Gets the key for the primay pk and sk key pair"""
        pk = self.pk
        sk = self.sk

        key = {
            "pk": pk,
            "sk": sk,
        }

        return key

    def map(self, item: dict) -> T | "DynamoDbModelBase":
        """Map the item to the instance"""

        if "Item" in item:
            item = item["Item"]

        if item is None:
            raise ValueError("Item cannot be None")

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

    def get_key_data(
        self, index_name: str, condition: str = "begins_with"
    ) -> Tuple[str, And | Equals]:
        """Get the index name and key"""

        if index_name is None:
            raise ValueError("Index name cannot be None")

        keys: DynamoDbKeys = DynamoDbKeys()
        keys.index_name = index_name
        self.helpers.populate_keys(self.key_configs, keys=keys)

        key = self.helpers.build_keys(
            pk_name=keys.pk_name,
            pk_value=keys.pk_value,
            sk_name=keys.sk_name,
            sk_value=keys.sk_value,
            condition=condition,
        )

        return index_name, key

    def get_pk(self, index_name: str) -> str | None:
        """Get the partition key for a given GSI index"""
        return DynamoDbHelpers.get_key(self.key_configs, index_name, "pk")

    def get_sk(self, index_name: str) -> str | None:
        """Get the sort key for a given GSI index"""
        return DynamoDbHelpers.get_key(self.key_configs, index_name, "sk")

    @property
    @exclude_from_serialization
    def helpers(self) -> DynamoDbHelpers:
        """Get the helpers"""
        if self.__helpers is None:
            self.__helpers = DynamoDbHelpers()
        return self.__helpers


class DynamoDbSerializer:
    """Library to Serialize object to a DynamoDB Format"""

    T = TypeVar("T", bound=DynamoDbModelBase)

    @staticmethod
    def map(source: dict, target: T) -> T:
        """
        Map the source dictionary to the target object.

        Args:
        - source: The dictionary to map from.
        - target: The object to map to.
        """
        mapped = Serialization.map(source, target)
        if mapped is None:
            raise ValueError("Unable to map source to target")

        return mapped

    @staticmethod
    def to_client_dictionary(instance: DynamoDbModelBase):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB client.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB client.
        """
        serializer = TypeSerializer()
        return DynamoDbSerializer._serialize(instance, serializer.serialize)

    @staticmethod
    def to_resource_dictionary(instance: DynamoDbModelBase):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB resource.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB resource.
        """
        return DynamoDbSerializer._serialize(instance, lambda x: x)

    @staticmethod
    def _serialize(instance: object, serialize_fn):
        def is_primitive(value):
            """Check if the value is a primitive data type."""
            return isinstance(value, (str, int, float, bool, type(None)))

        def serialize_value(value):
            """Serialize the value using the provided function."""
            if isinstance(value, dt.datetime):
                return serialize_fn(value.isoformat())
            elif isinstance(value, decimal.Decimal):
                return serialize_fn(str(value))
            elif isinstance(value, uuid.UUID):
                return serialize_fn(str(value))
            elif isinstance(value, (bytes, bytearray)):
                return serialize_fn(value.hex())
            elif is_primitive(value):
                return serialize_fn(value)
            elif isinstance(value, list):
                return serialize_fn([serialize_value(v) for v in value])
            elif isinstance(value, dict):
                return serialize_fn({k: serialize_value(v) for k, v in value.items()})
            else:
                return serialize_fn(DynamoDbSerializer._serialize(value, serialize_fn))

        instance_dict = DynamoDbSerializer._add_properties(instance, serialize_value)
        instance_dict = DynamoDbSerializer._add_key_attributes(instance, instance_dict)
        return instance_dict

    @staticmethod
    def _add_properties(instance: object, serialize_value) -> dict:
        instance_dict = {}
        # Add instance variables
        for attr, value in instance.__dict__.items():
            # don't get the private properties
            if not str(attr).startswith("_"):
                if value is not None:
                    instance_dict[attr] = serialize_value(value)

        # Add properties
        for name, _ in inspect.getmembers(
            instance.__class__, predicate=inspect.isdatadescriptor
        ):
            prop = None
            try:
                prop = getattr(instance.__class__, name)
            except AttributeError:
                continue
            if isinstance(prop, property):
                # Exclude properties marked with the exclude_from_serialization decorator
                # Check if the property should be excluded
                exclude = getattr(prop.fget, "exclude_from_serialization", False)
                if exclude:
                    continue

                # don't get the private properties
                if not str(name).startswith("_"):
                    value = getattr(instance, name)
                    if value is not None:
                        instance_dict[name] = serialize_value(value)

        return instance_dict

    @staticmethod
    def _add_key_attributes(instance: DynamoDbModelBase, instance_dict: dict) -> dict:
        print(instance.key_configs)
        keys: List[DynamoDbKeys] = instance.helpers.get_keys(instance.key_configs)
        for key in keys:
            if key.pk_name is not None and key.pk_value is not None:
                instance_dict[key.pk_name] = key.pk_value
            if key.sk_name is not None and key.sk_value is not None:
                instance_dict[key.sk_name] = key.sk_value

        return instance_dict
