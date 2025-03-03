"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import List


class DictionaryUtilitiy:
    """
    A class to provide utility methods for working with dictionaries.
    """

    @staticmethod
    def find_dict_by_name(
        dict_list: List[dict], key_field: str, name: str
    ) -> List[dict] | dict | str:
        """
        Searches for dictionaries in a list where the key 'name' matches the specified value.

        Args:
        dict_list (list): A list of dictionaries to search through.
        key_field (str): The key to search for in each dictionary.
        name (str): The value to search for in the 'key_field' key.

        Returns:
        list: A list of dictionaries where the 'key_field' key matches the specified value.
        """
        # List comprehension to filter dictionaries that have the 'name' key equal to the specified name

        return [d for d in dict_list if d.get(key_field) == name]
