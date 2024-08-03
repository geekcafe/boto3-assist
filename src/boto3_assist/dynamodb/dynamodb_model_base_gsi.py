"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Tuple, Callable, Mapping
from boto3.dynamodb.conditions import Key, And
from boto3_assist.dynamodb.dynamodb_model_base_interfaces import HasKeys


class DynamoDbModelBaseGSI:
    """GSI Indexes"""

    # type hinting
    key_configs: Mapping[str, Mapping[str, Callable[[], str]]] | str
    pk: str
    sk: str

    def __init__(self) -> None:
        pass

    def get_gsi_key(self: HasKeys, index_name: str) -> Tuple[str, And]:
        """Get the GSI index name and key"""

        pk_value = self.get_pk(index_name)  # pylint: disable=e1101
        sk_value = self.get_sk(index_name)  # pylint: disable=e1101

        key = Key(f"{index_name}_pk").eq(pk_value) & Key(
            f"{index_name}_sk"
        ).begins_with(sk_value)

        return index_name, key

    def get_key(self, index_name: str, key_name: str | None) -> str | None:
        """Get the partition key for a given GSI index"""
        keys = self.key_configs
        config: Mapping[str, Callable[[], str]] | str | None = None

        if isinstance(keys, str):
            config = keys
        elif isinstance(keys, dict):
            config = keys.get(index_name)

        if not config:
            return None
        value: str | Callable[[], str] | None = None

        if isinstance(config, str):
            value = config
        elif isinstance(config, dict):
            if key_name is not None:
                value = config[key_name]

        if callable(value):
            return value()
        return value

    ##################################################################################
    # currently there can be up to 20 GSI's 1-20 or 0-19

    @property
    def gsi0_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI0"""
        return self.get_pk("gsi0")  # pylint: disable=e1101

    @property
    def gsi0_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI0"""
        return self.get_sk("gsi0")  # pylint: disable=e1101

    @property
    def gsi1_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI1"""
        return self.get_pk("gsi1")  # pylint: disable=e1101

    @property
    def gsi1_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI1"""
        return self.get_sk("gsi1")  # pylint: disable=e1101

    @property
    def gsi2_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI2"""
        return self.get_pk("gsi2")  # pylint: disable=e1101

    @property
    def gsi2_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI2"""
        return self.get_sk("gsi2")  # pylint: disable=e1101

    @property
    def gsi3_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI3"""
        return self.get_pk("gsi3")  # pylint: disable=e1101

    @property
    def gsi3_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI3"""
        return self.get_sk("gsi3")  # pylint: disable=e1101

    @property
    def gsi4_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI4"""
        return self.get_pk("gsi4")  # pylint: disable=e1101

    @property
    def gsi4_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI4"""
        return self.get_sk("gsi4")  # pylint: disable=e1101

    @property
    def gsi5_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI5"""
        return self.get_pk("gsi5")  # pylint: disable=e1101

    @property
    def gsi5_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI5"""
        return self.get_sk("gsi5")  # pylint: disable=e1101

    @property
    def gsi6_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI6"""
        return self.get_pk("gsi6")  # pylint: disable=e1101

    @property
    def gsi6_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI6"""
        return self.get_sk("gsi6")  # pylint: disable=e1101

    @property
    def gsi7_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI7"""
        return self.get_pk("gsi7")  # pylint: disable=e1101

    @property
    def gsi7_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI7"""
        return self.get_sk("gsi7")  # pylint: disable=e1101

    @property
    def gsi8_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI8"""
        return self.get_pk("gsi8")  # pylint: disable=e1101

    @property
    def gsi8_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI8"""
        return self.get_sk("gsi8")  # pylint: disable=e1101

    @property
    def gsi9_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI9"""
        return self.get_pk("gsi9")  # pylint: disable=e1101

    @property
    def gsi9_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI9"""
        return self.get_sk("gsi9")  # pylint: disable=e1101

    @property
    def gsi10_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI10"""
        return self.get_pk("gsi10")  # pylint: disable=e1101

    @property
    def gsi10_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI10"""
        return self.get_sk("gsi10")  # pylint: disable=e1101

    @property
    def gsi11_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI11"""
        return self.get_pk("gsi11")  # pylint: disable=e1101

    @property
    def gsi11_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI11"""
        return self.get_sk("gsi11")  # pylint: disable=e1101

    @property
    def gsi12_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI12"""
        return self.get_pk("gsi12")  # pylint: disable=e1101

    @property
    def gsi12_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI12"""
        return self.get_sk("gsi12")  # pylint: disable=e1101

    @property
    def gsi13_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI13"""
        return self.get_pk("gsi13")  # pylint: disable=e1101

    @property
    def gsi13_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI13"""
        return self.get_sk("gsi13")  # pylint: disable=e1101

    @property
    def gsi14_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI14"""
        return self.get_pk("gsi14")  # pylint: disable=e1101

    @property
    def gsi14_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI14"""
        return self.get_sk("gsi14")  # pylint: disable=e1101

    @property
    def gsi15_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI15"""
        return self.get_pk("gsi15")  # pylint: disable=e1101

    @property
    def gsi15_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI15"""
        return self.get_sk("gsi15")  # pylint: disable=e1101

    @property
    def gsi16_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI16"""
        return self.get_pk("gsi16")  # pylint: disable=e1101

    @property
    def gsi16_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI16"""
        return self.get_sk("gsi16")  # pylint: disable=e1101

    @property
    def gsi17_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI17"""
        return self.get_pk("gsi17")  # pylint: disable=e1101

    @property
    def gsi17_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI17"""
        return self.get_sk("gsi17")  # pylint: disable=e1101

    @property
    def gsi18_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI18"""
        return self.get_pk("gsi18")  # pylint: disable=e1101

    @property
    def gsi18_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI18"""
        return self.get_sk("gsi18")  # pylint: disable=e1101

    @property
    def gsi19_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI19"""
        return self.get_pk("gsi19")  # pylint: disable=e1101

    @property
    def gsi19_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI19"""
        return self.get_sk("gsi19")  # pylint: disable=e1101

    @property
    def gsi20_pk(self: HasKeys) -> str | None:
        """Gets the pk for GSI20"""
        return self.get_pk("gsi20")  # pylint: disable=e1101

    @property
    def gsi20_sk(self: HasKeys) -> str | None:
        """Gets the sk for GSI20"""
        return self.get_sk("gsi20")  # pylint: disable=e1101

    # key's and index names
    def gsi0(self) -> tuple[str, And]:
        """
        Get the GSI0 index name and key.  This matches the pattern
        for gsi0 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi0")

    def gsi1(self) -> tuple[str, And]:
        """
        Get the GSI1 index name and key.  This matches the pattern
        for gsi1 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi1")

    def gsi2(self) -> tuple[str, And]:
        """
        Get the GSI2 index name and key.  This matches the pattern
        for gsi2 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi2")

    def gsi3(self) -> tuple[str, And]:
        """
        Get the GSI3 index name and key.  This matches the pattern
        for gsi3 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi3")

    def gsi4(self) -> tuple[str, And]:
        """
        Get the GSI4 index name and key.  This matches the pattern
        for gsi4 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi4")

    def gsi5(self) -> tuple[str, And]:
        """
        Get the GSI5 index name and key.  This matches the pattern
        for gsi5 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi5")

    def gsi6(self) -> tuple[str, And]:
        """
        Get the GSI6 index name and key.  This matches the pattern
        for gsi6 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi6")

    def gsi7(self) -> tuple[str, And]:
        """
        Get the GSI7 index name and key.  This matches the pattern
        for gsi7 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi7")

    def gsi8(self) -> tuple[str, And]:
        """
        Get the GSI8 index name and key.  This matches the pattern
        for gsi8 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi8")

    def gsi9(self) -> tuple[str, And]:
        """
        Get the GSI9 index name and key.  This matches the pattern
        for gsi9 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi9")

    def gsi10(self) -> tuple[str, And]:
        """
        Get the GSI10 index name and key.  This matches the pattern
        for gsi10 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi10")

    def gsi11(self) -> tuple[str, And]:
        """
        Get the GSI11 index name and key.  This matches the pattern
        for gsi11 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi11")

    def gsi12(self) -> tuple[str, And]:
        """
        Get the GSI12 index name and key.  This matches the pattern
        for gsi12 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi12")

    def gsi13(self) -> tuple[str, And]:
        """
        Get the GSI13 index name and key.  This matches the pattern
        for gsi13 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi13")

    def gsi14(self) -> tuple[str, And]:
        """
        Get the GSI14 index name and key.  This matches the pattern
        for gsi14 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi14")

    def gsi15(self) -> tuple[str, And]:
        """
        Get the GSI15 index name and key.  This matches the pattern
        for gsi15 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi15")

    def gsi16(self) -> tuple[str, And]:
        """
        Get the GSI16 index name and key.  This matches the pattern
        for gsi16 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi16")

    def gsi17(self) -> tuple[str, And]:
        """
        Get the GSI17 index name and key.  This matches the pattern
        for gsi17 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi17")

    def gsi18(self) -> tuple[str, And]:
        """
        Get the GSI18 index name and key.  This matches the pattern
        for gsi18 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi18")

    def gsi19(self) -> tuple[str, And]:
        """
        Get the GSI19 index name and key.  This matches the pattern
        for gsi19 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi19")

    def gsi20(self) -> tuple[str, And]:
        """
        Get the GSI20 index name and key.  This matches the pattern
        for gsi20 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        return self.get_gsi_key("gsi20")
