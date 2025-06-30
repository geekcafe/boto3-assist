"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Optional, List

from src.boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_re_indexer import DynamoDBReIndexer
from src.boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from src.boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex


class User(DynamoDBModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        DynamoDBModelBase.__init__(self)
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.age: Optional[int] = None
        self.email: Optional[str] = None

        self.__setup_indexes()

    def __setup_indexes(self):
        self.indexes.add_primary(
            index=DynamoDBIndex(
                index_name="primary",
                partition_key=DynamoDBKey(
                    "pk",
                    value=lambda: f"user#{self.id if self.id else ''}",
                ),
                sort_key=DynamoDBKey(
                    "sk",
                    value=lambda: f"user#{self.id if self.id else ''}",
                ),
            ),
        )

        self.indexes.add_secondary(
            index=DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    "gsi0_pk",
                    value="users#",
                ),
                sort_key=DynamoDBKey(
                    "gsi0_sk",
                    value=lambda: f"email#{self.email if self.email else ''}",
                ),
            ),
        )

        self.indexes.add_secondary(
            index=DynamoDBIndex(
                index_name="gsi1",
                partition_key=DynamoDBKey(
                    "gsi1_pk",
                    value="users#",
                ),
                sort_key=DynamoDBKey(
                    "gsi1_sk",
                    value=lambda: (
                        f"lastname#{self.last_name if self.last_name else ''}"
                        + (f"#firstname#{self.first_name}" if self.first_name else "")
                    ),
                ),
            ),
        )

        self.indexes.add_secondary(
            index=DynamoDBIndex(
                index_name="gsi2",
                partition_key=DynamoDBKey(
                    "gsi2_pk",
                    value=self.__get_gsi2,
                ),
                sort_key=DynamoDBKey("gsi2_sk", value=self.__get_gsi2),
            ),
        )

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
        keys: List[DynamoDBKey] = user.list_keys()

        re_indexer: DynamoDBReIndexer = DynamoDBReIndexer("dummy_table")

        dictionary = user.helpers.keys_to_dictionary(keys=keys)

        update_expression = re_indexer.build_update_expression(dictionary)
        expression_attribute_values = re_indexer.build_expression_attribute_values(
            dictionary
        )

        print(update_expression)
        print(expression_attribute_values)

        self.assertIsNotNone(update_expression)
        self.assertIsNotNone(expression_attribute_values)
