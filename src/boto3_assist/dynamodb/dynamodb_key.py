"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import Callable, Optional, Tuple


class DynamoDBKey:
    """DynamoDB Key"""

    def __init__(
        self,
        attribute_name: Optional[str] = None,
        value: Optional[str | Callable[[], str]] = None,
    ) -> None:
        self.__attribute_name: Optional[str] = attribute_name
        self.__value: Optional[str | Callable[[], str]] = value

    @property
    def attribute_name(self) -> str:
        """Get the name"""
        if self.__attribute_name is None:
            raise ValueError("The Attribute Name is not set")
        return self.__attribute_name

    @attribute_name.setter
    def attribute_name(self, value: str):
        self.__attribute_name = value

    @property
    def value(self) -> Optional[str | Callable[[], str]]:
        """Get the value"""

        if self.__value is None:
            raise ValueError("Value is not set")
        if callable(self.__value):
            return self.__value()
        return self.__value

    @value.setter
    def value(self, value: Optional[str | Callable[[], str]]):
        self.__value = value

    @staticmethod
    def build_key(*key_value_pairs) -> str:
        """
        Static method to build a key based on provided key-value pairs.
        Stops appending if any value is None.
        """
        parts = []
        for key, value in key_value_pairs:
            prefix = f"{key}#" if key else ""
            if value is None:
                parts.append(f"{prefix}")
                break
            else:
                parts.append(f"{prefix}{value}")
        key_str = "#".join(parts)

        return key_str
