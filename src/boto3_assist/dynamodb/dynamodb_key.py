"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import Callable, Optional, Mapping


class DynamoDbKey:
    """DynamoDb Key"""

    def __init__(
        self,
        attribute_name: Optional[str] = None,
        value: Optional[Mapping[str, Callable[[], str]]] = None,
    ) -> None:
        self.__attribute_name: Optional[str] = attribute_name
        self.__value: Optional[Mapping[str, Callable[[], str]]] = value

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
    def value(self) -> Mapping[str, Callable[[], str]]:
        """Get the value"""
        if self.__value is None:
            raise ValueError("Value is not set")
        if callable(self.__value):
            return self.__value()
        return self.__value

    @value.setter
    def value(self, value: Mapping[str, Callable[[], str]]):
        self.__value = value
