"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from urllib.parse import unquote
from typing import Dict, Any


class HttpUtility:
    """HTTP Utilities"""

    @staticmethod
    def get_query_params(query_string: str) -> Dict[str, Any]:
        """
        Get the query parameters from a query string
        returns a dictionary of key value pairs
        """
        if not query_string:
            return {}

        params = {}
        if query_string:
            for param in query_string.split("&"):
                key, value = param.split("=")
                params[key] = unquote(value)
        return params

    @staticmethod
    def get_query_param(query_string: str | None, key: str) -> str | None:
        """Get a query parameter from a query string"""

        if not query_string:
            return None
        params = HttpUtility.get_query_params(query_string)
        if key in params:
            return params[key]
        return None

    @staticmethod
    def decode_url(url: str):
        """Decodes a URL"""

        # sometimes a paylaod will have a + added instead of the space
        # or the space encoded value of %2B
        url = url.replace("+", " ")
        return unquote(url)
