"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Dict, List
from boto3_assist.models.serializable_model import SerializableModel
from tests.unit.models_tests.models.person import Person


class TestSerializableModel(unittest.TestCase):
    """Testing Serialzing Models"""

    def setUp(self) -> None:
        self.source_dict: Dict[str, any] = {
            "name": "John Doe",
            "age": 30,
            "active": True,
            "pets": ["abby", "lexie", "lena", "keisha"],
        }

    def test_map_valid_data(self):
        """
        Test mapping a valid dictionary to an object instance.
        """
        result = Person().map(self.source_dict)

        self.assertEqual(result.name, "John Doe")
        self.assertEqual(result.age, 30)
        self.assertEqual(result.active, True)
        self.assertEqual(len(result.pets), 4)

    def test_map_partial_data(self):
        """
        Test mapping a dictionary with partial data.
        """
        partial_dict = {"name": "Jane Doe"}
        result = Person().map(partial_dict)

        self.assertEqual(result.name, "Jane Doe")
        self.assertEqual(result.age, 0)  # Default value
        self.assertEqual(result.active, False)  # Default value

    def test_map_empty_data(self):
        """
        Test mapping an empty dictionary.
        """
        empty_dict = {}
        result = Person().map(empty_dict)

        self.assertEqual(result.name, "")  # Default value
        self.assertEqual(result.age, 0)  # Default value
        self.assertEqual(result.active, False)  # Default value

    def test_map_invalid_data(self):
        """
        Test mapping a dictionary with invalid data types.
        """
        invalid_dict = {"name": 123, "age": "thirty", "active": "yes"}

        with self.assertRaises(ValueError):
            Person().map(invalid_dict, coerce=False)

    def test_map_invalid_data_coerce_with_failure(self):
        """
        Test mapping a dictionary with invalid data types.
        """
        invalid_dict = {"name": 123, "age": "thirty", "active": "yes"}

        result = Person().map(invalid_dict)

        self.assertEqual(result.name, "123")
        # currently we're allowing this to happen
        self.assertEqual(result.age, "thirty")
        self.assertEqual(result.active, True)

    def test_map_invalid_data_coerce(self):
        """
        Test mapping a dictionary with invalid data types.
        """
        invalid_dict = {"name": 123, "age": 30, "active": "yes"}

        result = Person().map(invalid_dict)

        self.assertEqual(result.name, "123")
        self.assertEqual(result.age, 30)
        self.assertEqual(result.active, True)

    def test_map_mix_limited_fields(self):
        """
        Test mapping a dictionary with invalid data types.
        """
        model: Person = Person(name="Fred", age=25, active=True)
        invalid_dict = {"age": 30}

        result = model.map(invalid_dict)

        self.assertEqual(result.name, "Fred")
        self.assertEqual(result.age, 30)
        self.assertEqual(result.active, True)

    def test_map_non_dict_source(self):
        """
        Test mapping from a non-dictionary source object.
        """
        source_object = Person(name="Alice", age=25, active=True)

        result = Person().map(source_object)

        self.assertEqual(result.name, "Alice")
        self.assertEqual(result.age, 25)
        self.assertEqual(result.active, True)

    def test_to_dictionary(self):
        """
        Test converting an object instance to a dictionary.
        """
        model = Person(name="Bob", age=35, active=False)

        result = model.to_dictionary()

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 4)
        self.assertEqual(result.get("name"), "Bob")
        self.assertEqual(result.get("age"), 35)
        self.assertEqual(result.get("active"), False)


if __name__ == "__main__":
    unittest.main()
