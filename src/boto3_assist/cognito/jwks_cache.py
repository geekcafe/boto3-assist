"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""


class JwksCache:
    """A JWT Caching object"""

    def __init__(self):
        self.__cache = {}

    @property
    def cache(self):
        """The Cache"""
        return self.__cache

    @cache.setter
    def cache(self, value):
        self.__cache = value
