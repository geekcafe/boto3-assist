"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import datetime
from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class User(DynamoDBModelBase):
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
        # user id
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        self.indexes.add_primary(primary)

        # find all users by email address
        gsi0: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi0",
            partition_key=DynamoDBKey(attribute_name="gsi0_pk", value="users#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi0_sk",
                value=lambda: DynamoDBKey.build_key(("user", self.id)),
            ),
        )
        self.indexes.add_secondary(gsi0)

        gsi1: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi1",
            partition_key=DynamoDBKey(attribute_name="gsi1_pk", value="users#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi1_sk",
                value=self.__get_gsi1,
            ),
        )
        self.indexes.add_secondary(gsi1)

        # users search by last name
        gsi2: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi2",
            partition_key=DynamoDBKey(attribute_name="gsi2_pk", value="users#"),
            sort_key=DynamoDBKey(attribute_name="gsi2_sk", value=self.__get_gsi2),
        )
        self.indexes.add_secondary(gsi2)

        # users by status and email
        gsi3: DynamoDBIndex = DynamoDBIndex(
            index_name="gsi3",
            partition_key=DynamoDBKey(attribute_name="gsi3_pk", value="users#"),
            sort_key=DynamoDBKey(
                attribute_name="gsi3_sk",
                value=lambda: (
                    f"status#{self.status if self.status else ''}"
                    f"#email#{self.email if self.email else ''}"
                ),
            ),
        )
        self.indexes.add_secondary(gsi3)

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
