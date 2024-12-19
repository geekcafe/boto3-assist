import json
import re
from typing import Any, Dict, List, Optional, Union

from aws_lambda_powertools import Logger

from boto3_assist.cognito.cognito_authorizer import CognitoCustomAuthorizer
from boto3_assist.errors.custom_exceptions import Error
from boto3_assist.http_status_codes import HttpStatusCodes

logger = Logger()


class LambdaEventInfo:
    """
    Utility class for parsing and interacting with AWS Lambda event payloads.
    Contains methods to extract data from API Gateway payloads, path parameters,
    and headers.
    """

    class ApiGatewayPayload:
        """
        Handles API Gateway-specific event payloads.
        Provides methods to extract HTTP method types, resource paths, and
        authorizer claims.
        """

        @staticmethod
        def get_http_method_type(event: Dict[str, Any]) -> Optional[str]:
            """
            Extracts the HTTP method type (e.g., GET, POST) from the event.

            Args:
                event: The Lambda event payload.

            Returns:
                The HTTP method type as a string, or None if not found.
            """
            return LambdaEventInfo._get_value(event, "method_type", str)  # pylint: disable=w0212

        @staticmethod
        def get_resource_path(event: Dict[str, Any]) -> Optional[str]:
            """
            Extracts the resource path from the event.

            Args:
                event: The Lambda event payload.

            Returns:
                The resource path as a string, or None if not found.
            """
            return LambdaEventInfo._get_value_ex(event, "path", str)  # pylint: disable=w0212

        @staticmethod
        def get_resource_pattern(event: Dict[str, Any]) -> Optional[str]:
            """
            Extracts the resource pattern from the event, replacing path variables
            with placeholders (e.g., /users/{user-id}).

            Args:
                event: The Lambda event payload.

            Returns:
                The resource pattern as a string, or None if not found.
            """
            return LambdaEventInfo._get_value_ex(event, "resourcePath", str)  # pylint: disable=w0212

        class AuthorizerPayload:
            """
            Handles claims and tokens in API Gateway authorizer payloads.
            """

            @staticmethod
            def get_authenticated_email(event: Dict[str, Any]) -> Optional[str]:
                """
                Extracts the authenticated email or client ID from the event based
                on the token use.

                Args:
                    event: The Lambda event payload.

                Returns:
                    The email or client ID as a string, or None if not found.
                """
                token_use = (
                    LambdaEventInfo.ApiGatewayPayload.AuthorizerPayload.get_token_use(
                        event
                    )
                )  # pylint: disable=w0212
                key = "email" if token_use == "access" else "client_id"
                return (
                    LambdaEventInfo.ApiGatewayPayload.AuthorizerPayload.get_claims_data(
                        event, key
                    )
                )  # pylint: disable=w0212

            @staticmethod
            def get_token_use(event: Dict[str, Any]) -> Optional[str]:
                """
                Extracts the token use (e.g., "access" or "id") from the event.

                Args:
                    event: The Lambda event payload.

                Returns:
                    The token use as a string, or None if not found.
                """
                return LambdaEventInfo._get_value(  # pylint: disable=w0212
                    event, "requestContext/authorizer/claims/token_use", str
                )  # pylint: disable=w0212

            @staticmethod
            def get_claims_data(event: Dict[str, Any], key: str) -> Optional[str]:
                """
                Extracts a specific claim from the authorizer payload.

                Args:
                    event: The Lambda event payload.
                    key: The claim key to extract.

                Returns:
                    The claim value as a string, or None if not found.
                """
                try:
                    value = LambdaEventInfo._get_value(  # pylint: disable=w0212
                        event, f"requestContext/authorizer/claims/{key}", str
                    )  # pylint: disable=w0212
                    if not value:
                        value = LambdaEventInfo.ApiGatewayPayload.AuthorizerPayload.get_value_from_token(
                            event, key
                        )  # pylint: disable=w0212

                    if value is None:
                        raise Error(
                            {
                                "status_code": HttpStatusCodes.HTTP_401_UNAUTHENTICATED.value,
                                "message": f"Failed to locate {key} info in JWT Token",
                            }
                        )
                    return value

                except Exception as e:
                    raise Error(
                        {
                            "status_code": HttpStatusCodes.HTTP_401_UNAUTHENTICATED.value,
                            "message": f"Failed to locate {key} info in JWT Token",
                            "exception": str(e),
                        }
                    ) from e

            @staticmethod
            def get_value_from_token(event: Dict[str, Any], key: str) -> Optional[str]:
                """
                Extracts a value from the JWT token in the event.

                Args:
                    event: The Lambda event payload.
                    key: The key to extract from the token.

                Returns:
                    The extracted value as a string, or None if not found.
                """
                try:
                    jwt_token = LambdaEventInfo._get_value(  # pylint: disable=w0212
                        event, "headers/Authorization", str
                    )  # pylint: disable=w0212
                    if jwt_token:
                        ccas = CognitoCustomAuthorizer()
                        decoded_token = ccas.parse_jwt(token=jwt_token)
                        return decoded_token.get(key)

                    raise Error(
                        {
                            "status_code": HttpStatusCodes.HTTP_404_NOT_FOUND.value,
                            "message": f"Failed to locate {key} info in JWT Token",
                        }
                    )
                except Exception as e:
                    raise Error(
                        {
                            "status_code": HttpStatusCodes.HTTP_401_UNAUTHENTICATED.value,
                            "message": f"Failed to locate {key} info in JWT Token",
                            "exception": str(e),
                        }
                    ) from e

    class HttpPathParameters:
        """
        Handles path parameters in API Gateway events.
        """

        @staticmethod
        def get_target_user_id(
            event: Dict[str, Any], key: str = "user-id"
        ) -> Optional[str]:
            """
            Extracts the target user ID from the path parameters.

            Args:
                event: The Lambda event payload.
                key: The key representing the user ID.

            Returns:
                The user ID as a string, or None if not found.
            """
            return LambdaEventInfo._get_value_from_path_parameters(event, key)  # pylint: disable=w0212

        @staticmethod
        def get_target_tenant_id(
            event: Dict[str, Any], key: str = "tenant-id"
        ) -> Optional[str]:
            """
            Extracts the target tenant ID from the path parameters.

            Args:
                event: The Lambda event payload.
                key: The key representing the tenant ID.

            Returns:
                The tenant ID as a string, or None if not found.
            """
            return LambdaEventInfo._get_value_from_path_parameters(event, key)  # pylint: disable=w0212

    @staticmethod
    def get_message_id(event: Dict[str, Any], index: int = 0) -> Optional[str]:
        """
        Extracts the message ID from an event record.

        Args:
            event: The Lambda event payload.
            index: The index of the record to extract the message ID from.

        Returns:
            The message ID as a string, or None if not found.
        """
        records: List[Dict[str, Any]] = event.get("Records", [])
        if records and len(records) > index:
            return records[index].get("messageId")
        return None

    @staticmethod
    def _get_value_ex(
        event: Dict[str, Any], key: str, expected_type: type
    ) -> Optional[Any]:
        """
        Extracts a value from the event, checking additional paths if necessary.

        Args:
            event: The Lambda event payload.
            key: The key to extract.
            expected_type: The expected type of the value.

        Returns:
            The extracted value, or None if not found.
        """
        value = LambdaEventInfo._get_value(event, key, expected_type)  # pylint: disable=w0212
        if value is None:
            value = LambdaEventInfo._get_value(
                event, f"requestContext/{key}", expected_type
            )  # pylint: disable=w0212
        return value

    @staticmethod
    def _get_value(
        event: Dict[str, Any], key: Union[str, List[str]], expected_type: type
    ) -> Optional[Any]:
        """
        Extracts a value from the event based on the key.

        Args:
            event: The Lambda event payload.
            key: The key to extract, which can be a string or a list of strings for nested keys.
            expected_type: The expected type of the value.

        Returns:
            The extracted value, or None if not found.
        """
        logger.debug({"source": "_get_value", "event": event, "key": key})
        if not event:
            return None

        if isinstance(key, str):
            key = re.split(r"[./]", key)

        value = event
        for k in key:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

        if isinstance(value, expected_type):
            return value
        return None

    @staticmethod
    def _get_value_from_path_parameters(
        event: Dict[str, Any], key: str, default: Optional[Any] = None
    ) -> Optional[str]:
        """
        Extracts a value from the path parameters in the event.

        Args:
            event: The Lambda event payload.
            key: The key to extract from the path parameters.
            default: The default value to return if the key is not found.

        Returns:
            The extracted value, or None if not found.
        """
        value = LambdaEventInfo._search_key(event, "pathParameters", key, default)  # pylint: disable=w0212
        if value is None:
            path = LambdaEventInfo.ApiGatewayPayload.get_resource_path(event)  # pylint: disable=w0212
            pattern = LambdaEventInfo.ApiGatewayPayload.get_resource_pattern(event)  # pylint: disable=w0212
            if path and pattern:
                value = LambdaEventInfo._extract_value_from_path(path, pattern, key)  # pylint: disable=w0212
        return value

    @staticmethod
    def _extract_value_from_path(
        path: str, pattern: str, variable_name: str
    ) -> Optional[str]:
        """
        Extracts a value from a path using a regex pattern.

        Args:
            path: The actual path from the event.
            pattern: The pattern with placeholders (e.g., /users/{user-id}).
            variable_name: The variable name to extract.

        Returns:
            The extracted value, or None if not found.
        """
        regex_pattern = re.sub(
            r"\{([^}]+)\}",
            lambda m: f"(?P<{m.group(1).replace('-', '_')}>[^/]+)",
            pattern,
        )
        variable_name = variable_name.replace("-", "_")
        match = re.match(regex_pattern, path)
        if match:
            return match.group(variable_name)
        return None

    @staticmethod
    def _search_key(
        event: Dict[str, Any], container: str, key: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Searches for a key within a specified container in the event.

        Args:
            event: The Lambda event payload.
            container: The container key to search within (e.g., "headers").
            key: The key to search for within the container.
            default: The default value to return if the key is not found.

        Returns:
            The extracted value, or the default value if not found.
        """
        events = [event]

        if "Records" in event:
            record = event["Records"][0]
            if "body" in record:
                body = json.loads(record["body"])
                events.append(body)
                if "requestContext" in body:
                    events.append(body["requestContext"])

        for e in events:
            container_data = e.get(container)
            if container_data and key in container_data:
                return container_data[key]

        return default

    @staticmethod
    def get_body(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extracts the body of the event payload.

        Args:
            event: The Lambda event payload.

        Returns:
            The body as a dictionary, or None if not found.
        """
        tmp = event.get("Records", [{}])[0].get("body", event)
        if isinstance(tmp, str):
            try:
                return json.loads(tmp)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON body in the payload") from e
        return tmp if isinstance(tmp, dict) else None

    @staticmethod
    def override_event_info(
        event: Dict[str, Any], key: str, value: Any
    ) -> Dict[str, Any]:
        """
        Overrides a value in the event payload.

        Args:
            event: The Lambda event payload.
            key: The key to override.
            value: The value to set.

        Returns:
            The updated event payload.
        """
        body = LambdaEventInfo.get_body(event) or {}
        body[key] = value
        return body
