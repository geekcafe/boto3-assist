import pytest
import os
from typing import List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from tests.integration.tenant_services import TenantServices


@pytest.mark.integration
def test_cross_account_role_assumption_with_profile():
    responses = []

    profile_name = os.getenv("AWS_PROFILE")

    connections: List[dict] = [
        {
            "profile_name": profile_name,
            "aws_account": "959096737760",
            "aws_region": "us-east-1",
            "role_name": "CrossAccountAccessRole",
            "table_name": "db-us-east-1",
            "enabled": False,
        },
        {
            "profile_name": profile_name,
            "aws_account": "959096737760",
            "aws_region": "eu-west-2",
            "role_name": "CrossAccountAccessRole",
            "table_name": "db-eu-west-2",
            "enabled": False,
        },
        {
            "profile_name": profile_name,
            "aws_account": "257932641017",
            "aws_region": "us-east-1",
            "role_name": "CrossAccountAccessRole",
            "table_name": "aplos-nca-saas-production-demo-001-database",
            "enabled": True,
        },
        {
            "profile_name": profile_name,
            "aws_region": "us-east-1",
            "aws_account": "211125601483",
            "role_name": "CrossAccountAccessRole",
            "table_name": "aplos-nca-saas-production-app-database",
            "enabled": True,
        },
    ]

    for connection in connections:
        role_arn = (
            f"arn:aws:iam::{connection['aws_account']}:role/{connection['role_name']}"
        )
        if connection["enabled"]:
            db = DynamoDB(
                aws_profile=connection["profile_name"],
                aws_region=connection["aws_region"],
                assume_role_arn=role_arn,
            )
            ts: TenantServices = TenantServices(
                db=db, table_name=connection["table_name"]
            )
            response = ts.list()
            responses.append(response)
            # print(response)
        else:
            responses.append(None)

    print(len(responses))
    assert len(responses) == 3


def main():
    test_cross_account_role_assumption_with_profile()
    pass


if __name__ == "__main__":
    main()
