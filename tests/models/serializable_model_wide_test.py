"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest

from boto3_assist.models.serializable_model import SerializableModel
from boto3_assist.utilities.serialization_utility import Serialization


class Address(SerializableModel):
    """A model that inherits the serializable"""

    def __init__(
        self,
        *,
        id: str | None = None,  # pylint: disable=redefined-builtin
        street: str | None = None,
        city: str | None = None,
        state: str | None = None,
        zip: str | None = None,  # pylint: disable=redefined-builtin
    ):
        self.id: str | None = id
        self.street: str | None = street
        self.city: str | None = city
        self.state: str | None = state
        self.zip: str | None = zip


class User(SerializableModel):
    """A model that inherits the serializable"""

    def __init__(self):
        self.__id: str | None = None
        self.first_name: str = ""
        self.last_name: str = ""
        self.addresses: list[Address] = []

    @property
    def id(self) -> str:
        """The id of the order"""
        return self.__id

    @id.setter
    def id(self, value: str) -> None:
        self.__id = value


class TestSerializableModel(unittest.TestCase):
    """Testing Serialzing Models"""

    def setUp(self) -> None:
        pass

    def test_map_valid_data(self):
        """
        Test mapping a valid dictionary to an object instance.
        """
        user: User = User()
        user.id = "1"
        user.first_name = "John"
        user.last_name = "Smith"
        for i in range(3):
            user.addresses.append(
                Address(
                    id=str(i),
                    street=f"10{i} S. Main St.",
                    city="Anytown",
                    state="AnyWhere",
                    zip="00001",
                )
            )

        flat = user.to_wide_dictionary()

        self.assertIsNotNone(flat)
        self.assertEqual(flat["id"], "1")
        self.assertEqual(flat["first_name"], "John")
        self.assertEqual(flat["last_name"], "Smith")
        self.assertEqual(flat["addresses_0_id"], "0")
        self.assertEqual(flat["addresses_0_street"], "100 S. Main St.")
        self.assertEqual(flat["addresses_0_city"], "Anytown")
        self.assertEqual(flat["addresses_0_state"], "AnyWhere")
        self.assertEqual(flat["addresses_0_zip"], "00001")

    def test_dict_wide(self):
        model = {
            "id": "1",
            "first_name": "John",
            "last_name": "Smith",
            "addresses": [
                {
                    "id": "0",
                    "street": "100 S. Main St.",
                    "city": "Anytown",
                    "state": "AnyWhere",
                    "zip": "00001",
                },
                {
                    "id": "1",
                    "street": "101 S. Main St.",
                    "city": "Anytown",
                    "state": "AnyWhere",
                    "zip": "00001",
                },
            ],
        }

        flat = Serialization.to_wide_dictionary(model)

        self.assertIsNotNone(flat)
        self.assertEqual(flat["id"], "1")
        self.assertEqual(flat["first_name"], "John")
        self.assertEqual(flat["last_name"], "Smith")
        self.assertEqual(flat["addresses_0_id"], "0")
        self.assertEqual(flat["addresses_0_street"], "100 S. Main St.")
        self.assertEqual(flat["addresses_0_city"], "Anytown")
        self.assertEqual(flat["addresses_0_state"], "AnyWhere")
        self.assertEqual(flat["addresses_0_zip"], "00001")

    def test_dict_multi_level_array(self):
        model = {
            "id": "1",
            "level_one_array": [
                {
                    "id": "1",
                    "level_two_array": [
                        {
                            "id": "1",
                            "level_three_array": [
                                {
                                    "id": "1",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        flat = Serialization.to_wide_dictionary(model)

        self.assertIsNotNone(flat)
        self.assertEqual(flat["id"], "1")
        self.assertEqual(flat["level_one_array_0_id"], "1")
        self.assertEqual(flat["level_one_array_0_level_two_array_0_id"], "1")
        self.assertEqual(
            flat["level_one_array_0_level_two_array_0_level_three_array_0_id"], "1"
        )

    def test_dict_wide_list_happy_path(self):
        model = {
            "first_name": "John",
            "last_name": "Smith",
            "addresses": [
                {
                    "street": "100 S. Main St.",
                    "city": "Anytown",
                    "state": "AnyWhere",
                    "zip": "00001",
                },
                {
                    "street": "101 S. Main St.",
                    "city": "Anytown",
                    "state": "AnyWhere",
                    "zip": "00001",
                },
            ],
        }

        expected_results = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "street": "100 S. Main St.",
                "city": "Anytown",
                "state": "AnyWhere",
                "zip": "00001",
            },
            {
                "first_name": "John",
                "last_name": "Smith",
                "street": "101 S. Main St.",
                "city": "Anytown",
                "state": "AnyWhere",
                "zip": "00001",
            },
        ]

        flat = Serialization.to_wide_dictionary_list(model)

        self.assertIsNotNone(flat)
        self.assertEqual(flat, expected_results)

    def test_dict_wide_list_duplicate_keys(self):
        model = {
            "id": "1",
            "first_name": "John",
            "last_name": "Smith",
            "addresses": [
                {
                    "id": "a",
                    "street": "100 S. Main St.",
                    "city": "Anytown",
                    "state": "AnyWhere",
                    "zip": "00001",
                },
                {
                    "id": "b",
                    "street": "101 S. Main St.",
                    "city": "Anytown",
                    "state": "AnyWhere",
                    "zip": "00001",
                },
            ],
        }

        expected_results = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "street": "100 S. Main St.",
                "city": "Anytown",
                "state": "AnyWhere",
                "zip": "00001",
            },
            {
                "first_name": "John",
                "last_name": "Smith",
                "street": "101 S. Main St.",
                "city": "Anytown",
                "state": "AnyWhere",
                "zip": "00001",
            },
        ]

        flat = Serialization.to_wide_dictionary_list(model)

        self.assertIsNotNone(flat)
        self.assertEqual(flat, expected_results)


if __name__ == "__main__":
    unittest.main()
