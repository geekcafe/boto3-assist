"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.models.serializable_model import SerializableModel


class CognitoUser(SerializableModel):
    """A generic way to represent a cognito user"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=w0622
    ) -> None:
        super().__init__()
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.email: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.status: Optional[str] = None
        self.company_name: Optional[str] = None
        self.roles: list[str] = []
        self.cognito_user_name: str | None = None
