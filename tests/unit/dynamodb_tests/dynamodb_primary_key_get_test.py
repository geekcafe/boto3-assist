"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
import moto
from typing import Optional
from tests.unit.dynamodb_tests.db_models.user_model import User
from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.dynamodb.dynamodb import DynamoDB
from tests.unit.common.db_test_helpers import DbTestHelper


@moto.mock_aws
class DbQueryTest(unittest.TestCase):
    "Serialization Tests"

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)

        ev: EnvironmentLoader = EnvironmentLoader()
        # NOTE: you need to make sure the the env file below exists or you will get an error
        ev.load_environment_file(file_name=".env.unittest")
        self.__table_name = "mock_test_table"

        self.db: DynamoDB = DynamoDB()

    def setUp(self):
        # load our test environment file to make sure we override any default AWS Environment Vars setup
        # we don't want to accidentally connect to live environments
        # https://docs.getmoto.org/en/latest/docs/getting_started.html

        self.db: DynamoDB = self.db or DynamoDB()
        DbTestHelper().helper_create_mock_table(self.__table_name, self.db.client)
        print("Setup Complete")

    def create_user(
        self,
        id: str,
        first_name: str,
        last_name: str,
        email: str,
    ) -> User:
        user = User()

        user.id = id
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        response = self.db.save(
            table_name=self.__table_name, item=user, fail_if_exists=True
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        return user

    def test_primary_key_get(self):
        user: User = self.create_user(
            id="id1",
            first_name="first",
            last_name="last",
            email="email@example.com",
        )

        get_model: User = User()
        get_model.id = user.id

        get_response = self.db.get(table_name=self.__table_name, model=get_model)

        assert get_response["Item"]["id"] == f"{user.id}"

        user = User()
        get_response = self.db.get(table_name=self.__table_name, model=user)
        assert "Item" not in get_response
