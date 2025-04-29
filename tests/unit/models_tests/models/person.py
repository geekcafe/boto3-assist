
"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import List
from boto3_assist.models.serializable_model import SerializableModel

class Person(SerializableModel):
    """A model that inherits the serializable"""

    def __init__(self, name: str = "", age: int = 0, active: bool = False):
        self.name = name
        self.age = age
        self.active = active
        self.__pets: List[str] = []

    @property
    def pets(self) -> List[str]:
        return self.__pets

    @pets.setter
    def pets(self, value: List[str]):
        self.__pets = value