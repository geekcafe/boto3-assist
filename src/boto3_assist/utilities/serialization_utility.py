"""Serialization Utility"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, TypeVar
import json
import jsons
from aws_lambda_powertools import Logger, Tracer

T = TypeVar("T")

tracer = Tracer()
logger = Logger()


class JsonEncoder(json.JSONEncoder):
    """
    This class is used to serialize python generics which implement a __json_encode__ method
    and where the recipient does not require type hinting for deserialization.
    If type hinting is required, use GenericJsonEncoder
    """

    def default(self, o):
        # First, check if the object has a custom encoding method
        if hasattr(o, "__json_encode__"):
            return o.__json_encode__()

        # check for dictionary
        if hasattr(o, "__dict__"):
            return {k: v for k, v in o.__dict__.items() if not k.startswith("_")}

        # Handling datetime.datetime objects specifically
        elif isinstance(o, datetime):
            return o.isoformat()
        # handle decimal wrappers
        elif isinstance(o, Decimal):
            return float(o)

        logger.info(f"JsonEncoder failing back: ${type(o)}")

        # Fallback to the base class implementation for other types

        try:
            return super().default(o)
        except TypeError:
            # If an object does not have a __dict__ attribute, you might want to handle it differently.
            # For example, you could choose to return str(o) or implement other specific cases.
            return str(
                o
            )  # Or any other way you wish to serialize objects without __dict__


class Serialization:
    """
    Serliaztion Class
    """

    @staticmethod
    def convert_object_to_dict(model: object) -> Dict | List:
        """
        Dumps an object to dictionary structure
        """
        dump = jsons.dump(model, strip_privates=True)
        if isinstance(dump, dict) or isinstance(dump, List):
            return dump

        raise ValueError("Unable to convert object to dictionary")

    @staticmethod
    def map(source: object, target: T) -> T | None:
        """Map an object from one object to another"""
        source_dict: dict | object
        if isinstance(source, dict):
            source_dict = source
        else:
            source_dict = Serialization.convert_object_to_dict(source)
            if not isinstance(source_dict, dict):
                return None
        return Serialization.load_properties(source_dict, target=target)

    @staticmethod
    def load_properties(source: dict, target: T) -> T | None:
        """
        Converts a source to an object
        """
        # Ensure target is an instance of the class
        if isinstance(target, type):
            target = target()

        # Convert source to a dictionary if it has a __dict__ attribute
        if hasattr(source, "__dict__"):
            source = source.__dict__

        if hasattr(target, "__actively_serializing_data__"):
            setattr(target, "__actively_serializing_data__", True)

        for key, value in source.items():
            if Serialization.has_attribute(target, key):  # hasattr(target, key):
                attr = getattr(target, key)
                if isinstance(attr, (int, float, str, bool, type(None))):
                    try:
                        setattr(target, key, value)
                    except Exception as e:  # pylint: disable=w0718
                        logger.error(
                            f"Error setting attribute {key} with value {value}: {e}. "
                            "This usually occurs on properties that don't have setters. "
                            "You can add a setter (even with a pass action) for this property, "
                            "decorate it with the @exclude_from_serialization "
                            "or ignore this error. "
                        )
                elif isinstance(attr, list) and isinstance(value, list):
                    attr.clear()
                    attr.extend(value)
                elif isinstance(attr, dict) and isinstance(value, dict):
                    Serialization.load_properties(value, attr)
                elif hasattr(attr, "__dict__") and isinstance(value, dict):
                    Serialization.load_properties(value, attr)
                else:
                    setattr(target, key, value)

        if hasattr(target, "__actively_serializing_data__"):
            setattr(target, "__actively_serializing_data__", False)

        return target

    @staticmethod
    def has_attribute(obj: object, attribute_name: str) -> bool:
        """Check if an object has an attribute"""
        try:
            return hasattr(obj, attribute_name)
        except AttributeError:
            return False
        except Exception as e:  # pylint: disable=w0718
            raise RuntimeError(
                "Failed to serialize the object. \n"
                "You may have some validation that is preventing this routine "
                "from completing. Such as a None checker on a getter. \n\n"
                "To work around this create a boolean (bool) property named __actively_serializing_data__. \n"
                "e.g. self.__actively_serializing_data__: bool = False\n\n"
                "Only issue/raise your exception if __actively_serializing_data__ is not True. \n\n"
                "e.g. if not self.some_propert and not self.__actively_serializing_data__:\n"
                '    raise ValueError("some_property must be set")\n\n'
                "This procedure will update the property from False to True while serializing, "
                "then back to False once serialization is complete. "
            ) from e
