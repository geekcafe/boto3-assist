from abc import ABC, abstractmethod
from typing import Any
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class IDynamoDBService(ABC):
    """DynamoDB Service Interface"""

    @property
    @abstractmethod
    def db(self) -> DynamoDB:
        """Property that returns a DynamoDB service resource."""
        pass

    @db.setter
    @abstractmethod
    def db(self, val: DynamoDB) -> None:
        """Property setter for the DynamoDB service resource."""
        pass

    @abstractmethod
    def save(self, model: DynamoDBModelBase) -> Any:
        """Save a DynamoDBModelBase instance to the database."""
        pass
