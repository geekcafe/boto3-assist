"""Serialization Utility"""

from typing import Dict, List
import jsons
from aws_lambda_powertools import Logger, Tracer

tracer = Tracer()
logger = Logger()


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
    def map(source: object, target: object) -> object | None:
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
    def load_properties(source: dict, target: object) -> str | object | None:
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
