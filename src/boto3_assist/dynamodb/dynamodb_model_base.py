"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from __future__ import annotations
import datetime as dt
import decimal
import inspect
import uuid

from typing import TypeVar, List
from boto3.dynamodb.types import TypeSerializer
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_helpers import DynamoDbHelpers
from boto3_assist.dynamodb.dynamodb_index import (
    DynamoDbIndexes,
    DynamoDbIndex,
)


def exclude_from_serialization(method):
    """
    Decorator to mark methods or properties to be excluded from serialization.
    """
    method.exclude_from_serialization = True
    return method


def exclude_indexes_from_serialization(method):
    """
    Decorator to mark methods or properties to be excluded from serialization.
    """
    method.exclude_indexes_from_serialization = True
    return method


class DynamoDbModelBase:
    """DyanmoDb Model Base"""

    T = TypeVar("T", bound="DynamoDbModelBase")

    def __init__(self) -> None:
        self.__projection_expression: str | None = None
        self.__projection_expression_attribute_names: dict | None = None
        self.__helpers: DynamoDbHelpers | None = None
        self.__indexes: DynamoDbIndexes | None = None

    @property
    @exclude_from_serialization
    def indexes(self) -> DynamoDbIndexes:
        """Gets the indexes"""
        # although this is marked as excluded, the indexes are add
        # but in a more specialized way
        if self.__indexes is None:
            self.__indexes = DynamoDbIndexes()
        return self.__indexes

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

    def map(self: T, item: dict | DynamoDbModelBase) -> T | None:
        """
        Map the item to the instance.  If the item is a DynamoDbModelBase,
        it will be converted to a dictionary first and then mapped.

        Args:
            self (T): The Type of object you are converting it to.
            item (dict | DynamoDbModelBase): _description_

        Raises:
            ValueError: If the object is not a dictionary or DynamoDbModelBase

        Returns:
            T | None: An object of type T with properties set matching
            that of the dictionary object or None
        """
        if isinstance(item, DynamoDbModelBase):
            item = item.to_resource_dictionary()

        if isinstance(item, dict):
            # see if this is coming directly from dynamodb
            if "ResponseMetadata" in item:
                response: dict | None = item.get("Item")

                if response is None:
                    return None

                item = response

        else:
            raise ValueError("Item must be a dictionary or DynamoDbModelBase")
        # attempt to map it
        return DynamoDbSerializer.map(source=item, target=self)

    def to_client_dictionary(self, include_indexes: bool = True):
        """
        Convert the instance to a dictionary suitable for DynamoDB client.
        """
        return DynamoDbSerializer.to_client_dictionary(
            self, include_indexes=include_indexes
        )

    def to_resource_dictionary(self, include_indexes: bool = True):
        """
        Convert the instance to a dictionary suitable for DynamoDB resource.
        """
        return DynamoDbSerializer.to_resource_dictionary(
            self, include_indexes=include_indexes
        )

    def get_key(self, index_name: str) -> DynamoDbIndex:
        """Get the index name and key"""

        if index_name is None:
            raise ValueError("Index name cannot be None")

        return self.indexes.get(index_name)

    @property
    @exclude_from_serialization
    def helpers(self) -> DynamoDbHelpers:
        """Get the helpers"""
        if self.__helpers is None:
            self.__helpers = DynamoDbHelpers()
        return self.__helpers

    def list_keys(self, exclude_pk: bool = False) -> List[DynamoDbIndex]:
        """List the keys"""
        values = self.indexes.values()
        if exclude_pk:
            values = [v for v in values if not v.name == DynamoDbIndexes.PRIMARY_INDEX]
        # print(value)
        # return self.helpers.get_keys(self.key_configs, exclude_pk=exclude_pk)
        return values


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
    def to_client_dictionary(instance: DynamoDbModelBase, include_indexes: bool = True):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB client.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB client.
        """
        serializer = TypeSerializer()
        return DynamoDbSerializer._serialize(
            instance, serializer.serialize, include_indexes=include_indexes
        )

    @staticmethod
    def to_resource_dictionary(
        instance: DynamoDbModelBase, include_indexes: bool = True
    ):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB resource.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB resource.
        """
        return DynamoDbSerializer._serialize(
            instance, lambda x: x, include_indexes=include_indexes
        )

    @staticmethod
    def _serialize(
        instance: DynamoDbModelBase, serialize_fn, include_indexes: bool = True
    ):
        def is_primitive(value):
            """Check if the value is a primitive data type."""
            return isinstance(value, (str, int, bool, type(None)))

        def serialize_value(value):
            """Serialize the value using the provided function."""

            if isinstance(value, DynamoDbModelBase):
                return serialize_fn(value.to_resource_dictionary(False))
            if isinstance(value, dt.datetime):
                return serialize_fn(value.isoformat())
            elif isinstance(value, float):
                return serialize_fn(decimal.Decimal(value))
            elif isinstance(value, decimal.Decimal):
                return serialize_fn(value)
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

        if include_indexes:
            instance_dict = DynamoDbSerializer._add_indexes(instance, instance_dict)
        return instance_dict

    @staticmethod
    def _add_properties(instance: DynamoDbModelBase, serialize_value) -> dict:
        instance_dict = {}
        include_indexes = True
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
    def _add_indexes(instance: DynamoDbModelBase, instance_dict: dict) -> dict:
        if not issubclass(type(instance), DynamoDbModelBase):
            return instance_dict

        if instance.indexes is None:
            return instance_dict

        primary = instance.indexes.primary

        if primary:
            instance_dict[primary.partition_key.attribute_name] = (
                primary.partition_key.value
            )
            if (
                primary.sort_key.attribute_name is not None
                and primary.sort_key.value is not None
            ):
                instance_dict[primary.sort_key.attribute_name] = primary.sort_key.value

        secondaries = instance.indexes.secondaries

        key: DynamoDbIndex
        for _, key in secondaries.items():
            if (
                key.partition_key.attribute_name is not None
                and key.partition_key.value is not None
            ):
                instance_dict[key.partition_key.attribute_name] = (
                    key.partition_key.value
                )
            if key.sort_key.value is not None and key.sort_key.value is not None:
                instance_dict[key.sort_key.attribute_name] = key.sort_key.value

        return instance_dict
