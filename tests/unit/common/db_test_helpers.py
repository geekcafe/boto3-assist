from mypy_boto3_dynamodb import DynamoDBClient


class DbTestHelper:

    def helper_create_mock_table(self, table_name: str, client: DynamoDBClient) -> None:
        """
        Create a mock DynamoDB table.
        """

        gs_indexes = []

        for i in range(1, 11):
            gs_indexes.append(
                {
                    "IndexName": f"gsi{i}",
                    "KeySchema": [
                        {
                            "AttributeName": f"gsi{i}_pk",
                            "KeyType": "HASH",
                        },  # Partition key for GSI
                        {
                            "AttributeName": f"gsi{i}_sk",
                            "KeyType": "RANGE",
                        },  # Sort key for GSI
                    ],
                    "Projection": {"ProjectionType": "ALL"},  # Project all attributes
                }
            )

        attributes = [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ]
        for i in range(1, 11):
            attributes.append({"AttributeName": f"gsi{i}_pk", "AttributeType": "S"})
            attributes.append({"AttributeName": f"gsi{i}_sk", "AttributeType": "S"})

        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "sk", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=attributes,
            GlobalSecondaryIndexes=gs_indexes,
            BillingMode="PAY_PER_REQUEST",
        )

        print(response)
