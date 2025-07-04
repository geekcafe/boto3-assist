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

    def create_data_process_task(
        self,
        name: str,
        step: str,
        task_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Task:
        task = Task()
        if task_id:
            task.id = task_id
            task.step_id = Task.generate_uuid()
        else:
            task.step_id = task.id
        task.name = name
        task.step = step

        task.metadata = metadata
        response = self.db.save(
            table_name=self.__table_name, item=task, fail_if_exists=True
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        return task

    def test_primary_key_query_sort(self):
        task: Task = self.create_data_process_task(
            name="test", step="test", task_id=None
        )

        # no create a bunch of children
        for i in range(0, 10):
            self.create_data_process_task(
                name="test",
                step=f"child-{i}",
                task_id=task.id,
                metadata={"child": f"i"},
            )

        query_model: Task = Task()
        query_model.id = task.id
        key = query_model.get_key("primary")
        query_response = self.db.query(table_name=self.__table_name, key=key)

        # primary task and 10 children == 11
        assert len(query_response["Items"]) == 11
