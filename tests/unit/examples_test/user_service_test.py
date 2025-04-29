"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from moto import mock_aws
import boto3

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.services.user_service import UserService, User
from examples.dynamodb.services.table_service import DynamoDBTableService


@mock_aws
class UserServiceTest(unittest.TestCase):
    """
    Unit Tests for the User Service.
    We're using the Moto library to mock out the DynamoDB service.


    """

    def setUp(self):
        # Set up the mocked DynamoDB
        self.dynamodb: DynamoDB = DynamoDB()

        self.dynamodb.dynamodb_resource = boto3.resource(
            "dynamodb", region_name="us-east-1"
        )
        self.table_name = "my_test_table"
        table_service = DynamoDBTableService(self.dynamodb)
        table_service.create_a_table(table_name=self.table_name)

    def test_create_user(self):
        user_service = UserService(self.dynamodb, self.table_name)

        for i in range(10):
            str_i = str(i).zfill(4)
            user: User = User(
                id=f"id{str_i}",
                first_name=f"first{str_i}",
                last_name=f"last{str_i}",
                email=f"user{str_i}@example.com",
            )
            user = user_service.save(user=user)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
