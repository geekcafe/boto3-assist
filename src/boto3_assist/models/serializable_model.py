"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from __future__ import annotations
from typing import TypeVar, Dict, Any
from boto3_assist.utilities.serialization_utility import Serialization


class SerializableModel:
    """Library to Serialize object to a DynamoDB Format"""

    T = TypeVar("T", bound="SerializableModel")

    def __init__(self):
        pass

    def map(
        self: T, source: Dict[str, Any] | SerializableModel | None, coerce: bool = True
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

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary.
        """
        return Serialization.convert_object_to_dict(self)
