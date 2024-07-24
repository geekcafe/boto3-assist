from gc_boto3_lib.dynamodb.dynamodb_model_serialization import DynamoDbSerializer


class DynamoDbModelBase:
    def __init__(self) -> None:
        pass

    def to_client_dictionary(self):
        """
        Convert the instance to a dictionary suitable for DynamoDB client.
        """
        return DynamoDbSerializer.to_client_dictionary(self)

    def to_resource_dictionary(self):
        """
        Convert the instance to a dictionary suitable for DynamoDB resource.
        """
        return DynamoDbSerializer.to_resource_dictionary(self)
