"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import time
from typing import Any, Dict, List

import jwt  # PyJWT
from aws_lambda_powertools import Logger
from jwt import InvalidTokenError, PyJWKClient

from boto3_assist.boto3session import Boto3SessionManager
from boto3_assist.cognito.jwks_cache import JwksCache

logger = Logger()

jwks_cache = JwksCache()


class CognitoCustomAuthorizer:
    """Cognito Custom Authorizer"""

    def __init__(self):
        self.__client_connections: Dict[str, Any] = {}

    def __get_client_connection(
        self, user_pool_id: str, refresh_client: bool = False
    ) -> Any:
        """Get the client connection to cognito"""
        region = user_pool_id.split("_")[0]
        client = self.__client_connections.get(region)
        if refresh_client:
            client = None
        if not client:
            session = Boto3SessionManager(service_name="cognito-idp", aws_region=region)
            client = session.client
            # boto3.client("cognito-idp", region_name=region)
            self.__client_connections[region] = client

        return client

    def generate_policy(
        self, user_pools: str | List[str], event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates the policy for the authorizer"""

        token = event["authorizationToken"]
        user_pools = self.__to_list(user_pools=user_pools)
        for user_pool_id in user_pools:
            try:
                if not user_pool_id:
                    continue
                # up_id = self.__to_id(user_pool_id=user_pool_id)
                # Decode the token, assuming RS256 (used by Cognito)
                # decoded_token = self.decode_jwt(token=token, user_pool_id=up_id)
                issuer = self.build_issuer_url(user_pool_id)
                claims = self.decode_jwt(token, issuer)
                # Token is valid, return an IAM policy
                return self.__generate_policy_doc(
                    principal_id=claims["sub"],
                    effect="Allow",
                    method_arn=event["methodArn"],
                )

            except InvalidTokenError as e:
                # Token is not valid for this user pool, try the next one
                logger.debug(str(e))
                continue
            except Exception as e:  # pylint: disable=w0718
                logger.error(str(e))

        # if we get here we deny it
        return self.__generate_policy_doc(
            principal_id="user",
            effect="Deny",
            method_arn=event["methodArn"],
        )

    def __generate_policy_doc(self, *, principal_id, effect, method_arn):
        """Generate the policy doc"""
        auth_response: Dict[str, Any] = {"principalId": principal_id}

        if effect and method_arn:
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": effect,
                        "Resource": method_arn,
                    }
                ],
            }
            auth_response["policyDocument"] = policy_document

        return auth_response

    def build_issuer_url(self, user_pool_id: str) -> str:
        """Build the issuer URL"""

        # Extract region from user pool ID format, e.g., "us-east-1_ABC123"
        region = user_pool_id.split("_")[0]
        return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

    def __to_list(self, user_pools: str | List[str]) -> List[str]:
        if isinstance(user_pools, str):
            user_pools = str(user_pools).replace(";", ",").replace(" ", "")
            user_pools = str(user_pools).split(",")
        elif isinstance(user_pools, list):
            pass
        else:
            logger.warning(
                f"Missing/ Invalid user pool: {user_pools}, type: {type(user_pools)}"
            )

        return user_pools

    def parse_jwt(self, token: str) -> dict:
        """Parse the JWT"""
        if "Bearer" in token:
            token = token.replace("Bearer ", "")

        decoded_jwt: dict = jwt.decode(token, options={"verify_signature": False})

        return decoded_jwt

    def decode_jwt(self, token: str, issuer) -> dict:
        """Decode the JWT"""
        # Get the public keys
        # Get the JWKS client
        jwks_client = self.get_jwks_client(issuer)
        if "Bearer" in token:
            token = token.replace("Bearer ", "")
        # Fetch the signing key using the PyJWKClient
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify the token
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            # audience=user_pool_id,
            issuer=issuer,
            options={"verify_aud": False},  # Disable audience verification
        )

        # Optional claim checks
        if claims["token_use"] != "id":
            # we are currently only using ID tokens
            raise RuntimeError("Not an id token")

        return claims

    def get_jwks_client(self, issuer) -> PyJWKClient:
        """Get the JWT Client"""
        if (
            issuer in jwks_cache.cache
            and (time.time() - jwks_cache.cache.get(issuer, {})["timestamp"]) < 3600
        ):
            # Return cached JWKS client if it’s less than an hour old
            return jwks_cache.cache[issuer]["client"]
        else:
            # Create a new PyJWKClient and cache it
            jwks_url = f"{issuer}/.well-known/jwks.json"
            jwks_client = PyJWKClient(jwks_url)
            jwks_cache.cache[issuer] = {"client": jwks_client, "timestamp": time.time()}
            return jwks_client
