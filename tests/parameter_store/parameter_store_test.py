"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest

import moto

from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.ssm.parameter_store.parameter_store import ParameterStore


@moto.mock_aws
class ParameterStoreTest(unittest.TestCase):
    """Parameter store tests - with mocking"""

    def setUp(self):
        """Setup"""
        ev: EnvironmentLoader = EnvironmentLoader()
        # NOTE: you need to make sure the the env file below exists or you will get an error
        # this also requires the @moto.mock_aws decorator
        ev.load_environment_file(file_name=".env.unittest")
        # ev.load_environment_file(file_name=".env")

    def test_get_parameter(self):
        parameter_store = ParameterStore()
        parameter_name = "/dev/test"
        parameter_value = "test_1"

        parameter_store.put_parameter(parameter_name, parameter_value)
        response = parameter_store.get_parameter(parameter_name)

        self.assertEqual(response, parameter_value)
