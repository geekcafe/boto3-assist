"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Callable, Mapping
from boto_assist.dynamodb.dynamodb_model_base_interfaces import HasKeys


class DynamoDbModelBaseLSI:
    """LSI Indexes"""

    key_configs: Mapping[str, Mapping[str, Callable[[], str]]] | str
    pk: str
    sk: str

    def __init__(self) -> None:
        pass

    @property
    def lsi0_pk(self: HasKeys) -> str | None:
        """Gets the pk for lsi0"""
        return self.get_pk("lsi0")  # pylint: disable=e1101

    @property
    def lsi0_sk(self: HasKeys) -> str | None:
        """Gets the sk for lsi0"""
        return self.get_sk("lsi0")  # pylint: disable=e1101

    @property
    def lsi1_pk(self: HasKeys) -> str | None:
        """Gets the pk for lsi1"""
        return self.get_pk("lsi1")  # pylint: disable=e1101

    @property
    def lsi1_sk(self: HasKeys) -> str | None:
        """Gets the sk for lsi1"""
        return self.get_sk("lsi1")  # pylint: disable=e1101

    @property
    def lsi2_pk(self: HasKeys) -> str | None:
        """Gets the pk for lsi2"""
        return self.get_pk("lsi2")  # pylint: disable=e1101

    @property
    def lsi2_sk(self: HasKeys) -> str | None:
        """Gets the sk for lsi2"""
        return self.get_sk("lsi2")  # pylint: disable=e1101

    @property
    def lsi3_pk(self: HasKeys) -> str | None:
        """Gets the pk for lsi3"""
        return self.get_pk("lsi3")  # pylint: disable=e1101

    @property
    def lsi3_sk(self: HasKeys) -> str | None:
        """Gets the sk for lsi3"""
        return self.get_sk("lsi3")  # pylint: disable=e1101

    @property
    def lsi4_pk(self: HasKeys) -> str | None:
        """Gets the pk for lsi4"""
        return self.get_pk("lsi4")  # pylint: disable=e1101

    @property
    def lsi4_sk(self: HasKeys) -> str | None:
        """Gets the sk for lsi4"""
        return self.get_sk("lsi4")  # pylint: disable=e1101

    @property
    def lsi5_pk(self: HasKeys) -> str | None:
        """Gets the pk for lsi5"""
        return self.get_pk("lsi5")  # pylint: disable=e1101

    @property
    def lsi5_sk(self: HasKeys) -> str | None:
        """Gets the sk for lsi5"""
        return self.get_sk("lsi5")  # pylint: disable=e1101
