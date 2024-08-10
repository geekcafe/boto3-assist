"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.user_post_db_model import UserPostDbModel


class UserPostService:
    """
    A service class to handle user operations on a DynamoDB table.

    Attributes:
        db (DynamoDB): An instance of DynamoDB to interact with the database.
    """

    def __init__(self, db: DynamoDB) -> None:
        """
        Initializes the UserService with a DynamoDB instance.

        Args:
            db (DynamoDB): An instance of DynamoDB.
        """
        self.db: DynamoDB = db

    def save(self, user_post: UserPostDbModel, table_name: str) -> dict:
        """
        Saves a user post to the specified DynamoDB table.

        Args:
            user_post (UserPostDbModel): The user post model to save.
            table_name (str): The name of the DynamoDB table.

        Returns:
            dict: The saved item as a dictionary.
        """
        item: dict = user_post.to_resource_dictionary()
        self.db.save(item=item, table_name=table_name)
        return item

    def list_by_title(self, table_name: str) -> list:
        """
        Lists user posts by title using a global secondary index.

        Args:
            table_name (str): The name of the DynamoDB table.

        Returns:
            list: A list of user posts.
        """
        model = UserPostDbModel()
        index_name = "gsi0"
        key = model.indexes.get(index_name).key()
        projections_ex = model.projection_expression
        ex_attributes_names = model.projection_expression_attribute_names
        user_list = self.db.query(
            key=key,
            index_name=index_name,
            table_name=table_name,
            projection_expression=projections_ex,
            expression_attribute_names=ex_attributes_names,
        )
        if "Items" in user_list:
            user_list = user_list.get("Items")
        return user_list

    def get(self, slug: str, table_name: str) -> dict:
        """
        Retrieves a user post by post ID from the specified DynamoDB table.

        Args:
            slug (str): The ID of the post to retrieve.
            table_name (str): The name of the DynamoDB table.

        Returns:
            dict: The retrieved post as a dictionary.
        """

        model = UserPostDbModel(slug=slug)
        key = model.indexes.primary.key()
        p = model.projection_expression
        e = model.projection_expression_attribute_names
        response = self.db.get(
            key=key,
            table_name=table_name,
            projection_expression=p,
            expression_attribute_names=e,
        )

        entry: dict = {}
        if "Item" in response:
            entry: dict = response.get("Item")
        return entry
