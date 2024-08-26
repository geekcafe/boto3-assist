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

        logger.info(f"AplosJsonEncoder failing back: ${type(o)}")

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
    @tracer.capture_method
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
    @tracer.capture_method
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

        for key, value in source.items():
            if hasattr(target, key):
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
        return target
