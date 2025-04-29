"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Dict, List, Any
from boto3_assist.models.serializable_model import SerializableModel
from tests.unit.models_tests.models.user import User


class TestSerializableModel(unittest.TestCase):
    """Testing Serialzing Models"""

    def setUp(self) -> None:
        self.source_dict: Dict[str, Any] = {
            "first_name": "John",
            "last_name": "Doe",
            "meta_data": {
                "favorite_color": "blue",
                "favorite_food": "pizza",
                "favorite_movie": "The Matrix",
                "favorite_book": "The Lord of the Rings",
                "favorite_music": "Classic Rock",
                "favorite_hobby": "reading",
                "favorite_sport": "football",
                "favorite_tv_show": "The Office",
                "favorite_animal": "dog",
                "favorite_place": "home",
                "favorite_drink": "water",
            },
            "settings": {
                "notifications": True,
                "dark_mode": False,
                "language": "en",
                "timezone": "UTC",
            },
        }

    def test_map_valid_data(self):
        """
        Test mapping a valid dictionary to an object instance.
        """
        result = User().map(self.source_dict)

        self.assertEqual(result.first_name, "John")
        self.assertEqual(result.last_name, "Doe")
        self.assertEqual(len(result.meta_data), 11)
        self.assertEqual(len(result.settings), 4)


if __name__ == "__main__":
    unittest.main()
