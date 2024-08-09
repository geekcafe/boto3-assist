"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Optional, List

from src.boto3_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase, DynamoDbKey
from src.boto3_assist.dynamodb.dynamodb_reindexer import DynamoDbReindexer


class User(DynamoDbModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        DynamoDbModelBase.__init__(self)
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.age: Optional[int] = None
        self.email: Optional[str] = None

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
                        "value": lambda: (
                            f"lastname#{self.last_name if self.last_name else ''}"
                            + (
                                f"#firstname#{self.first_name}"
                                if self.first_name
                                else ""
                            )
                        ),
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
                        "results": {
                            "firstname#{self.first_name}": "with no last name",
                            "firstname#{self.first_name}#lastname#{self.lastname}": "with a last name",
                        },
                    },
                }
            },
        ]

        self.key_configs = key_configs
        self.projection_expression = (
            "id,first_name,last_name,email,tenant_id,#type,#status,"
            "company_name,authorization,modified_datetime_utc"
        )
        self.projection_expression_attribute_names = {
            "#status": "status",
            "#type": "type",
        }

    def __get_gsi2(self) -> str:
        index = f"firstname#{self.first_name if self.first_name else ''}"
        if self.last_name:
            index = f"{index}#lastname#{self.last_name}"

        return index


class ReindexTest(unittest.TestCase):
    "Serialization Tests"

    def test_key_dictionary_expressions(self):
        """Test Listing Keys"""
        # Arrange
        data = {
            "id": "123456",
            "first_name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        # Act
        user: User = User().map(data)
        keys: List[DynamoDbKey] = user.list_keys()

        reindexer: DynamoDbReindexer = DynamoDbReindexer("dummy_table")

        dictionary = user.helpers.keys_to_dictionary(keys=keys)

        update_expression = reindexer.build_update_expression(dictionary)
        expression_attribute_values = reindexer.build_expression_attribute_values(
            dictionary
        )

        print(update_expression)
        print(expression_attribute_values)

        self.assertIsNotNone(update_expression)
        self.assertIsNotNone(expression_attribute_values)
