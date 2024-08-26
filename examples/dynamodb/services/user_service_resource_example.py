"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Any
from boto3_assist.dynamodb.dynamodb import DynamoDB


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
        Saves a user to the specified DynamoDB table using resource syntax.

        Args:
            id (str): The user ID.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            email (str): The user's email.
            table_name (str): The name of the DynamoDB table.
        """

        user_id: str = f"user#{id}"
        resource_syntax_item = {
            "pk": user_id,
            "sk": user_id,
            "id": id,
            "gsi0_pk": "users#",
            "gsi0_sk": f"email#{email}",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "age": 30,  # Notice you can use an int here and not wrap it as a string.
        }
        self.db.save(item=resource_syntax_item, table_name=self.table_name)
