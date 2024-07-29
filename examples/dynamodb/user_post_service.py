from boto_assist.dynamodb.dynamodb import DynamoDb
from examples.dynamodb.user_post_db_model import UserPostDbModel


class UserPostService:
    """
    A service class to handle user operations on a DynamoDB table.

    Attributes:
        db (DynamoDb): An instance of DynamoDb to interact with the database.
    """

    def __init__(self, db: DynamoDb) -> None:
        """
        Initializes the UserService with a DynamoDb instance.

        Args:
            db (DynamoDb): An instance of DynamoDb.
        """
        self.db: DynamoDb = db

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
        print(item)
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
        index_name, key = UserPostDbModel.gsi0()
        projections_ex, ex_attributes_names = (
            UserPostDbModel.get_projection_expressions()
        )
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

    def get(self, post_id: str, table_name: str) -> dict:
        """
        Retrieves a user post by post ID from the specified DynamoDB table.

        Args:
            post_id (str): The ID of the post to retrieve.
            table_name (str): The name of the DynamoDB table.

        Returns:
            dict: The retrieved post as a dictionary.
        """
        key = UserPostDbModel.pk_sk_key(post_id)
        p, e = UserPostDbModel.get_projection_expressions()
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
