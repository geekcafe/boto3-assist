"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase


class UserDbModel(DynamoDbModelBase):
    """Database Model for the User Entity"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=w0622
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.id: Optional[str] = id
        self.first_name: Optional[str] = first_name
        self.last_name: Optional[str] = last_name
        self.email: Optional[str] = email
        self.modified_datetime_utc: str = str(datetime.datetime.now(datetime.UTC))
        self.status: Optional[str] = None
        self.__setup_indexes()

    def __setup_indexes(self):
        key_configs = {
            "pk_sk": {
                "pk": lambda: f"user#{self.id if self.id else ''}",
                "sk": lambda: f"user#{self.id if self.id else ''}",
            },
            "gsi0": {
                "pk": "users#",
                "sk": lambda: f"email#{self.email if self.email else ''}",
            },
            "gsi1": {
                "pk": "users#",
                "sk": lambda: f"lastname#{self.last_name if self.last_name else ''}",
            },
            "gsi2": {
                "pk": "users#",
                "sk": lambda: f"lastname#{self.first_name if self.first_name else ''}",
            },
            "gsi3": {
                "pk": "users#",
                "sk": lambda: (
                    f"status#{self.status if self.status else ''}"
                    f"#email#{self.email if self.email else ''}"
                ),
            },
        }

        self.key_configs = key_configs
        self.projection_expression = (
            "id,first_name,last_name,email,modified_datetime_utc,#status"
        )
        self.projection_expression_attribute_names = {"#status": "status"}
