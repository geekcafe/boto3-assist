"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, Protocol

from boto3.dynamodb.conditions import (  # NotEquals,; Or,; GreaterThan,; GreaterThanEquals,; LessThan,; LessThanEquals,; In,; Between,; Contains,; BeginsWith,
    And,
    Equals,
)


class HasKeys(Protocol):
    """Interface for classes that have primary and sort keys"""

    def get_pk(self, index_name: str) -> Optional[str]:
        """Interface to get_pk"""

    def get_sk(self, index_name: str) -> Optional[str]:
        """Interface to get_sk"""

    def get_key(self, index_name: str) -> And | Equals:
        """Get the index name and key"""
