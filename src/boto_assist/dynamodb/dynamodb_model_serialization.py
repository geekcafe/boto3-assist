"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime as dt
import decimal
import inspect
import uuid

from boto3.dynamodb.types import TypeSerializer
from boto_assist.utilities.serialization_utility import Serialization


def exclude_from_serialization(method):
    """
    Decorator to mark methods or properties to be excluded from serialization.
    """
    method.exclude_from_serialization = True
    return method


class DynamoDbSerializer:
    """Library to Serialize object to a DynamoDb Format"""

    @staticmethod
    def map(source: dict, target: object) -> object | None:
        """
        Map the source dictionary to the target object.

        Args:
        - source: The dictionary to map from.
        - target: The object to map to.
        """
        return Serialization.map(source, target)

    @staticmethod
    def to_client_dictionary(instance: object):
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
    def to_resource_dictionary(instance: object):
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
