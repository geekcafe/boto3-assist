"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import unittest
import moto
from typing import List


from mypy_boto3_dynamodb import DynamoDBClient

from dynamodb.models.cms.page import Page
from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.dynamodb.dynamodb import DynamoDB


@moto.mock_aws
class DynamoDBSortinglUnitTest(unittest.TestCase):
    "Sorting Tests"

    def setUp(self):
        # load our test environment file to make sure we override any default AWS Environment Vars setup
        # we don't want to accidently connec to live environments
        # https://docs.getmoto.org/en/latest/docs/getting_started.html
        ev: EnvironmentLoader = EnvironmentLoader()
        # NOTE: you need to make sure the the env file below exists or you will get an error
        ev.load_environment_file(file_name=".env.unittest")
        self.__table_name = "mock_test_table"

        # env_vars = str(os.environ.).split(",")
        for key, value in os.environ.items():
            print(f"{key}: {value}")

        # option 1: create a connection directly
        # self.client: DynamoDBClient = boto3.client("dynamodb", region_name="us-east-1")

        # option 2: we can now use our internal libraries, which will wire up everything for us.
        self.db: DynamoDB = DynamoDB()
        self.helper_create_mock_table(self.db.dynamodb_client)
        print("Setup Complete")

    def test_storing_and_sorting_test(self):
        """
        Test the db sorting on a query.  We want to return a list of page in the order of the
        directory structure. This would be used in an admin tool to display the pages in the order
        """
        # add some values an any order we want
        slugs = self.helper_get_some_slugs()
        self.helper_add_some_slugs(slugs=slugs, site_id="geekcafe.com")

        page: Page = Page()
        page.site_id = "geekcafe.com"
        key = page.indexes.primary.key(include_sort_key=False)
        pages = self.db.query(
            table_name=self.__table_name, key=key, source="unittest", ascending=True
        )

        # after the insert we can sort our expected vaues
        slugs.sort()

        self.assertIn("Items", pages)
        self.assertEqual(len(slugs), len(pages["Items"]))

        # compare the local array to the order of the slugs returned (they should be sorted from the db query)
        for i, _ in enumerate(slugs):
            self.assertEqual(slugs[i], pages["Items"][i]["slug"])

    def test_projections_with_sorting(self) -> None:
        # add some values an any order we want
        slugs = self.helper_get_some_slugs()
        self.helper_add_some_slugs(slugs=slugs, site_id="geekcafe.com")

        page: Page = Page()
        page.site_id = "geekcafe.com"
        key = page.indexes.primary.key(include_sort_key=False)

        # test projections
        slugs_only = self.db.query(
            table_name=self.__table_name,
            key=key,
            source="unittest",
            ascending=True,
            projection_expression="slug",
        )

        self.assertIn("Items", slugs_only)
        self.assertEqual(len(slugs), len(slugs_only["Items"]))
        # we should only have one key - the "slug"
        self.assertEqual(1, len(slugs_only["Items"][0].keys()))

        # after the insert we can sort our expected vaues
        slugs.sort()

        # compare the local array to the order of the slugs returned (they should be sorted from the db query)
        for i, _ in enumerate(slugs):
            self.assertEqual(slugs[i], slugs_only["Items"][i]["slug"])

    def helper_add_some_slugs(self, slugs: List[str], site_id: str) -> None:
        for slug in slugs:
            page: Page = Page()
            page.site_id = site_id
            page.slug = slug
            self.db.save(item=page, table_name=self.__table_name, source="unittest")

    def helper_get_some_slugs(self) -> list[str]:
        """
        Return a list of slugs to test with
        """

        return [
            "/zerbras",
            "/docs/docs.html",
            "/blogs/blog.html",
            "/blog/re-certify-your-aws-associates-and-cloud-practitioner-certifications-for-free.html",
            "/blog/failed-to-initialize-coreclr-hresult-0x80004005-when-doing-a-dotnet-ef-migrations.html",
            "/docs/abc.html",
            "/alphabet",
        ]

    def helper_create_mock_table(self, client: DynamoDBClient) -> None:
        """
        Create a mock DynamoDB table.
        """

        client.create_table(
            TableName=self.__table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "sk", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "gsi1_pk", "AttributeType": "S"},
                {"AttributeName": "gsi1_sk", "AttributeType": "N"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi1",
                    "KeySchema": [
                        {
                            "AttributeName": "gsi1_pk",
                            "KeyType": "HASH",
                        },  # Partition key for GSI
                        {
                            "AttributeName": "gsi1_sk",
                            "KeyType": "RANGE",
                        },  # Sort key for GSI
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"  # Project all attributes
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
