"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import unittest
from typing import Any, Dict, Optional

from boto3_assist.dynamodb.dynamodb_model_base import CLEAR_FIELD, DynamoDBModelBase, MergeStrategy


class SimpleModel(DynamoDBModelBase):
    """Simple test model for merge testing."""

    def __init__(self):
        super().__init__()
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.price: Optional[float] = None
        self.quantity: Optional[int] = None
        self.is_active: Optional[bool] = None
        self.metadata: Optional[Dict[str, Any]] = None


class NestedModel(DynamoDBModelBase):
    """Model with nested objects for testing deep merge."""

    def __init__(self):
        super().__init__()
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.settings: Dict[str, Any] = {}
        self.address: Optional[Dict[str, str]] = None


class DynamoDBModelMergeTest(unittest.TestCase):
    """Tests for the merge() method on DynamoDBModelBase."""

    # =========================================================================
    # NON_NULL_WINS Strategy Tests (Default)
    # =========================================================================

    def test_merge_non_null_wins_updates_non_null_fields(self):
        """Non-null values in updates should overwrite existing values."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original Name"
        existing.description = "Original Description"
        existing.price = 10.0

        updates = {"name": "Updated Name", "price": 25.0}

        # Act
        existing.merge(updates)

        # Assert
        self.assertEqual(existing.name, "Updated Name")
        self.assertEqual(existing.price, 25.0)
        self.assertEqual(existing.description, "Original Description")  # unchanged
        self.assertEqual(existing.id, "123")  # unchanged

    def test_merge_non_null_wins_ignores_none_values(self):
        """None values in updates should NOT overwrite existing values."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original Name"
        existing.price = 10.0

        updates = {"name": None, "price": None, "description": "New Description"}

        # Act
        existing.merge(updates)

        # Assert
        self.assertEqual(existing.name, "Original Name")  # unchanged
        self.assertEqual(existing.price, 10.0)  # unchanged
        self.assertEqual(existing.description, "New Description")  # updated

    def test_merge_non_null_wins_with_clear_field_sentinel(self):
        """CLEAR_FIELD sentinel should explicitly set field to None."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original Name"
        existing.description = "Original Description"

        updates = {"description": CLEAR_FIELD}

        # Act
        existing.merge(updates)

        # Assert
        self.assertEqual(existing.name, "Original Name")  # unchanged
        self.assertIsNone(existing.description)  # explicitly cleared

    def test_merge_non_null_wins_fills_none_fields(self):
        """Updates should fill in fields that are currently None."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = None
        existing.price = None

        updates = {"name": "New Name", "price": 15.0}

        # Act
        existing.merge(updates)

        # Assert
        self.assertEqual(existing.name, "New Name")
        self.assertEqual(existing.price, 15.0)

    # =========================================================================
    # UPDATES_WIN Strategy Tests
    # =========================================================================

    def test_merge_updates_win_overwrites_everything(self):
        """UPDATES_WIN should overwrite all fields, including with None."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original Name"
        existing.description = "Original Description"
        existing.price = 10.0

        updates = {"name": "Updated Name", "description": None, "price": 25.0}

        # Act
        existing.merge(updates, strategy=MergeStrategy.UPDATES_WIN)

        # Assert
        self.assertEqual(existing.name, "Updated Name")
        self.assertIsNone(existing.description)  # overwritten with None
        self.assertEqual(existing.price, 25.0)
        self.assertEqual(existing.id, "123")  # not in updates, unchanged

    def test_merge_updates_win_with_all_none(self):
        """UPDATES_WIN with all None values should clear those fields."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"
        existing.description = "Description"

        updates = {"name": None, "description": None}

        # Act
        existing.merge(updates, strategy=MergeStrategy.UPDATES_WIN)

        # Assert
        self.assertIsNone(existing.name)
        self.assertIsNone(existing.description)

    # =========================================================================
    # EXISTING_WINS Strategy Tests
    # =========================================================================

    def test_merge_existing_wins_only_fills_gaps(self):
        """EXISTING_WINS should only update fields that are currently None."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original Name"
        existing.description = None
        existing.price = None

        updates = {
            "name": "Should Not Change",
            "description": "New Description",
            "price": 20.0,
        }

        # Act
        existing.merge(updates, strategy=MergeStrategy.EXISTING_WINS)

        # Assert
        self.assertEqual(existing.name, "Original Name")  # unchanged
        self.assertEqual(existing.description, "New Description")  # filled
        self.assertEqual(existing.price, 20.0)  # filled

    def test_merge_existing_wins_ignores_all_when_populated(self):
        """EXISTING_WINS should not change anything if all fields are populated."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original"
        existing.description = "Original Desc"
        existing.price = 10.0

        updates = {"name": "New", "description": "New Desc", "price": 99.0}

        # Act
        existing.merge(updates, strategy=MergeStrategy.EXISTING_WINS)

        # Assert
        self.assertEqual(existing.name, "Original")
        self.assertEqual(existing.description, "Original Desc")
        self.assertEqual(existing.price, 10.0)

    def test_merge_existing_wins_with_clear_field(self):
        """CLEAR_FIELD should still work with EXISTING_WINS strategy."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"
        existing.description = "Original Desc"

        updates = {"description": CLEAR_FIELD}

        # Act
        existing.merge(updates, strategy=MergeStrategy.EXISTING_WINS)

        # Assert
        self.assertIsNone(existing.description)  # CLEAR_FIELD always works

    # =========================================================================
    # Field Filtering Tests
    # =========================================================================

    def test_merge_with_include_fields(self):
        """Only specified include_fields should be considered for merge."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"
        existing.description = "Original Desc"
        existing.price = 10.0

        updates = {"name": "New Name", "description": "New Desc", "price": 99.0}

        # Act
        existing.merge(updates, include_fields=["name", "price"])

        # Assert
        self.assertEqual(existing.name, "New Name")  # included
        self.assertEqual(existing.description, "Original Desc")  # not included
        self.assertEqual(existing.price, 99.0)  # included

    def test_merge_with_exclude_fields(self):
        """Specified exclude_fields should be skipped during merge."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original"
        existing.description = "Original Desc"
        existing.price = 10.0

        updates = {
            "id": "999",
            "name": "New Name",
            "description": "New Desc",
            "price": 99.0,
        }

        # Act
        existing.merge(updates, exclude_fields=["id", "price"])

        # Assert
        self.assertEqual(existing.id, "123")  # excluded
        self.assertEqual(existing.name, "New Name")  # updated
        self.assertEqual(existing.description, "New Desc")  # updated
        self.assertEqual(existing.price, 10.0)  # excluded

    def test_merge_with_both_include_and_exclude(self):
        """Both include and exclude can be used together."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"
        existing.description = "Original Desc"
        existing.price = 10.0
        existing.quantity = 5

        updates = {
            "name": "New",
            "description": "New Desc",
            "price": 99.0,
            "quantity": 100,
        }

        # Act - include name, description, price but exclude price
        existing.merge(
            updates,
            include_fields=["name", "description", "price"],
            exclude_fields=["price"],
        )

        # Assert
        self.assertEqual(existing.name, "New")  # included, not excluded
        self.assertEqual(existing.description, "New Desc")  # included, not excluded
        self.assertEqual(existing.price, 10.0)  # included but also excluded
        self.assertEqual(existing.quantity, 5)  # not included

    # =========================================================================
    # Nested Object/Dict Tests
    # =========================================================================

    def test_merge_nested_dict_non_null_wins(self):
        """Nested dicts should be recursively merged with NON_NULL_WINS."""
        # Arrange
        existing = NestedModel()
        existing.settings = {"theme": "dark", "language": "en", "notifications": True}

        updates = {"settings": {"theme": "light", "language": None}}

        # Act
        existing.merge(updates)

        # Assert
        self.assertEqual(existing.settings["theme"], "light")  # updated
        self.assertEqual(existing.settings["language"], "en")  # None ignored
        self.assertEqual(existing.settings["notifications"], True)  # unchanged

    def test_merge_nested_dict_updates_win(self):
        """UPDATES_WIN should replace entire nested dict."""
        # Arrange
        existing = NestedModel()
        existing.settings = {"theme": "dark", "language": "en"}

        updates = {"settings": {"theme": "light"}}

        # Act
        existing.merge(updates, strategy=MergeStrategy.UPDATES_WIN)

        # Assert
        self.assertEqual(existing.settings, {"theme": "light"})

    def test_merge_with_none_updates(self):
        """Passing None as updates should return self unchanged."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"

        # Act
        result = existing.merge(None)

        # Assert
        self.assertEqual(result.name, "Original")
        self.assertIs(result, existing)

    # =========================================================================
    # Model-to-Model Merge Tests
    # =========================================================================

    def test_merge_from_another_model(self):
        """Should be able to merge from another DynamoDBModelBase instance."""
        # Arrange
        existing = SimpleModel()
        existing.id = "123"
        existing.name = "Original"
        existing.description = "Original Desc"

        updates_model = SimpleModel()
        updates_model.name = "Updated Name"
        updates_model.price = 50.0

        # Act
        existing.merge(updates_model)

        # Assert
        self.assertEqual(existing.name, "Updated Name")
        self.assertEqual(existing.description, "Original Desc")  # unchanged
        self.assertEqual(existing.price, 50.0)

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_merge_ignores_unknown_fields(self):
        """Fields not on the model should be ignored."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"

        updates = {"name": "Updated", "unknown_field": "value", "another_unknown": 123}

        # Act
        existing.merge(updates)

        # Assert
        self.assertEqual(existing.name, "Updated")
        self.assertFalse(hasattr(existing, "unknown_field"))
        self.assertFalse(hasattr(existing, "another_unknown"))

    def test_merge_returns_self(self):
        """Merge should return self for method chaining."""
        # Arrange
        existing = SimpleModel()

        # Act
        result = existing.merge({"name": "Test"})

        # Assert
        self.assertIs(result, existing)

    def test_merge_with_empty_dict(self):
        """Merging empty dict should not change anything."""
        # Arrange
        existing = SimpleModel()
        existing.name = "Original"
        existing.price = 10.0

        # Act
        existing.merge({})

        # Assert
        self.assertEqual(existing.name, "Original")
        self.assertEqual(existing.price, 10.0)

    def test_clear_field_repr(self):
        """CLEAR_FIELD should have a readable repr."""
        self.assertEqual(repr(CLEAR_FIELD), "CLEAR_FIELD")

    def test_clear_field_is_singleton(self):
        """CLEAR_FIELD should be a singleton."""
        from boto3_assist.dynamodb.dynamodb_model_base import _ClearFieldSentinel

        another = _ClearFieldSentinel()
        self.assertIs(CLEAR_FIELD, another)


if __name__ == "__main__":
    unittest.main()
