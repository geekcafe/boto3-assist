"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Protocol, Optional


class HasKeys(Protocol):
    """Interface for classes that have primary and sort keys"""

    def get_pk(self, index_name: str) -> Optional[str]:
        """Inteface to get_pk"""

    def get_sk(self, index_name: str) -> Optional[str]:
        """Inteface to get_sk"""
