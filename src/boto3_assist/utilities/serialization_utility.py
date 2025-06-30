"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime as dt
import decimal
import inspect
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, TypeVar
from aws_lambda_powertools import Logger
from boto3_assist.utilities.string_utility import StringUtility

T = TypeVar("T")


logger = Logger()


class SerializableModel:
    """Library to Serialize object to a DynamoDB Format or other dictionary"""

    T = TypeVar("T", bound="SerializableModel")

    def __init__(self):
        pass

    def map(
        self: T,
        source: Dict[str, Any] | "SerializableModel" | None,
        coerce: bool = True,
    ) -> T:
        """
        Map the source dictionary to the target object.

        Args:
        - source: The dictionary to map from.
        - target: The object to map to.
        """
        mapped = Serialization.map(source=source, target=self, coerce=coerce)
        if mapped is None:
            raise ValueError("Unable to map source to target")

        return mapped

    def dict(self) -> Dict[str, Any]:
        """
        Same as .to_dictionary

        """
        return self.to_dictionary()

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary. Same as .dict()
        """
        # return Serialization.convert_object_to_dict(self)
        return Serialization.to_dict(
            instance=self, serialize_fn=lambda x: x, include_none=True
        )

    def to_wide_dictionary(self) -> Dict:
        """
        Dumps an object to dictionary structure
        """

        dump = Serialization.to_wide_dictionary(model=self)

        return dump


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


class JsonConversions:
    """
    Json Conversion Utility
    Used for snake_case to camelCase and vice versa
    """

    @staticmethod
    def _camel_to_snake(value: str) -> str:
        """Converts a camelCase to a snake_case"""
        return StringUtility.camel_to_snake(value)

    @staticmethod
    def _snake_to_camel(value: str) -> str:
        """Converts a value from snake_case to camelCase"""
        return StringUtility.snake_to_camel(value)

    @staticmethod
    def _convert_keys(data, convert_func, deep: bool = True):
        """
        Recursively converts dictionary keys using the provided convert_func.

        Parameters:
        data: The input data (dict, list, or other) to process.
        convert_func: Function to convert the keys (e.g. camel_to_snake or snake_to_camel).
        deep (bool): If True (default), convert keys in all nested dictionaries.
                    If False, only convert the keys at the current level.
        """
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key = convert_func(key)
                # Only process nested structures if deep is True.
                new_dict[new_key] = (
                    JsonConversions._convert_keys(value, convert_func, deep)
                    if deep
                    else value
                )
            return new_dict
        elif isinstance(data, list):
            # For lists, if deep conversion is enabled, process each element.
            return [
                (
                    JsonConversions._convert_keys(item, convert_func, deep)
                    if deep
                    else item
                )
                for item in data
            ]
        else:
            return data

    @staticmethod
    def json_camel_to_snake(data, deep: bool = True):
        """Converts all keys in the JSON structure from camelCase to snake_case.

        Parameters:
        data: The JSON-like structure (dict or list) to process.
        deep (bool): If True, process keys in all nested dictionaries; if False, only at the first level.
        """
        return JsonConversions._convert_keys(
            data, JsonConversions._camel_to_snake, deep
        )

    @staticmethod
    def json_snake_to_camel(data, deep: bool = True):
        """Converts all keys in the JSON structure from snake_case to camelCase.

        Parameters:
        data: The JSON-like structure (dict or list) to process.
        deep (bool): If True, process keys in all nested dictionaries; if False, only at the first level.
        """
        return JsonConversions._convert_keys(
            data, JsonConversions._snake_to_camel, deep
        )

    # # Example usage:
    # if __name__ == "__main__":
    #     sample_json = {
    #         "firstName": "John",
    #         "lastName": "Doe",
    #         "address": {"streetAddress": "21 2nd Street", "city": "New York"},
    #         "phoneNumbers": [
    #             {"phoneType": "home", "phoneNumber": "2125551234"},
    #             {"phoneType": "fax", "phoneNumber": "6465554567"},
    #         ],
    #     }

    #     print("Original JSON:")
    #     print(sample_json)

    #     # Convert from camelCase to snake_case on all levels.
    #     snake_json_deep = json_camel_to_snake(sample_json, deep=True)
    #     print("\nConverted to snake_case (deep conversion):")
    #     print(snake_json_deep)

    #     # Convert from camelCase to snake_case only at the first level.
    #     snake_json_shallow = json_camel_to_snake(sample_json, deep=False)
    #     print("\nConverted to snake_case (first-level only):")
    #     print(snake_json_shallow)

    #     # Convert back from snake_case to camelCase on all levels.
    #     camel_json_deep = json_snake_to_camel(snake_json_deep, deep=True)
    #     print("\nConverted back to camelCase (deep conversion):")
    #     print(camel_json_deep)


class Serialization:
    """
    Serialization Class
    """

    @staticmethod
    def convert_object_to_dict(model: object) -> Dict | List:
        """
        Dumps an object to dictionary structure
        """

        dump = Serialization.to_dict(
            instance=model, serialize_fn=lambda x: x, include_none=True
        )

        return dump

    @staticmethod
    def to_wide_dictionary(model: object) -> Dict:
        """
        Dumps an object to dictionary structure
        """

        dump = Serialization.to_dict(
            instance=model, serialize_fn=lambda x: x, include_none=True
        )

        # have a dictionary now let's flatten out
        flat_dict = {}
        for key, value in dump.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_dict[f"{key}_{sub_key}"] = sub_value
            elif isinstance(value, list):
                for i, sub_value in enumerate(value):
                    sub_dict = Serialization.to_wide_dictionary(sub_value)
                    for sub_key, sub_value in sub_dict.items():
                        flat_dict[f"{key}_{i}_{sub_key}"] = sub_value
            else:
                flat_dict[key] = value

        return flat_dict

    @staticmethod
    def map(source: object, target: T, coerce: bool = True) -> T | None:
        """Map an object from one object to another"""
        source_dict: dict | object
        if isinstance(source, dict):
            source_dict = source
        else:
            source_dict = Serialization.convert_object_to_dict(source)
            if not isinstance(source_dict, dict):
                return None
        return Serialization._load_properties(
            source=source_dict, target=target, coerce=coerce
        )

    @staticmethod
    def to_wide_dictionary_list(
        data: Dict[str, Any] | List[Dict[str, Any]],
        remove_collisions: bool = True,
        raise_error_on_collision: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Converts a dictionary or list of dictionaries to a list of dictionaries.

        :param data: Dictionary or list of dictionaries to be converted
        :param remove_collisions: If True, removes duplicate keys from the dictionaries
        :return: List of dictionaries
        """

        collisions = []

        def recursive_flatten(prefix, obj):
            """
            Recursively flattens a JSON object.

            :param prefix: Current key prefix
            :param obj: Object to flatten
            :return: List of flattened dictionaries
            """
            if isinstance(obj, list):
                result = []
                for _, item in enumerate(obj):
                    x = recursive_flatten("", item)
                    result.extend(x)
                return result
            elif isinstance(obj, dict):
                result = [{}]
                for key, value in obj.items():
                    sub_result = recursive_flatten(
                        f"{prefix}_{key}" if prefix else key, value
                    )
                    new_result = []
                    for entry in result:
                        for sub_entry in sub_result:
                            # remove any collisions

                            for k in entry:
                                if k in sub_entry:
                                    if k not in collisions:
                                        logger.debug(f"Collision detected: {k}")
                                        collisions.append(k)
                            merged = entry.copy()
                            merged.update(sub_entry)
                            new_result.append(merged)
                    result = new_result
                return result
            else:
                return [{prefix: obj}] if prefix else []

        results = recursive_flatten("", data)
        if remove_collisions:
            results = Serialization.remove_collisions(results, collisions)

        if raise_error_on_collision and len(collisions) > 0:
            raise ValueError(f"Duplicate keys detected: {collisions}")

        return results

    @staticmethod
    def remove_collisions(
        data: List[Dict[str, Any]], collisions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Removes collisions from a list of dictionaries.

        :param data: List of dictionaries
        :param collisions: List of collision keys
        :return: List of dictionaries with collisions removed
        """
        for c in collisions:
            for r in data:
                if c in r:
                    del r[c]
        return data

    @staticmethod
    def _load_properties(
        source: dict,
        target: T,
        coerce: bool = True,
    ) -> T | None:
        """
        Converts a source dictionary to a target object.

        Args:
            source (dict): The source dictionary containing properties.
            target (T): The target object to populate.
            coerce (bool): If True, attempts to convert values to the target attribute types. If False, raises an error for type mismatches.

        Returns:
            T | None: The populated target object, or None if an error occurred.
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
            if isinstance(target, dict):
                # our target is a dictionary, so we need to handle this differently
                target[key] = value
            elif Serialization.has_attribute(target, key):
                attr = getattr(target, key)
                expected_type = type(attr)

                try:
                    if isinstance(attr, (int, float, str, bool)):
                        if not isinstance(value, expected_type):
                            if coerce:
                                # Attempt to coerce the value to the expected type
                                try:
                                    if isinstance(value, list) and expected_type is str:
                                        value = "".join(value)

                                    value = expected_type(value)
                                except ValueError as e:
                                    logger.warning(
                                        f"Warning coercing attribute {key} with value {value}: {e}"
                                    )
                                    # TODO: should we set numbers to 0 or a NaN or raise an error

                                    setattr(target, key, value)
                                    # raise ValueError(  # pylint: disable=w0707
                                    #     f"Type mismatch for attribute {key}. Expected {expected_type}, got {type(value)}."
                                    # )
                            else:
                                raise ValueError(
                                    f"Type mismatch for attribute {key}. Expected {expected_type}, got {type(value)}."
                                )
                        setattr(target, key, value)
                    elif isinstance(attr, type(None)):
                        setattr(target, key, value)
                    elif isinstance(attr, list) and isinstance(value, list):
                        attr.clear()
                        attr.extend(value)
                    elif isinstance(attr, dict) and isinstance(value, dict):
                        Serialization._load_properties(value, attr, coerce=coerce)
                    elif hasattr(attr, "__dict__") and isinstance(value, dict):
                        Serialization._load_properties(value, attr, coerce=coerce)
                    else:
                        setattr(target, key, value)
                except ValueError as e:
                    logger.error(
                        f"Error setting attribute {key} with value {value}: {e}"
                    )
                    raise
                except Exception as e:  # pylint: disable=w0718
                    if not Serialization.has_setter(target, key):
                        logger.warning(
                            f"Error warning attempting to set attribute {key} with value {value}: {e}. "
                            "This usually occurs on properties that don't have setters. "
                            "You should add a setter (even with a pass action) for this property or "
                            "decorate it with the @exclude_from_serialization to avoid this warning."
                        )
                    else:
                        raise e

        if hasattr(target, "__actively_serializing_data__"):
            setattr(target, "__actively_serializing_data__", False)

        return target

    @staticmethod
    def has_setter(obj: object, attr_name: str) -> bool:
        """Check if the given attribute has a setter defined."""
        cls = obj.__class__
        if not hasattr(cls, attr_name):
            return False
        attr = getattr(cls, attr_name, None)
        return isinstance(attr, property) and attr.fset is not None

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
                "e.g. if not self.some_property and not self.__actively_serializing_data__:\n"
                '    raise ValueError("some_property must be set")\n\n'
                "This procedure will update the property from False to True while serializing, "
                "then back to False once serialization is complete. "
            ) from e

    @staticmethod
    def to_dict(
        instance: SerializableModel | dict,
        serialize_fn,
        include_none: bool = True,
    ) -> Dict[str, Any]:
        """To Dict / Dictionary"""

        if instance is None:
            return {}

        if isinstance(instance, dict):
            return instance

        def is_primitive(value):
            """Check if the value is a primitive data type."""
            return isinstance(value, (str, int, bool, type(None)))

        def serialize_value(value):
            """Serialize the value using the provided function."""

            if isinstance(value, SerializableModel):
                return serialize_fn(
                    Serialization.to_dict(
                        instance=value,
                        serialize_fn=lambda x: x,
                        include_none=include_none,
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
                    Serialization.to_dict(
                        value,
                        serialize_fn,
                        include_none=include_none,
                    )
                )

        instance_dict = Serialization._add_properties(
            instance, serialize_value, include_none=include_none
        )

        return instance_dict

    @staticmethod
    def _add_properties(
        instance: SerializableModel,
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
