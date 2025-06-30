import unittest
from unittest.mock import patch

from boto3_assist.aws_lambda.event_info import LambdaEventInfo


class TestLambdaEventInfo(unittest.TestCase):
    """
    Unit tests for the LambdaEventInfo utility class.
    Covers methods for extracting HTTP method types, resource paths,
    authorizer claims, and overriding event information.
    """

    def setUp(self):
        """
        Set up the test environment with a sample Lambda event.
        """
        self.event = {
            "method_type": "POST",
            "path": "/users/123",
            "resourcePath": "/users/{user-id}",
            "requestContext": {
                "authorizer": {
                    "claims": {"token_use": "access", "email": "user@example.com"}
                }
            },
            "headers": {"Authorization": "Bearer jwt.token.here"},
            "pathParameters": {"user-id": "123"},
            "Records": [{"messageId": "abc-123", "body": '{"key": "value"}'}],
        }

    def test_get_http_method_type(self):
        """
        Test that the HTTP method type is correctly extracted from the event.
        """
        result = LambdaEventInfo.ApiGatewayPayload.get_http_method_type(self.event)
        self.assertEqual(result, "POST")

    def test_get_resource_path(self):
        """
        Test that the resource path is correctly extracted from the event.
        """
        result = LambdaEventInfo.ApiGatewayPayload.get_resource_path(self.event)
        self.assertEqual(result, "/users/123")

    def test_get_resource_pattern(self):
        """
        Test that the resource pattern with placeholders is correctly extracted.
        """
        result = LambdaEventInfo.ApiGatewayPayload.get_resource_pattern(self.event)
        self.assertEqual(result, "/users/{user-id}")

    def test_get_authenticated_email(self):
        """
        Test that the authenticated email is correctly extracted from the authorizer claims.
        """
        result = (
            LambdaEventInfo.ApiGatewayPayload.AuthorizerPayload.get_authenticated_email(
                self.event
            )
        )
        self.assertEqual(result, "user@example.com")

    def test_get_token_use(self):
        """
        Test that the token use is correctly extracted from the authorizer claims.
        """
        result = LambdaEventInfo.ApiGatewayPayload.AuthorizerPayload.get_token_use(
            self.event
        )
        self.assertEqual(result, "access")

    @patch("boto3_assist.cognito.cognito_authorizer.CognitoCustomAuthorizer.parse_jwt")
    def test_get_value_from_token(self, mock_parse_jwt):
        """
        Test that values are correctly extracted from the JWT token.
        """
        mock_parse_jwt.return_value = {"email": "user@example.com"}
        result = (
            LambdaEventInfo.ApiGatewayPayload.AuthorizerPayload.get_value_from_token(
                self.event, "email"
            )
        )  # pylint: disable=w0212
        self.assertEqual(result, "user@example.com")

    def test_get_target_user_id(self):
        """
        Test that the target user ID is correctly extracted from the path parameters.
        """
        result = LambdaEventInfo.HttpPathParameters.get_target_user_id(self.event)
        self.assertEqual(result, "123")

    def test_get_message_id(self):
        """
        Test that the message ID is correctly extracted from the event records.
        """
        result = LambdaEventInfo.get_message_id(self.event)
        self.assertEqual(result, "abc-123")

    def test_get_body(self):
        """
        Test that the body is correctly extracted and parsed from the event.
        """
        result = LambdaEventInfo.get_body(self.event)
        self.assertEqual(result, {"key": "value"})

    def test_override_event_info(self):
        """
        Test that event information can be correctly overridden.
        """
        updated_event = LambdaEventInfo.override_event_info(
            self.event, "new_key", "new_value"
        )
        self.assertIn("new_key", updated_event)
        self.assertEqual(updated_event["new_key"], "new_value")


if __name__ == "__main__":
    unittest.main()
