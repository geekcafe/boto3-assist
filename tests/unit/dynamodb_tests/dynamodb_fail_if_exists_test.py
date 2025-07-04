"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
import moto
from typing import Optional
from tests.unit.dynamodb_tests.db_models.task import Task
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

    def test_fail_if_exists(self):

        task_id: str = "123456789"

        task = Task(task_id)
        response = self.db.save(table_name=self.__table_name, item=task)

        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 200)

        # this will fail, fail_if_exists is set to true
        self.assertRaises(
            Exception,
            self.db.save,
            table_name=self.__table_name,
            item=task,
            fail_if_exists=True,
        )

        # this does not
        response = self.db.save(table_name=self.__table_name, item=task)
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 200)
