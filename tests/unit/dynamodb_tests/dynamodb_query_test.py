"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
import moto

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

    def test_query_user(self):

        # create a few users
        for i in range(1, 11):
            user = User(i)

            user.first_name = f"first_{i}"
            user.last_name = f"last_{i}"
            user.email = f"email_{i}@example.com"
            response = self.db.save(table_name=self.__table_name, item=user)

            self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 200)

        # query for all users
        user = User()
        key = user.get_key("gsi1")
        response = self.db.query(table_name=self.__table_name, key=key)
        items = response["Items"]
        self.assertEqual(len(items), 10)

        # query for one user
        user = User()
        user.email = "email_1@example.com"
        # use the same index but this time we have an email address to add to the filter
        response = self.db.query(table_name=self.__table_name, key=user.get_key("gsi1"))

        items = response["Items"]
        self.assertEqual(len(items), 1)

    def test_query_with_pagination_start_key(self):
        """Test pagination using start_key parameter"""
        
        # Create 20 users
        for i in range(1, 21):
            user = User(i)
            user.first_name = f"first_{i}"
            user.last_name = f"last_{i}"
            user.email = f"email_{i}@example.com"
            response = self.db.save(table_name=self.__table_name, item=user)
            self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 200)

        # Query with limit of 5 - should return first 5 items and a LastEvaluatedKey
        user = User()
        key = user.get_key("gsi1")
        response = self.db.query(
            table_name=self.__table_name,
            key=key,
            limit=5
        )
        
        # Verify first batch
        items = response["Items"]
        self.assertEqual(len(items), 5, "First query should return 5 items")
        self.assertIn("LastEvaluatedKey", response, "Should have LastEvaluatedKey for pagination")
        
        # Store the LastEvaluatedKey to use as start_key
        last_key = response["LastEvaluatedKey"]
        
        # Query again using start_key - should return next 5 items
        response2 = self.db.query(
            table_name=self.__table_name,
            key=key,
            limit=5,
            start_key=last_key
        )
        
        # Verify second batch
        items2 = response2["Items"]
        self.assertEqual(len(items2), 5, "Second query should return 5 items")
        self.assertIn("LastEvaluatedKey", response2, "Should still have LastEvaluatedKey since more items exist")
        
        # Verify the items are different (pagination is working)
        first_batch_ids = {item["id"] for item in items}
        second_batch_ids = {item["id"] for item in items2}
        self.assertEqual(len(first_batch_ids.intersection(second_batch_ids)), 0, 
                        "First and second batch should contain different items")
        
        # Continue pagination until no more items
        all_items = items + items2
        next_start_key = response2["LastEvaluatedKey"]
        
        while next_start_key:
            response_next = self.db.query(
                table_name=self.__table_name,
                key=key,
                limit=5,
                start_key=next_start_key
            )
            all_items.extend(response_next["Items"])
            next_start_key = response_next.get("LastEvaluatedKey")
        
        # Verify we retrieved all 20 items
        self.assertEqual(len(all_items), 20, "Should retrieve all 20 items through pagination")
        
        # Verify all items are unique
        unique_ids = {item["id"] for item in all_items}
        self.assertEqual(len(unique_ids), 20, "All items should have unique IDs")
