"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase


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
        key_configs = [
            {
                "primary_key": {
                    "pk": {
                        "attribute": "pk",
                        "value": lambda: f"user#{self.id if self.id else ''}",
                    },
                    "sk": {
                        "attribute": "sk",
                        "value": lambda: f"user#{self.id if self.id else ''}",
                    },
                }
            },
            {
                "gsi0": {
                    "pk": {
                        "attribute": "gsi0_pk",
                        "value": "users#",
                    },
                    "sk": {
                        "attribute": "gsi0_sk",
                        "value": lambda: f"email#{self.email if self.email else ''}",
                    },
                }
            },
            {
                "gsi1": {
                    "pk": {"attribute": "gsi1_pk", "value": "users#"},
                    "sk": {
                        "attribute": "gsi1_sk",
                        "value": self.__get_gsi1,
                        "meta": {
                            "lastname#{self.last_name}": "with no first name",
                            "lastname#{self.last_name}#firstname#{self.first_name}": "with a first name",
                        },
                    },
                }
            },
            {
                "gsi2": {
                    "pk": {
                        "attribute": "gsi2_pk",
                        "value": "users#",
                    },
                    "sk": {
                        "attribute": "gsi2_sk",
                        "value": self.__get_gsi2,
                        "meta": {
                            "firstname#{self.first_name}": "with no last name",
                            "firstname#{self.first_name}#lastname#{self.last_name}": "with a last name",
                        },
                    },
                }
            },
            {
                "gsi3": {
                    "pk": {
                        "attribute": "gsi3_pk",
                        "value": "users#",
                    },
                    "sk": {
                        "attribute": "gsi3_sk",
                        "value": lambda: (
                            f"status#{self.status if self.status else ''}"
                            f"#email#{self.email if self.email else ''}"
                        ),
                    },
                }
            },
        ]

        self.key_configs = key_configs
        self.projection_expression = (
            "id,first_name,last_name,email,#type,#status,"
            "company_name,modified_datetime_utc"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type",
        }

    def __get_gsi1(self) -> str:
        index = f"lastname#{self.last_name if self.last_name else ''}"
        if self.last_name:
            index = f"{index}#firstname#{self.first_name}"

        return index

    def __get_gsi2(self) -> str:
        index = f"firstname#{self.first_name if self.first_name else ''}"
        if self.last_name:
            index = f"{index}#lastname#{self.last_name}"

        return index
