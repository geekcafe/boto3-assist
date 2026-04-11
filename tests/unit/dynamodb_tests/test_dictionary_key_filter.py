"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests for the dictionary key filter feature on DynamoDBModelBase.
"""

import unittest

from tests.unit.dynamodb_tests.db_models.user_model import User


class TestDictionaryKeyFilter(unittest.TestCase):
    """Unit tests for the keys parameter on to_dictionary and to_dict."""

    def _make_user(self) -> User:
        """Create a populated User instance for testing."""
        data = {
            "id": "u-001",
            "first_name": "Alice",
            "last_name": "Smith",
            "age": 30,
            "email": "alice@example.com",
            "status": "active",
        }
        return User().map(data)

    # --- Requirement 1.1: non-empty keys returns only those fields ---

    def test_to_dictionary_with_specific_keys(self):
        """to_dictionary(keys=[...]) returns exactly the requested fields."""
        user = self._make_user()
        result = user.to_dictionary(keys=["id", "first_name"])

        self.assertEqual(set(result.keys()), {"id", "first_name"})
        self.assertEqual(result["id"], "u-001")
        self.assertEqual(result["first_name"], "Alice")

    # --- Requirement 1.2: nonexistent keys silently omitted ---

    def test_to_dictionary_with_nonexistent_key(self):
        """to_dictionary(keys=["nonexistent"]) returns {}."""
        user = self._make_user()
        result = user.to_dictionary(keys=["nonexistent"])

        self.assertEqual(result, {})

    # --- Requirement 1.4: empty list returns empty dict ---

    def test_to_dictionary_with_empty_keys(self):
        """to_dictionary(keys=[]) returns {}."""
        user = self._make_user()
        result = user.to_dictionary(keys=[])

        self.assertEqual(result, {})

    # --- Requirement 1.3: None / omitted keys returns full dict ---

    def test_to_dictionary_without_keys_returns_full_dict(self):
        """to_dictionary() with no keys arg returns the full dictionary."""
        user = self._make_user()
        full_dict = user.to_dictionary()

        # Should contain all user fields
        self.assertIn("id", full_dict)
        self.assertIn("first_name", full_dict)
        self.assertIn("last_name", full_dict)
        self.assertIn("age", full_dict)
        self.assertIn("email", full_dict)
        self.assertIn("status", full_dict)

        # Verify it matches calling with keys=None explicitly
        self.assertEqual(full_dict, user.to_dictionary(keys=None))

    # --- Requirements 2.2, 2.3: to_dict delegates to to_dictionary ---

    def test_to_dict_matches_to_dictionary_with_keys(self):
        """to_dict(keys=...) matches to_dictionary(keys=...)."""
        user = self._make_user()
        keys = ["id", "email"]

        self.assertEqual(
            user.to_dict(keys=keys),
            user.to_dictionary(keys=keys),
        )

    def test_to_dict_matches_to_dictionary_without_keys(self):
        """to_dict() matches to_dictionary() when no keys provided."""
        user = self._make_user()

        self.assertEqual(user.to_dict(), user.to_dictionary())

    # --- include_none interaction ---

    def test_include_none_false_with_none_field_key(self):
        """to_dictionary(include_none=False, keys=["field_that_is_none"]) returns {}."""
        user = self._make_user()
        # last_name is set, but let's use a field that is None
        user.status = None
        result = user.to_dictionary(include_none=False, keys=["status"])

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
