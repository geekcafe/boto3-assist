"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional, Literal

from botocore.exceptions import ClientError
from boto3_assist.ssm.connection import SSMConnection


class ParameterStore(SSMConnection):
    """Parameter Store"""

    def get_parameter(self, name: str, with_decryption=True):
        """
        Retrieve a parameter from Parameter Store.

        :param name: The full name of the parameter.
        :param with_decryption: If True, decrypt secure strings.
        :return: The parameter value or None if an error occurs.
        """
        try:
            response = self.client.get_parameter(
                Name=name, WithDecryption=with_decryption
            )
            return response["Parameter"]["Value"]
        except ClientError as e:
            print(f"Error getting parameter {name}: {e}")
            raise

    def put_parameter(
        self,
        name: str,
        value: str,
        type: Literal["String", "StringList", "SecureString"] = "String",  # pylint: disable=redefined-builtin
        overwrite=True,
    ):
        """
        Create or update a parameter in Parameter Store.

        :param name: The full name of the parameter.
        :param value: The value to store.
        :param type: Parameter type ('String', 'StringList', or 'SecureString').
        :param overwrite: If True, overwrite an existing parameter.
        :return: The response from the put_parameter call or None on error.
        """
        try:
            response = self.client.put_parameter(
                Name=name, Value=value, Type=type, Overwrite=overwrite
            )
            return response
        except ClientError as e:
            print(f"Error putting parameter {name}: {e}")
            raise

    def delete_parameter(self, name: str):
        """
        Delete a parameter from Parameter Store.

        :param name: The full name of the parameter.
        :return: The response from the delete_parameter call or None on error.
        """
        try:
            response = self.client.delete_parameter(Name=name)
            return response
        except ClientError as e:
            print(f"Error deleting parameter {name}: {e}")
            raise

    def list_parameters(self, path: str = "/", recursive=True):
        """
        List parameters in a given path.

        :param path: The hierarchical path for the parameters.
        :param recursive: If True, retrieve parameters recursively.
        :return: A list of parameter metadata dictionaries.
        """
        try:
            paginator = self.client.get_paginator("describe_parameters")
            parameters = []
            filters = [
                {
                    "Key": "Path",
                    "Option": "Recursive" if recursive else "OneLevel",
                    "Values": [path],
                }
            ]
            for page in paginator.paginate(ParameterFilters=filters):
                parameters.extend(page.get("Parameters", []))
            return parameters
        except ClientError as e:
            print(f"Error listing parameters for path {path}: {e}")
            raise


# Example usage:
if __name__ == "__main__":
    # Initialize the ParameterStore class.
    ssm = ParameterStore()
    # Example: Put a parameter.
    put_response = ssm.put_parameter("/myapp/AccountNumber", "123456789012")
    print("Put parameter response:", put_response)

    # Example: Get a parameter.
    account_number = ssm.get_parameter("/myapp/AccountNumber")
    print("Account Number:", account_number)

    # Example: List parameters under /myapp.
    params = ssm.list_parameters(path="/myapp")
    print("Parameters under /myapp:", params)

    # Example: Delete a parameter.
    delete_response = ssm.delete_parameter("/myapp/AccountNumber")
    print("Delete parameter response:", delete_response)
