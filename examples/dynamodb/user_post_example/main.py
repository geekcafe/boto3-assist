"""
DynamoDB Example
"""

import json
import os
from pathlib import Path

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.dynamodb.dynamodb_importer import DynamoDBImporter

from examples.dynamodb.services.table_service import DynamoDBTableService
from examples.dynamodb.services.user_post_service import UserPost, UserPostService
from examples.dynamodb.services.user_service import UserService, User
from examples.dynamodb.services.user_service_client_example import (
    UserService as UserServiceClientExample,
)
from examples.dynamodb.services.user_service_resource_example import (
    UserService as UserServiceResourceExample,
)


class DynamoDBExample:
    """An example of using and debuggin DynamoDB"""

    def __init__(
        self, user_table: str, user_post_table: str, import_table_name: str
    ) -> None:
        self.db: DynamoDB = DynamoDB()
        self.table_service: DynamoDBTableService = DynamoDBTableService(self.db)
        self.user_service: UserService = UserService(self.db, table_name=user_table)
        self.user_post_service: UserPostService = UserPostService(
            self.db, table_name=user_post_table
        )
        self.import_table_name = import_table_name
        self.user_service_client: UserServiceClientExample = UserServiceClientExample(
            self.db, table_name=user_table
        )

        self.user_service_resource: UserServiceResourceExample = (
            UserServiceResourceExample(self.db, table_name=user_table)
        )

    def create_tables(self):
        tables = [
            self.user_service.table_name,
            self.user_post_service.table_name,
            self.import_table_name,
        ]

        for table_name in tables:
            if not self.table_service.table_exists(table_name):
                self.table_service.create_a_table(table_name)

    def run_examples(self):
        """Run a basic examples with some CRUD examples"""

        # I'm going to use a single table design pattern but you don't have to
        self.create_tables()

        # load some data
        self.__generate_some_users()

        print("\nLIST OUR USERS")
        users = self.user_service.list_users()
        for user in users:
            print(json.dumps(user, indent=4))

        # use a known user id from out saving user example
        print("\nGETTING A SINGLE USER")
        user_id = "dfcad9d0-a9b3-43ff-83a6-a62965c70178"
        user = self.user_service.get_user_simplified(user_id=user_id)
        print(json.dumps(user, indent=5))

        print("\nGETTING A SUSPENDED USER")
        users = self.user_service.list_users(status="suspended")
        for user in users:
            print(json.dumps(user, indent=5))

        print("\nGETTING ACTIVE USERS")
        users = self.user_service.list_users(status="active")
        for user in users:
            print(json.dumps(user, indent=4))

        user = self.user_service.get_user_simplified(
            user_id="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        )
        print("\nGETTING A USER THAT DOESN'T EXIST")
        print(json.dumps(user, indent=4))

    def __generate_some_users(self):
        print("upserting users")
        ################################################
        ### Alice Smith

        self.user_service_client.save(
            id="ed3ca6c8-7a8d-4da1-9098-27182b0fafdf",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
        )

        self.__add_user_some_posts(user_id="ed3ca6c8-7a8d-4da1-9098-27182b0fafdf")

        ################################################
        ### Bob Smith
        self.user_service_resource.save(
            id="dfcad9d0-a9b3-43ff-83a6-a62965c70178",
            first_name="Bob",
            last_name="Smith",
            email="bob@example.com",
        )

        ################################################
        ### Alex Smith

        self.user_service.save(
            id="031c9a9a-b835-4026-b4a0-eb49f4a151ae",
            first_name="Alex",
            last_name="Smith",
            email="alex.smith@example.com",
        )

        ################################################
        ### Betty Smith
        user: User = User()
        user.id = "98381a51-6397-40cb-b581-1ea313e76c1d"
        user.first_name = "Bett"
        user.last_name = "Smith"
        user.email = "betty.smith@example.com"
        user.status = "suspended"

        self.user_service.save(user=user)

    def __add_user_some_posts(self, user_id: str):
        """Add some random posts"""

        print("adding posts")

        for i in range(5):
            model: UserPost = UserPost(title=f"Title {i}", user_id=user_id)
            model.slug = f"/coding/{i}"
            model.data = f"""
            <html>
            <body>
            <h1>Some H1 Title {i}</h1>
            </body>
            </html>
            """
            self.user_post_service.save(user_post=model)

        self.__import_files()

    def __import_files(self):
        import_directory = os.getenv("IMPORT_DIRECTORY")
        if import_directory is not None:
            print(f"Importing files from {import_directory}")
            root = Path(__file__).parents[2].absolute()
            import_path = Path(os.path.join(root, import_directory)).absolute()
            if os.path.exists(import_path):
                files = os.listdir(import_path)
                files = [os.path.join(import_path, f) for f in files]
                print(f"Importing files from {import_path}")
                # do the import
                importer: DynamoDBImporter = DynamoDBImporter(
                    table_name=self.import_table_name, db=self.db
                )

                importer.import_json_files(files)

            else:
                print(f"Import directory {import_path} does not exist")


def main():
    """Main"""
    # get an environment file name or default to .env.docker
    env_file_name: str = os.getenv("ENVRIONMENT_FILE", ".env.docker")
    path = os.path.join(str(Path(__file__).parents[2].absolute()), env_file_name)
    el: EnvironmentLoader = EnvironmentLoader()
    if not os.path.exists(path=path):
        raise FileNotFoundError("Failed to find the environmetn file")
    loaded: bool = el.load_environment_file(path=path)
    if not loaded:
        raise RuntimeError("Failed to load my local environment")

    table_name = "application_table"
    example: DynamoDBExample = DynamoDBExample(
        user_table=table_name,
        user_post_table=table_name,
        import_table_name=table_name,
    )
    # load a single table design
    example.run_examples()

    example = DynamoDBExample(
        user_table="user_table",
        user_post_table="user_post_table",
        import_table_name="import_table",
    )
    # load different table
    example.run_examples()


if __name__ == "__main__":
    main()
