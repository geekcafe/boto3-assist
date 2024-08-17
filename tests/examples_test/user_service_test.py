"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import cast
from typing import Optional, List
from moto import mock_aws
import boto3
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase
from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.user_service import UserService, UserDbModel
from examples.dynamodb.table_service import DynamoDbTableService


@mock_aws
class UserServiceTest(unittest.TestCase):
    def setUp(self):
        # Set up the mocked DynamoDB
        self.dynamodb: DynamoDB = DynamoDB(setup_session=False)

        self.dynamodb.dynamodb_resource = boto3.resource(
            "dynamodb", region_name="us-west-1"
        )
        self.table_name = "my_test_table"
        table_service = DynamoDbTableService(self.dynamodb)
        table_service.create_a_table(table_name=self.table_name)

    def test_create_user(self):
        user_service = UserService(self.dynamodb, self.table_name)

        for i in range(10):
            str_i = str(i).zfill(4)
            user: UserDbModel = UserDbModel(
                id=f"id{str_i}",
                first_name=f"first{str_i}",
                last_name=f"last{str_i}",
                email=f"user{str_i}@example.com",
            )
            user = user_service.save(user=user)
