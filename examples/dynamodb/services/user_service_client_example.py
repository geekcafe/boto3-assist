"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Any
from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.models.user_model import User


class UserService:
    """
    A service class to handle user operations on a DynamoDB table.

    Attributes:
        db (DynamoDB): An instance of DynamoDB to interact with the database.
    """

    def __init__(self, db: DynamoDB, table_name: str) -> None:
        """
        Initializes the UserService with a DynamoDB instance.

        Args:
            db (DynamoDB): An instance of DynamoDB.
        """
        self.db: DynamoDB = db
        self.table_name: str = table_name

    def save(
        self,
        id: str,  # pylint: disable=w0622
        first_name: str,
        last_name: str,
        email: str,
    ) -> None:
        """
        Saves a user to the specified DynamoDB table using client syntax.

        Args:
            id (str): The user ID.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            email (str): The user's email.
            table_name (str): The name of the DynamoDB table.
        """

        user_id: str = f"user#{id}"
        client_syntax_item = {
            "pk": {"S": user_id},
            "sk": {"S": user_id},
            "id": {"S": id},
            "gsi0_pk": {"S": "users#"},
            "gsi0_sk": {"S": f"email#{email}"},
            "first_name": {"S": first_name},
            "last_name": {"S": last_name},
            "email": {"S": email},
            "age": {"N": "30"},  # Need to wrap as a string or it will throw an error.
        }
        self.db.save(item=client_syntax_item, table_name=self.table_name)
