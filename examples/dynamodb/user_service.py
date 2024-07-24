from gc_boto3_lib.dynamodb.dynamodb import DynamoDb
from examples.dynamodb.user_db_model import UserDbModel


class UserService:
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

    def save_user_resource_syntax(
        self,
        id: str,  # pylint: disable=w0622
        first_name: str,
        last_name: str,
        email: str,
        table_name: str,
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
        self.db.save(item=resource_syntax_item, table_name=table_name)

    def save_user_client_syntax(
        self,
        id: str,  # pylint: disable=w0622
        first_name: str,
        last_name: str,
        email: str,
        table_name: str,
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
        self.db.save(item=client_syntax_item, table_name=table_name)

    def save_user_using_model(
        self,
        id: str,  # pylint: disable=w0622
        first_name: str,
        last_name: str,
        email: str,
        table_name: str,
        db_dictionary_type: str = "resource",
    ) -> dict:
        """
        Saves a user to the specified DynamoDB table using the user model.

        Args:
            id (str): The user ID.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            email (str): The user's email.
            table_name (str): The name of the DynamoDB table.
            db_dictionary_type (str): The type of dictionary to use ('resource' or 'client').

        Returns:
            dict: The saved item as a dictionary.
        """
        user: UserDbModel = UserDbModel(
            id=id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        item: dict = (
            user.to_resource_dictionary()
            if db_dictionary_type == "resource"
            else user.to_client_dictionary()
        )
        print(item)
        self.db.save(item=item, table_name=table_name)
        return item

    def list_users(self, table_name: str) -> list:
        """
        Lists users using a global secondary index.

        Args:
            table_name (str): The name of the DynamoDB table.

        Returns:
            list: A list of users.
        """
        index_name, key = UserDbModel.gsi0()
        projections_ex, ex_attributes_names = UserDbModel.get_projection_expressions()
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

    def get_user(self, user_id: str, table_name: str) -> dict:
        """
        Retrieves a user by user ID from the specified DynamoDB table.

        Args:
            user_id (str): The ID of the user to retrieve.
            table_name (str): The name of the DynamoDB table.

        Returns:
            dict: The retrieved user as a dictionary.
        """
        pk = f"user#{user_id}"
        sk = pk  # The key is the same
        key = {"pk": pk, "sk": sk}

        # Alternative way to get the key from the model
        key = UserDbModel.pk_sk_key(user_id)
        p, e = UserDbModel.get_projection_expressions()
        response = self.db.get(
            key=key,
            table_name=table_name,
            projection_expression=p,
            expression_attribute_names=e,
        )

        user: dict = {}
        if "Item" in response:
            user = response.get("Item")

        return user
