"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from datetime import datetime, UTC
from datetime import timedelta
from typing import cast

from boto3_assist.utilities.string_utility import StringUtility
import uuid


class StringUtilityUnitTest(unittest.TestCase):
    "String Utility Tests"

    def test_uuid_idempotency(self):
        """Testing Idempotnent UUID generation."""
        # must be consistent
        namespace: uuid.UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

        idempotent_id_john_smith: str = StringUtility.generate_idempotent_uuid(
            str(namespace), "tenant-one:john.smith@tenant-one.com"
        )

        # should always get this GUID
        self.assertEqual(
            idempotent_id_john_smith, "3e68597f-3a32-5f82-a028-010f34eccfe6"
        )

        idempotent_id_john_smith_camel: str = StringUtility.generate_idempotent_uuid(
            namespace, "tenant-one:John.Smith@tenant-one.com", case_sensitive=True
        )

        # should always get this GUID
        self.assertEqual(
            idempotent_id_john_smith_camel, "06daa067-77e1-56c1-80d5-8ee8306d0298"
        )

        idempotent_id_john_smith_case_insensitive: str = (
            StringUtility.generate_idempotent_uuid(
                namespace,
                "tenant-one:John.Smith@tenant-one.com",
                case_sensitive=False,
            )
        )
        self.assertEqual(
            idempotent_id_john_smith_case_insensitive,
            "3e68597f-3a32-5f82-a028-010f34eccfe6",
        )

        self.assertEqual(
            idempotent_id_john_smith, idempotent_id_john_smith_case_insensitive
        )
