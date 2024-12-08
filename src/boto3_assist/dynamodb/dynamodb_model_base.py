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
from typing import TypeVar, List, Dict, Any
from boto3.dynamodb.types import TypeSerializer
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_helpers import DynamoDBHelpers
from boto3_assist.dynamodb.dynamodb_index import (
    DynamoDBIndexes,
    DynamoDBIndex,
)
from boto3_assist.dynamodb.dynamodb_reserved_words import DynamoDBReservedWords


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


class DynamoDBModelBase:
    """DyanmoDb Model Base"""

    T = TypeVar("T", bound="DynamoDBModelBase")

    def __init__(self, auto_generate_projections: bool = True) -> None:
        self.__projection_expression: str | None = None
        self.__projection_expression_attribute_names: dict | None = None
        self.__helpers: DynamoDBHelpers | None = None
        self.__indexes: DynamoDBIndexes | None = None
        self.__reserved_words: DynamoDBReservedWords = DynamoDBReservedWords()
        self.__auto_generate_projections: bool = auto_generate_projections

    @property
    @exclude_from_serialization
    def indexes(self) -> DynamoDBIndexes:
        """Gets the indexes"""
        # although this is marked as excluded, the indexes are add
        # but in a more specialized way
        if self.__indexes is None:
            self.__indexes = DynamoDBIndexes()
        return self.__indexes

    @property
    @exclude_from_serialization
    def projection_expression(self) -> str | None:
        """Gets the projection expression"""
        prop_list: List[str] = []
        if self.__projection_expression is None and self.auto_generate_projections:
            props = self.to_dictionary()
            # turn props to a list[str]
            prop_list = list(props.keys())
        else:
            if self.__projection_expression:
                prop_list = self.__projection_expression.split(",")
                prop_list = [p.strip() for p in prop_list]

        if len(prop_list) == 0:
            return None

        transformed_list = self.__reserved_words.tranform_projections(prop_list)
        self.projection_expression = ",".join(transformed_list)

        return self.__projection_expression

    @projection_expression.setter
    def projection_expression(self, value: str | None):
        self.__projection_expression = value

    @property
    @exclude_from_serialization
    def auto_generate_projections(self) -> bool:
        """Gets the auto generate projections"""
        return self.__auto_generate_projections

    @auto_generate_projections.setter
    def auto_generate_projections(self, value: bool):
        self.__auto_generate_projections = value

    @property
    @exclude_from_serialization
    def projection_expression_attribute_names(self) -> dict | None:
        """
        Gets the projection expression attribute names

        """
        if (
            self.__projection_expression_attribute_names is None
            and self.auto_generate_projections
        ):
            props = self.to_dictionary()
            # turn props to a list[str]
            prop_list = list(props.keys())
            self.projection_expression_attribute_names = (
                self.__reserved_words.transform_attributes(prop_list)
            )
        else:
            if self.projection_expression:
                expression_list = self.projection_expression.replace("#", "").split(",")
                self.projection_expression_attribute_names = (
                    self.__reserved_words.transform_attributes(expression_list)
                )

        return self.__projection_expression_attribute_names

    @projection_expression_attribute_names.setter
    def projection_expression_attribute_names(self, value: dict | None):
        self.__projection_expression_attribute_names = value

    def map(self: T, item: Dict[str, Any] | DynamoDBModelBase | None) -> T | None:
        """
        Map the item to the instance.  If the item is a DynamoDBModelBase,
        it will be converted to a dictionary first and then mapped.

        Args:
            self (T): The Type of object you are converting it to.
            item (dict | DynamoDBModelBase): _description_

        Raises:
            ValueError: If the object is not a dictionary or DynamoDBModelBase

        Returns:
            T | None: An object of type T with properties set matching
            that of the dictionary object or None
        """
        if item is None:
            return None

        if isinstance(item, DynamoDBModelBase):
            item = item.to_resource_dictionary()

        if isinstance(item, dict):
            # see if this is coming directly from dynamodb
            if "ResponseMetadata" in item:
                response: dict | None = item.get("Item")

                if response is None:
                    return None

                item = response

        else:
            raise ValueError("Item must be a dictionary or DynamoDBModelBase")
        # attempt to map it
        return DynamoDBSerializer.map(source=item, target=self)

    def to_client_dictionary(self, include_indexes: bool = True):
        """
        Convert the instance to a dictionary suitable for DynamoDB client.
        """
        return DynamoDBSerializer.to_client_dictionary(
            self, include_indexes=include_indexes
        )

    def to_resource_dictionary(
        self, include_indexes: bool = True, include_none: bool = False
    ):
        """
        Convert the instance to a dictionary suitable for DynamoDB resource.
        """
        return DynamoDBSerializer.to_resource_dictionary(
            self, include_indexes=include_indexes, include_none=include_none
        )

    def to_dictionary(self, include_none: bool = True):
        """
        Convert the instance to a dictionary without an indexes/keys.
        Usefull for turning an object into a dictionary for serialization.
        This is the same as to_resource_dictionary(include_indexes=False)
        """
        return DynamoDBSerializer.to_resource_dictionary(
            self, include_indexes=False, include_none=include_none
        )

    def get_key(self, index_name: str) -> DynamoDBIndex:
        """Get the index name and key"""

        if index_name is None:
            raise ValueError("Index name cannot be None")

        return self.indexes.get(index_name)

    @property
    @exclude_from_serialization
    def helpers(self) -> DynamoDBHelpers:
        """Get the helpers"""
        if self.__helpers is None:
            self.__helpers = DynamoDBHelpers()
        return self.__helpers

    def list_keys(self, exclude_pk: bool = False) -> List[DynamoDBIndex]:
        """List the keys"""
        values = self.indexes.values()
        if exclude_pk:
            values = [v for v in values if not v.name == DynamoDBIndexes.PRIMARY_INDEX]

        return values


class DynamoDBSerializer:
    """Library to Serialize object to a DynamoDB Format"""

    T = TypeVar("T", bound=DynamoDBModelBase)

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
    def to_client_dictionary(instance: DynamoDBModelBase, include_indexes: bool = True):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB client.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB client.
        """
        serializer = TypeSerializer()
        return DynamoDBSerializer._serialize(
            instance, serializer.serialize, include_indexes=include_indexes
        )

    @staticmethod
    def to_resource_dictionary(
        instance: DynamoDBModelBase,
        include_indexes: bool = True,
        include_none: bool = False,
    ):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB resource.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB resource.
        """
        return DynamoDBSerializer._serialize(
            instance,
            lambda x: x,
            include_indexes=include_indexes,
            include_none=include_none,
        )

    @staticmethod
    def _serialize(
        instance: DynamoDBModelBase,
        serialize_fn,
        include_indexes: bool = True,
        include_none: bool = True,
    ):
        def is_primitive(value):
            """Check if the value is a primitive data type."""
            return isinstance(value, (str, int, bool, type(None)))

        def serialize_value(value):
            """Serialize the value using the provided function."""

            if isinstance(value, DynamoDBModelBase):
                return serialize_fn(
                    value.to_resource_dictionary(
                        include_indexes=False, include_none=include_none
                    )
                )
            if isinstance(value, dt.datetime):
                return serialize_fn(value.isoformat())
            elif isinstance(value, float):
                v = serialize_fn(decimal.Decimal(str(value)))
                return v
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
                return serialize_fn(
                    DynamoDBSerializer._serialize(
                        value,
                        serialize_fn,
                        include_indexes=include_indexes,
                        include_none=include_none,
                    )
                )

        instance_dict = DynamoDBSerializer._add_properties(
            instance, serialize_value, include_none=include_none
        )

        if include_indexes:
            instance_dict = DynamoDBSerializer._add_indexes(instance, instance_dict)
        return instance_dict

    @staticmethod
    def _add_properties(
        instance: DynamoDBModelBase,
        serialize_value,
        include_none: bool = True,
    ) -> dict:
        instance_dict = {}

        # Add instance variables
        for attr, value in instance.__dict__.items():
            if str(attr) == "T":
                continue
            # don't get the private properties
            if not str(attr).startswith("_"):
                if value is not None or include_none:
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

                # Skip TypeVar T or instances of DynamoDBModelBase
                if str(name) == "T":
                    continue

                # don't get the private properties
                if not str(name).startswith("_"):
                    value = getattr(instance, name)
                    if value is not None or include_none:
                        instance_dict[name] = serialize_value(value)

        return instance_dict

    @staticmethod
    def _add_indexes(instance: DynamoDBModelBase, instance_dict: dict) -> dict:
        if not issubclass(type(instance), DynamoDBModelBase):
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

        key: DynamoDBIndex
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
