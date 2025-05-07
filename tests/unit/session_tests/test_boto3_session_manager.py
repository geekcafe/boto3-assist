import pytest
from unittest.mock import patch, MagicMock
from boto3 import Session as RealBoto3Session


@pytest.fixture
def mock_boto3_session():
    """Patch boto3.Session and simulate a base and an assumed session with separate client behaviors."""
    with patch("boto3.Session", autospec=True) as mock_session_class:
        # Create base and assumed session mocks
        base_session = MagicMock(spec=RealBoto3Session)
        assumed_session = MagicMock(spec=RealBoto3Session)

        # STS client returns mocked credentials
        mock_sts_client = MagicMock()
        mock_sts_client.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "mock-access-key",
                "SecretAccessKey": "mock-secret-key",
                "SessionToken": "mock-session-token",
            }
        }

        # Assign isolated .client behavior per session
        base_session.client.side_effect = lambda service_name: (
            mock_sts_client if service_name == "sts" else MagicMock()
        )
        assumed_session.client.return_value = MagicMock()

        # Simulate two sessions: base → assumed
        mock_session_class.side_effect = [base_session, assumed_session]

        yield base_session, assumed_session, mock_sts_client, mock_session_class


def test_single_assume_role_chain(mock_boto3_session):
    base_session, assumed_session, mock_sts_client, session_class = mock_boto3_session

    from boto3_assist.boto3session import Boto3SessionManager

    manager = Boto3SessionManager(
        service_name="s3",
        aws_region="us-east-1",
        assume_role_chain=["arn:aws:iam::111111111111:role/TestRole"],
    )

    # Ensure base session initialized
    assert session_class.call_args_list[0].kwargs["region_name"] == "us-east-1"

    # Ensure assume_role called correctly
    mock_sts_client.assume_role.assert_called_once_with(
        RoleArn="arn:aws:iam::111111111111:role/TestRole",
        RoleSessionName="AssumeRoleSessionFors3",
        DurationSeconds=3600,
    )

    # Ensure second session created with correct credentials
    assert session_class.call_args_list[1].kwargs == {
        "aws_access_key_id": "mock-access-key",
        "aws_secret_access_key": "mock-secret-key",
        "aws_session_token": "mock-session-token",
        "region_name": "us-east-1",
    }

    # Ensure client created from assumed session
    _ = manager.client
    assumed_session.client.assert_called_with("s3", config=None, endpoint_url=None)


def test_no_assume_role(mock_boto3_session):
    base_session, _, _, session_class = mock_boto3_session

    from boto3_assist.boto3session import Boto3SessionManager

    manager = Boto3SessionManager(
        service_name="dynamodb",
        aws_region="us-west-2",
    )

    # Only one session created
    assert session_class.call_count == 1
    assert session_class.call_args.kwargs == {
        "profile_name": None,
        "region_name": "us-west-2",
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
        "aws_session_token": None,
    }

    # Resource created from base session
    _ = manager.resource
    base_session.resource.assert_called_with("dynamodb", config=None, endpoint_url=None)


def test_multiple_assume_role_chain():
    from boto3_assist.boto3session import Boto3SessionManager
    from boto3 import Session as RealBoto3Session

    with patch("boto3.Session", autospec=True) as mock_session_class:
        # Create three sessions: base → first assume → second assume
        base_session = MagicMock(spec=RealBoto3Session)
        first_assumed_session = MagicMock(spec=RealBoto3Session)
        second_assumed_session = MagicMock(spec=RealBoto3Session)

        # Mock each session's client() behavior
        first_sts = MagicMock()
        second_sts = MagicMock()

        # First assume_role returns first credentials
        first_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "first-key",
                "SecretAccessKey": "first-secret",
                "SessionToken": "first-token",
            }
        }

        # Second assume_role returns second credentials
        second_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "second-key",
                "SecretAccessKey": "second-secret",
                "SessionToken": "second-token",
            }
        }

        # Assign proper .client() behavior for each session
        base_session.client.side_effect = lambda svc: (
            first_sts if svc == "sts" else MagicMock()
        )
        first_assumed_session.client.side_effect = lambda svc: (
            second_sts if svc == "sts" else MagicMock()
        )
        second_assumed_session.client.return_value = MagicMock()

        # Setup session chain return order
        mock_session_class.side_effect = [
            base_session,
            first_assumed_session,
            second_assumed_session,
        ]

        # Run session manager
        manager = Boto3SessionManager(
            service_name="s3",
            aws_region="us-east-1",
            assume_role_chain=[
                "arn:aws:iam::111111111111:role/FirstRole",
                "arn:aws:iam::222222222222:role/SecondRole",
            ],
        )

        # Assert role assumptions
        first_sts.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::111111111111:role/FirstRole",
            RoleSessionName="AssumeRoleSessionFors3",
            DurationSeconds=3600,
        )
        second_sts.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::222222222222:role/SecondRole",
            RoleSessionName="AssumeRoleSessionFors3",
            DurationSeconds=3600,
        )

        # Assert final session creation used second credentials
        assert mock_session_class.call_args_list[2].kwargs == {
            "aws_access_key_id": "second-key",
            "aws_secret_access_key": "second-secret",
            "aws_session_token": "second-token",
            "region_name": "us-east-1",
        }

        # Ensure client is created from final session
        _ = manager.client
        second_assumed_session.client.assert_called_with(
            "s3", config=None, endpoint_url=None
        )
