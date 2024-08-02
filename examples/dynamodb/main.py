"""
DynamoDb Example
"""

import json
import os
from pathlib import Path

from boto_assist.dynamodb.dynamodb import DynamoDb
from boto_assist.environment_services.environment_loader import EnvironmentLoader

from examples.dynamodb.table_service import DynamoDbTableService
from examples.dynamodb.user_post_service import UserPostDbModel, UserPostService
from examples.dynamodb.user_service import UserService


class DynamoDbExample:
    """An example of using and debuggin DynamoDb"""

    def __init__(self) -> None:
        self.db: DynamoDb = DynamoDb()
        self.table_service: DynamoDbTableService = DynamoDbTableService(self.db)
        self.user_service: UserService = UserService(self.db)
        self.user_post_service: UserPostService = UserPostService(self.db)

    def run_examples(self, table_name: str):
        """Run a basic examples with some CRUD examples"""

        # I'm going to use a single table design pattern but you don't have to

        if not self.table_service.table_exists(table_name):
            self.table_service.create_a_table(table_name)

        # load some data
        self.__load_users(table_name=table_name)

        print("\nLIST OUR USERS")
        users = self.user_service.list_users(table_name=table_name)
        for user in users:
            print(json.dumps(user, indent=4))

        # use a known user id from out saving user example
        print("\nGETTING A SINGLE USER")
        user_id = "dfcad9d0-a9b3-43ff-83a6-a62965c70178"
        user = self.user_service.get_user(user_id=user_id, table_name=table_name)
        print(json.dumps(user, indent=4))

        print("\nGETTING A SUSPENDED USER")
        users = self.user_service.list_users(table_name=table_name, status="suspended")
        for user in users:
            print(json.dumps(user, indent=4))

        print("\nGETTING ACTIVE USERS")
        users = self.user_service.list_users(table_name=table_name, status="active")
        for user in users:
            print(json.dumps(user, indent=4))

    def __load_users(self, table_name: str):
        print("upserting users")
        ################################################
        ### Alice Smith

        self.user_service.save_user_resource_syntax(
            id="ed3ca6c8-7a8d-4da1-9098-27182b0fafdf",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            table_name=table_name,
        )

        self.__add_user_some_posts(
            user_id="ed3ca6c8-7a8d-4da1-9098-27182b0fafdf", table_name=table_name
        )

        ################################################
        ### Bob Smith
        self.user_service.save_user_client_syntax(
            id="dfcad9d0-a9b3-43ff-83a6-a62965c70178",
            first_name="Bob",
            last_name="Smith",
            email="bob@example.com",
            table_name=table_name,
        )

        ################################################
        ### Alex Smith

        self.user_service.save_user_using_model(
            id="031c9a9a-b835-4026-b4a0-eb49f4a151ae",
            first_name="Alex",
            last_name="Smith",
            email="alex.smith@example.com",
            table_name=table_name,
        )

        ################################################
        ### Betty Smith
        self.user_service.save_user_using_model(
            id="98381a51-6397-40cb-b581-1ea313e76c1d",
            first_name="Bett",
            last_name="Smith",
            email="betty.smith@example.com",
            status="suspended",
            table_name=table_name,
        )

    def __add_user_some_posts(self, user_id: str, table_name: str):
        """Add some random posts"""

        print("adding posts")

        for i in range(5):
            model: UserPostDbModel = UserPostDbModel(
                title=f"Title {i}", user_id=user_id
            )
            model.slug = f"/coding/{i}"
            model.data = f"""
            <html>
            <body>
            <h1>Some H1 Title {i}</h1>
            </body>
            </html>
            """
            self.user_post_service.save(user_post=model, table_name=table_name)


def main():
    """Main"""
    # get an environment file name or default to .env.docker
    env_file_name: str = os.getenv("ENVRIONMENT_FILE", ".env.docker")
    path = os.path.join(str(Path(__file__).parents[2].absolute()), env_file_name)
    el: EnvironmentLoader = EnvironmentLoader()
    if not os.path.exists(path=path):
        raise FileNotFoundError("Failed to find the environmetn file")
    loaded: bool = el.load_environment_file(path)
    if not loaded:
        raise RuntimeError("Failed to load my local environment")

    example: DynamoDbExample = DynamoDbExample()
    table_name = "application_table"
    example.run_examples(table_name)


if __name__ == "__main__":
    main()
