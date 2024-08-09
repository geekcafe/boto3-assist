"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Protocol, Optional
from boto3.dynamodb.conditions import (
    And,
    Equals,
    # NotEquals,
    # Or,
    # GreaterThan,
    # GreaterThanEquals,
    # LessThan,
    # LessThanEquals,
    # In,
    # Between,
    # Contains,
    # BeginsWith,
)


class HasKeys(Protocol):
    """Interface for classes that have primary and sort keys"""

    def get_pk(self, index_name: str) -> Optional[str]:
        """Inteface to get_pk"""

    def get_sk(self, index_name: str) -> Optional[str]:
        """Inteface to get_sk"""

    def get_key(self, index_name: str) -> And | Equals:
        """Get the index name and key"""
