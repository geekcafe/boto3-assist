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
            if is_primitive(value):
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
            # don't ge the private properties
            if not str(attr).startswith("_"):
                if value is not None:
                    instance_dict[attr] = serialize_value(value)

        # Add properties
        for name, _ in inspect.getmembers(
            instance.__class__, predicate=inspect.isdatadescriptor
        ):
            if isinstance(getattr(instance.__class__, name), property):
                # don't ge the private properties
                if not str(name).startswith("_"):
                    value = getattr(instance, name)
                    if value is not None:
                        instance_dict[name] = serialize_value(value)

        return instance_dict
