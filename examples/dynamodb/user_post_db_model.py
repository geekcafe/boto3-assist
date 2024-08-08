"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional

from boto3_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase


class UserPostDbModel(DynamoDbModelBase):
    """Database Model for the User Posts Entity"""

    def __init__(
        self,
        slug: Optional[str] = None,  # pylint: disable=w0622
        title: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.slug: Optional[str] = slug
        self.user_id: Optional[str] = user_id
        self.title: Optional[str] = title

        self.data: Optional[str] = None
        self.status: Optional[str] = None
        self.type: Optional[str] = None
        self.timestamp: str = str(datetime.datetime.now(datetime.UTC).timestamp())
        self.modified_datetime_utc: str = str(datetime.datetime.now(datetime.UTC))
        self.__setup_indexes()

    def __setup_indexes(self):
        key_configs = [
            {
                "primary_key": {
                    "pk": {
                        "attribute": "pk",
                        "value": lambda: f"post#{self.slug if self.slug else ''}",
                    },
                    "sk": {
                        "attribute": "sk",
                        "value": lambda: f"post#{self.slug if self.slug else ''}",
                    },
                }
            },
            {
                "gsi0": {
                    "pk": {
                        "attribute": "gsi0_pk",
                        "value": "posts#",
                    },
                    "sk": {
                        "attribute": "gsi0_sk",
                        "value": lambda: f"title#{self.title if self.title else ''}",
                    },
                }
            },
            {
                "gsi1": {
                    "pk": {
                        "attribute": "gsi1_pk",
                        "value": "posts#",
                    },
                    "sk": {
                        "attribute": "gsi1_sk",
                        "value": lambda: f"ts#{self.timestamp if self.timestamp else ''}",
                    },
                }
            },
            {
                "gsi2": {
                    "pk": {
                        "attribute": "gsi2_pk",
                        "value": "posts#",
                    },
                    "sk": {
                        "attribute": "gsi2_sk",
                        "value": lambda: f"slug#{self.slug if self.slug else ''}",
                    },
                }
            },
        ]

        self.key_configs = key_configs
        self.projection_expression = (
            "id,user_id,title,data,timestamp,modified_datetime_utc,#status,#type"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type",
        }
