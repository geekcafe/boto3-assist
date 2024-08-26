"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

DynamoDB Table Service Example.
Normally I would create the table with CloudFormation, SAM or the CDK

This is just an example of creating it here for demo purposes, as well
as using it in a docker container.
"""

from typing import List
from boto3_assist.dynamodb.dynamodb import DynamoDB


class DynamoDBTableService:
    """
    Dynamo DB Table Service
    Use this to create and manage tables in DynamoDB
    """

    def __init__(self, db: DynamoDB) -> None:
        self.db: DynamoDB = db

    def list_tables(self) -> List[str]:
        """List Tables"""
        tables = self.db.list_tables()

        return tables

    def table_exists(self, table_name: str) -> bool:
        """Check to see if the table exists or not"""
        tables = self.db.list_tables()

        for table in tables:
            if table == table_name:
                return True
        return False

    def create_a_table(self, table_name: str, wait: bool = True):
        """Create a table"""
        # create table is an async call, returns quickly but the table
        # may or may not be ready.
        print(f"creating table: {table_name}")

        if self.table_exists(table_name=table_name):
            return

        response = self.db.dynamodb_resource.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    "AttributeName": "pk",
                    "KeyType": "HASH",
                },
                {
                    "AttributeName": "sk",
                    "KeyType": "RANGE",
                },
            ],
            AttributeDefinitions=self.__create_attribute_defs(),
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=self.__generate_secondary_gsi_indexes(4),
            LocalSecondaryIndexes=[
                self.__generate_secondary_index("lsi0", "pk", "lsi0_sk"),
            ],
        )

        if wait:
            response.meta.client.get_waiter("table_exists").wait(TableName=table_name)

    def __create_attribute_defs(self, gsi_count: int = 4, lsi_count: int = 1) -> dict:
        attribute_defs = []
        attribute_defs.append(self.__create_attribute_def("pk"))
        attribute_defs.append(self.__create_attribute_def("sk"))

        for i in range(gsi_count):
            attribute_defs.append(self.__create_attribute_def(f"gsi{i}_pk"))
            attribute_defs.append(self.__create_attribute_def(f"gsi{i}_sk"))

        for i in range(lsi_count):
            attribute_defs.append(self.__create_attribute_def(f"lsi{i}_sk"))

        return attribute_defs

    def __create_attribute_def(
        self,
        name: str,
        attr_type: str = "S",
    ) -> dict:
        attr_def = {"AttributeName": f"{name}", "AttributeType": f"{attr_type}"}

        return attr_def

    def __generate_secondary_gsi_indexes(self, count: int = 4) -> List[dict]:
        indexes: List[dict] = []
        for i in range(count):
            index = self.__generate_secondary_index(
                f"gsi{i}", f"gsi{i}_pk", f"gsi{i}_sk"
            )
            indexes.append(index)

        return indexes

    def __generate_secondary_index(
        self, index_name: str, pk_name: str, sk_name: str, projection_type: str = "ALL"
    ) -> dict:
        return {
            "IndexName": f"{index_name}",
            "KeySchema": [
                {"AttributeName": f"{pk_name}", "KeyType": "HASH"},
                {"AttributeName": f"{sk_name}", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": f"{projection_type}"},
        }
