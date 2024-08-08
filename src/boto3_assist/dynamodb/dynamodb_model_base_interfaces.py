"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Protocol, Optional, Tuple
from boto3.dynamodb.conditions import And


class HasKeys(Protocol):
    """Interface for classes that have primary and sort keys"""

    def get_pk(self, index_name: str) -> Optional[str]:
        """Inteface to get_pk"""

    def get_sk(self, index_name: str) -> Optional[str]:
        """Inteface to get_sk"""

    def get_key_data(self, index_name: str) -> Tuple[str, And]:
        """Get the index name and key"""
