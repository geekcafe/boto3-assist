"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Dict, Any
from boto3_assist.models.serializable_model import SerializableModel


class User(SerializableModel):
    """A model that inherits the serializable"""

    def __init__(self):
        self.__first_name: str | None = None
        self.__last_name: str | None = None
        self.__email: str | None = None
        self.__meta_data: Dict[str, Any] = {}
        self.settings: Dict[str, Any] = {}

    @property
    def first_name(self) -> str | None:
        """The first name of the user"""
        if self.__first_name is None:
            return None
        return self.__first_name

    @first_name.setter
    def first_name(self, value: str | None):
        self.__first_name = value

    @property
    def last_name(self) -> str | None:
        """The last name of the user"""
        if self.__last_name is None:
            return None
        return self.__last_name

    @last_name.setter
    def last_name(self, value: str | None):
        self.__last_name = value

    @property
    def email(self) -> str | None:
        """The email address of the user"""
        if self.__email is None:
            return None
        return self.__email

    @email.setter
    def email(self, value: str | None):
        self.__email = value

    @property
    def meta_data(self) -> Dict[str, Any]:
        """The last name of the user"""
        if self.__meta_data is None:
            return {}
        return self.__meta_data

    @meta_data.setter
    def meta_data(self, value: Dict[str, Any] | None):
        if value is None:
            self.__meta_data = {}
            return
        self.__meta_data = value
