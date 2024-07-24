"""
DynamoDb Table Service Example.
Normally I would create the table with CloudFormation, SAM or the CDK

This is just an example of creating it here for demo purposes, as well
as using it in a docker container.
"""

from gc_boto3_lib.dynamodb.dynamodb import DynamoDb


class DynamoDbTableService:
    def __init__(self, db: DynamoDb) -> None:
        self.db: DynamoDb = db

    def list_tables(self):
        tables = self.db.list_tables()
        if len(tables) > 0:
            print("The following Tables were found.")
            for table in tables:
                print(f"\t{table.name}")
        else:
            print("no tables were found")

    def table_exists(self, table_name: str) -> bool:
        tables = self.db.list_tables()

        for table in tables:
            if table.name == table_name:
                return True
        return False

    def create_a_table(self, table_name: str, wait: bool = True):
        # create table is an async call, returns quickly but the table
        # may or may not be ready.
        print(f"creating table: {table_name}")
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
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {
                    "AttributeName": "gsi0_pk",
                    "AttributeType": "S",
                },  # GSI0 partition key
                {"AttributeName": "gsi0_sk", "AttributeType": "S"},  # GSI0 sort key
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi0",
                    "KeySchema": [
                        {
                            "AttributeName": "gsi0_pk",
                            "KeyType": "HASH",
                        },
                        {
                            "AttributeName": "gsi0_sk",
                            "KeyType": "RANGE",
                        },
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"  # This can be KEYS_ONLY, INCLUDE, or ALL
                    },
                    # ProvisionedThroughput={  # Not needed when using PAY_PER_REQUEST
                    #     "ReadCapacityUnits": 5,
                    #     "WriteCapacityUnits": 5,
                    # },
                }
            ],
        )

        if wait:
            response.meta.client.get_waiter("table_exists").wait(TableName=table_name)
