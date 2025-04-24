"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import time
from typing import List, Dict, Any, Optional, Literal


from aws_lambda_powertools import Logger

from boto3_assist.cognito.user import CognitoUser
from boto3_assist.utilities.string_utility import StringUtility
from boto3_assist.utilities.dictionary_utility import DictionaryUtilitiy
from boto3_assist.cognito.cognito_connection import CognitoConnection

logger = Logger()


class CognitoCustomAttributes:
    """
    Defines the custom Cognito attributes available in the application.
    Use the defaults or override as needed.

    Attributes:
        USER_ID_KEY_NAME (str): The key for the custom user ID attribute.
        TENANT_ID_KEY_NAME (str): The key for the custom tenant ID attribute.
        USER_ROLES_KEY_NAME (str): The key for the custom roles attribute.
    """

    def __init__(
        self,
        user_id_key: str = "custom:user-id",
        tenant_id_key: str = "custom:tenant-id",
        user_roles_key: str = "custom:roles",
    ):
        self.user_id_custom_attribute = user_id_key
        self.tenant_id_custom_attribute = tenant_id_key
        self.user_roles_custom_attribute = user_roles_key


class CognitoUtility(CognitoConnection):
    """
    A utility class for managing AWS Cognito operations, including user creation, modification, and authentication.

    Inherits:
        CognitoConnection: Base class providing a connection to AWS Cognito.
    """

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        custom_attributes: Optional[CognitoCustomAttributes] = None,
        auto_lower_case_email_addresses: bool = True,
    ) -> None:
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.custom_attributes = custom_attributes
        self.auto_lower_case_email_addresses = auto_lower_case_email_addresses

    def admin_create_user(
        self,
        user_pool_id: Optional[str] = None,
        temp_password: Optional[str] = None,
        *,
        user: CognitoUser,
        send_invitation: bool = False,
        retry_count: int = 0,
    ) -> dict:
        """
        Creates a new user in Cognito with custom attributes and optional invitation handling.

        Args:
            user_pool_id (Optional[str]): Cognito user pool ID.
            temp_password (Optional[str]): Temporary password for the user.
            user (CognitoUser): The user object containing details to create the user.
            send_invitation (bool): Whether to send an invitation email to the user.
            retry_count (int): Number of retries for password-related issues.

        Returns:
            dict: Response from the AWS Cognito admin create user API.

        Raises:
            ValueError: If user ID or tenant ID is missing.
            Exception: If user creation fails for other reasons.
        """
        user_supplied_password = temp_password is not None

        if temp_password is None:
            temp_password = StringUtility.generate_random_password(15)

        if user.id is None:
            raise ValueError("User id is required")

        if user.tenant_id is None:
            raise ValueError("Tenant id is required")

        user_attributes = self.__set_user_attributes(user=user)

        if not send_invitation:
            user_attributes.append({"Name": "email_verified", "Value": "true"})

        try:
            kwargs = {
                "UserPoolId": user_pool_id,
                "Username": user.email,
                "UserAttributes": user_attributes,
                "DesiredDeliveryMediums": ["EMAIL"],
            }

            if not send_invitation:
                kwargs["MessageAction"] = "SUPPRESS"

            response = self.client.admin_create_user(**kwargs)

            self.admin_set_user_password(
                user_name=user.email,
                password=temp_password,
                user_pool_id=user_pool_id,
                is_permanent=True,
            )

            return dict(response)

        except self.client.exceptions.UsernameExistsException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            raise
        except self.client.exceptions.InvalidPasswordException:
            if not user_supplied_password and retry_count < 5:
                logger.debug(
                    {
                        "action": "admin_create_user",
                        "user_pool_id": user_pool_id,
                        "user_name": user.email,
                        "retry_count": retry_count,
                    }
                )
                retry_count += 1
                return self.admin_create_user(
                    user_pool_id=user_pool_id,
                    temp_password=None,
                    send_invitation=send_invitation,
                    user=user,
                    retry_count=retry_count,
                )
            raise
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    def admin_disable_user(
        self, user_name: str, user_pool_id: str, reset_password: bool = True
    ) -> dict:
        """Disable a user in cognito"""
        response = self.client.admin_disable_user(
            UserPoolId=user_pool_id, Username=user_name
        )

        if reset_password:
            self.admin_set_user_password(
                user_name=user_name, user_pool_id=user_pool_id, password=None
            )

        return response

    def admin_delete_user(self, user_name: str, user_pool_id: str) -> dict:
        """Delete the user account"""

        # we need to disbale a user first
        self.admin_disable_user(
            user_name=user_name, user_pool_id=user_pool_id, reset_password=False
        )

        response = self.client.admin_delete_user(
            UserPoolId=user_pool_id, Username=user_name
        )

        return dict(response)

    def admin_enable_user(
        self, user_name: str, user_pool_id: str, reset_password: bool = True
    ) -> dict:
        """Enable the user account"""
        response = self.client.admin_enable_user(
            UserPoolId=user_pool_id, Username=user_name
        )

        if reset_password:
            # reset the password
            self.admin_set_user_password(
                user_name=user_name, user_pool_id=user_pool_id, password=None
            )
        return response

    def admin_set_user_password(
        self, user_name, password: str | None, user_pool_id, is_permanent=True
    ) -> dict:
        """Set a user password"""

        if not password:
            password = StringUtility.generate_random_password(15)
        logger.debug(
            {
                "action": "admin_set_user_password",
                "UserPoolId": user_pool_id,
                "Username": user_name,
                "Password": "****************",
                "Permanent": is_permanent,
            }
        )

        for i in range(5):
            try:
                response = self.client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=user_name,
                    Password=password,
                    Permanent=is_permanent,
                )
                break
            except Exception as e:  # pylint: disable=w0718
                time.sleep(5 * i + 1)
                logger.error(f"Error: {e}")
                if i >= 4:
                    raise e

        return response

    def update_user_account(self, *, user_pool_id: str, user: CognitoUser) -> dict:
        """
        Update the cognito user account
        """
        user_attributes = self.__set_user_attributes(user=user)

        if user.cognito_user_name is None:
            raise ValueError("User cognito user name is required")

        response = self.client.admin_update_user_attributes(
            UserPoolId=f"{user_pool_id}",
            Username=f"{user.cognito_user_name}",
            UserAttributes=user_attributes,
            ClientMetadata={"string": "string"},
        )
        return response

    def sign_up_cognito_user(self, email, password, client_id) -> dict | None:
        """
        This is only allowed if the admin only flag is not being inforced.
        Under most circumstatnces we won't have this enabled
        """
        email = self.__format_email(email=email)
        try:
            # Create the user in Cognito
            response = self.client.sign_up(
                ClientId=client_id,
                Username=email,
                Password=password,
                UserAttributes=[{"Name": "email", "Value": email}],
            )

            logger.debug(
                f"User {email} created successfully. Confirmation code sent to {email}."
            )
            return dict(response)

        except self.client.exceptions.UsernameExistsException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                f"The username {email} already exists. Please choose a different username."
            )
            return None

        except self.client.exceptions.InvalidPasswordException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                "Password does not meet the requirements. Please choose a stronger password."
            )
            return None

        except Exception as e:  # pylint: disable=w0718
            logger.error(f"Error: {e}")
            return None

    def authenticate_user_pass_auth(
        self, username, password, client_id
    ) -> tuple[str, str, str]:
        """
        Login with the username/passwrod combo + client_id
        Returns:
            Tuple: id_token, access_token, refresh_token
            Use the id_token as the jwt
            Use the access_token if you are directly accessing aws resources
            Use the refresh_token if you are attempting to get a 'refreshed' jwt token
        """
        # Initiate the authentication process and get the session
        auth_response = self.client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )

        if "ChallengeName" in auth_response:
            raise RuntimeError("New password required before a token can be provided")

        # Extract the session tokens
        id_token = auth_response["AuthenticationResult"]["IdToken"]
        access_token = auth_response["AuthenticationResult"]["AccessToken"]
        refresh_token = auth_response["AuthenticationResult"]["RefreshToken"]

        return id_token, access_token, refresh_token

    def create_client_app_machine_to_machine(
        self,
        user_pool_id,
        client_name,
        id_token_time_out=60,
        id_token_units: Literal["days", "hours", "minutes", "seconds"] = "minutes",
        access_token_time_out=60,
        access_token_units: Literal["days", "hours", "minutes", "seconds"] = "minutes",
        refresh_token_time_out=60,
        refresh_token_units: Literal["days", "hours", "minutes", "seconds"] = "minutes",
    ) -> dict:
        # valid units: 'seconds'|'minutes'|'hours'|'days'

        response = self.client.create_user_pool_client(
            UserPoolId=f"{user_pool_id}",
            ClientName=f"{client_name}",
            GenerateSecret=True,
            RefreshTokenValidity=refresh_token_time_out,
            AccessTokenValidity=access_token_time_out,
            IdTokenValidity=id_token_time_out,
            TokenValidityUnits={
                "AccessToken": access_token_units,
                "IdToken": id_token_units,
                "RefreshToken": refresh_token_units,
            },
            # ReadAttributes=[
            #     'string',
            # ],
            # WriteAttributes=[
            #     'string',
            # ],
            # ExplicitAuthFlows=[
            #     'ADMIN_NO_SRP_AUTH'|'CUSTOM_AUTH_FLOW_ONLY'|'USER_PASSWORD_AUTH'|'ALLOW_ADMIN_USER_PASSWORD_AUTH'|'ALLOW_CUSTOM_AUTH'|'ALLOW_USER_PASSWORD_AUTH'|'ALLOW_USER_SRP_AUTH'|'ALLOW_REFRESH_TOKEN_AUTH',
            # ],
            # SupportedIdentityProviders=[
            #     'string',
            # ],
            # CallbackURLs=[
            #     'string',
            # ],
            # LogoutURLs=[
            #     'string',
            # ],
            # DefaultRedirectURI='string',
            AllowedOAuthFlows=["client_credentials"],
            AllowedOAuthScopes=[
                "string",
            ],
            AllowedOAuthFlowsUserPoolClient=True,
            # AnalyticsConfiguration={
            #     'ApplicationId': 'string',
            #     'ApplicationArn': 'string',
            #     'RoleArn': 'string',
            #     'ExternalId': 'string',
            #     'UserDataShared': True|False
            # },
            # PreventUserExistenceErrors='LEGACY'|'ENABLED',
            EnableTokenRevocation=True,
            # EnablePropagateAdditionalUserContextData=True|False,
            # AuthSessionValidity=123
        )

        return dict(response)

    def search_cognito(self, email: str, user_pool_id: str) -> dict:
        """Search cognito for an existing user"""

        email = self.__format_email(email=email) or ""
        filter_string = f'email = "{email}"'

        # Call the admin_list_users method with the filter
        response = self.client.list_users(UserPoolId=user_pool_id, Filter=filter_string)

        return dict(response)

    def __set_user_attributes(self, *, user: CognitoUser) -> List[dict]:
        """
        Constructs a list of user attributes for Cognito based on the provided user object.

        Args:
            user (CognitoUser): The user object containing attributes to set.

        Returns:
            List[dict]: A list of attribute dictionaries for Cognito.
        """
        user_attributes: List[Dict[str, Any]] = [
            {"Name": "email", "Value": str(user.email).lower()}
        ]

        user_attributes.append({"Name": "email_verified", "Value": "true"})

        if user.first_name is not None:
            user_attributes.append({"Name": "given_name", "Value": user.first_name})

        if user.last_name is not None:
            user_attributes.append({"Name": "family_name", "Value": user.last_name})

        if self.custom_attributes:
            if user.id is not None:
                user_attributes.append(
                    {
                        "Name": self.custom_attributes.user_id_custom_attribute,
                        "Value": user.id,
                    }
                )

            if user.roles is not None:
                roles: str = (
                    ",".join(user.roles) if isinstance(user.roles, list) else user.roles
                )
                user_attributes.append(
                    {
                        "Name": self.custom_attributes.user_roles_custom_attribute,
                        "Value": roles,
                    }
                )

            if user.tenant_id is not None:
                user_attributes.append(
                    {
                        "Name": self.custom_attributes.tenant_id_custom_attribute,
                        "Value": user.tenant_id,
                    }
                )

        return user_attributes

    def map(self, cognito_response: dict) -> CognitoUser:
        """Map the cognito response to a user object"""
        user = CognitoUser()
        # this is the internal Cognito ID that get's generated
        user.cognito_user_name = self.get_cognito_attribute(
            cognito_response, "Username"
        )
        user.email = self.get_cognito_attribute(cognito_response, "email", None)
        user.first_name = self.get_cognito_attribute(
            cognito_response, "given_name", None
        )
        user.last_name = self.get_cognito_attribute(
            cognito_response, "family_name", None
        )
        if self.custom_attributes:
            user.id = self.get_cognito_attribute(
                cognito_response, self.custom_attributes.user_id_custom_attribute, None
            )
            user.tenant_id = self.get_cognito_attribute(
                cognito_response,
                self.custom_attributes.tenant_id_custom_attribute,
                None,
            )

            roles: str | None | List[str] = self.get_cognito_attribute(
                cognito_response,
                self.custom_attributes.user_roles_custom_attribute,
                None,
            )
        else:
            user.id = self.get_cognito_attribute(cognito_response, "sub", None)
            roles = self.get_cognito_attribute(cognito_response, "cognito:groups", None)

        if roles is None:
            roles = []
        if isinstance(roles, str):
            roles = roles.split(",")
        user.roles = roles
        return user

    def get_cognito_attribute(
        self, response: dict, name: str, default: Optional[str] = None
    ) -> Optional[str]:
        if name in response:
            return response.get(name, default)

        attributes = response.get("Attributes", [])
        attribute = DictionaryUtilitiy.find_dict_by_name(attributes, "Name", name)
        if attribute and isinstance(attribute, list):
            return str(attribute[0].get("Value", default))
        return default

    def __format_email(self, email: str | None) -> str | None:
        """
        Formats an email address to be used in Cognito user pools. Converts to lowercase
        if self.auto_lower_case_email_addresses is set to true (the default)

        Args:
            email (str | None): The email address to format.

        Returns:
            str | None: The formatted email address, or None if input is None.
        """
        if self.auto_lower_case_email_addresses:
            return None if email is None else str(email).lower()
        return email
