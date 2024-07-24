from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeSerializer
import inspect


class DynamoDbSerializer:
    """Library to Serialize object to a DynamoDb Format"""

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

        def serialize_value(value):
            """
            Serialize the value to DynamoDB format.
            """
            if is_primitive(value):
                return serializer.serialize(value)
            elif isinstance(value, list):
                return serializer.serialize([serialize_value(v) for v in value])
            elif isinstance(value, dict):
                return serializer.serialize(
                    {k: serialize_value(v) for k, v in value.items()}
                )
            else:
                return serializer.serialize(
                    DynamoDbSerializer.to_client_dictionary(value)
                )

        def is_primitive(value):
            """
            Check if the value is a primitive data type.
            """
            return isinstance(value, (str, int, float, bool, type(None)))

        instance_dict = {}
        # Add instance variables
        for attr, value in instance.__dict__.items():
            instance_dict[attr] = serialize_value(value)

        # Add properties
        for name, method in inspect.getmembers(
            instance.__class__, predicate=inspect.isdatadescriptor
        ):
            if isinstance(getattr(instance.__class__, name), property):
                instance_dict[name] = serialize_value(getattr(instance, name))

        return {k: v for k, v in instance_dict.items()}

    @staticmethod
    def to_resource_dictionary(instance: object):
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB resource.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB resource.
        """

        def serialize_value(value):
            """
            Serialize the value to a format suitable for DynamoDB resource.
            """
            if is_primitive(value):
                return value
            elif isinstance(value, list):
                return [serialize_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            else:
                return DynamoDbSerializer.to_resource_dictionary(value)

        def is_primitive(value):
            """
            Check if the value is a primitive data type.
            """
            return isinstance(value, (str, int, float, bool, type(None)))

        instance_dict = {}
        # Add instance variables
        for attr, value in instance.__dict__.items():
            instance_dict[attr] = serialize_value(value)

        # Add properties
        for name, method in inspect.getmembers(
            instance.__class__, predicate=inspect.isdatadescriptor
        ):
            if isinstance(getattr(instance.__class__, name), property):
                instance_dict[name] = getattr(instance, name)

        return instance_dict
