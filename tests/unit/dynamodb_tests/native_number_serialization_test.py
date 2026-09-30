"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Native-number serialization tests.

``to_dictionary()`` is the app-facing serializer and MUST return native Python
numeric types (a ``float`` stays a ``float``; a ``Decimal`` becomes ``int`` for a
whole value / ``float`` for a fractional value), including numbers nested inside
``dict`` and ``list`` attributes. ``to_resource_dictionary()`` /
``to_client_dictionary()`` are DynamoDB-write serializers and MUST keep emitting
``Decimal`` / typed attribute maps.

This guards the fix for the bug where a fractional float stored as a DynamoDB
Number was returned to API clients as a string (because ``to_dictionary()``
converted ``float`` -> ``Decimal`` and the downstream ``json.dumps(default=str)``
stringified it).
"""

import datetime as dt
import json
import unittest
from decimal import Decimal
from typing import Any, Dict, Optional

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class ThemeLike(DynamoDBModelBase):
    """A model with a free-form nested map (like a plot theme's ``configuration``)
    plus a top-level float, to exercise numeric serialization at depth."""

    def __init__(self, id: Optional[str] = None):  # pylint: disable=redefined-builtin
        super().__init__(self)
        self.id: Optional[str] = id
        self.name: Optional[str] = None
        self.ratio: Optional[float] = None
        self.created: Optional[dt.datetime] = None
        self.configuration: Dict[str, Any] = {}
        self.__setup_indexes()

    def __setup_indexes(self):
        primary = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("theme", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("theme", self.id))
        self.indexes.add_primary(primary)


class NativeNumberSerializationUnitTest(unittest.TestCase):
    """to_dictionary() native numbers vs to_resource_dictionary() Decimal."""

    def _model(self) -> ThemeLike:
        m = ThemeLike(id="t-1")
        m.name = "Aplos Dark"
        m.ratio = 0.65
        m.configuration = {
            "grid": {
                "major_alpha": 0.65,  # fractional float
                "minor_alpha": 0.6,
                "whole": 2,  # native int
            },
            "series": [
                {"opacity": 0.25},  # fractional float nested in a list
                {"opacity": 1},  # native int nested in a list
            ],
        }
        return m

    # ---- to_dictionary(): native numbers -------------------------------------

    def test_to_dictionary_keeps_fractional_float(self):
        d = self._model().to_dictionary()
        value = d["configuration"]["grid"]["major_alpha"]
        self.assertIsInstance(value, float)
        self.assertNotIsInstance(value, Decimal)
        self.assertEqual(value, 0.65)

    def test_to_dictionary_top_level_float(self):
        d = self._model().to_dictionary()
        self.assertIsInstance(d["ratio"], float)
        self.assertEqual(d["ratio"], 0.65)

    def test_to_dictionary_nested_list_float(self):
        d = self._model().to_dictionary()
        opacity = d["configuration"]["series"][0]["opacity"]
        self.assertIsInstance(opacity, float)
        self.assertEqual(opacity, 0.25)

    def test_to_dictionary_native_int_preserved(self):
        d = self._model().to_dictionary()
        self.assertIsInstance(d["configuration"]["grid"]["whole"], int)
        self.assertEqual(d["configuration"]["grid"]["whole"], 2)
        self.assertIsInstance(d["configuration"]["series"][1]["opacity"], int)

    def test_to_dictionary_converts_decimal_attr_to_native(self):
        """A Decimal placed on the model (e.g. read from DynamoDB) becomes native
        via to_dictionary(): whole -> int, fractional -> float."""
        m = self._model()
        m.configuration = {
            "grid": {
                "major_alpha": Decimal("0.65"),  # fractional Decimal -> float
                "whole": Decimal("1"),  # whole Decimal -> int
                "whole_float": Decimal("1.0"),  # whole-valued Decimal -> int
            }
        }
        d = m.to_dictionary()
        grid = d["configuration"]["grid"]
        self.assertIsInstance(grid["major_alpha"], float)
        self.assertEqual(grid["major_alpha"], 0.65)
        self.assertIsInstance(grid["whole"], int)
        self.assertEqual(grid["whole"], 1)
        self.assertIsInstance(grid["whole_float"], int)
        self.assertEqual(grid["whole_float"], 1)

    def test_to_dictionary_is_json_number_not_string(self):
        """End goal: json.dumps of to_dictionary() emits a number, not a string."""
        d = self._model().to_dictionary()
        body = json.dumps(d)  # no default= needed; all native
        reparsed = json.loads(body)
        self.assertEqual(reparsed["configuration"]["grid"]["major_alpha"], 0.65)
        self.assertIsInstance(reparsed["configuration"]["grid"]["major_alpha"], float)

    # ---- to_resource_dictionary(): Decimal (DynamoDB write) ------------------

    def test_to_resource_dictionary_keeps_decimal(self):
        d = self._model().to_resource_dictionary(include_indexes=False)
        value = d["configuration"]["grid"]["major_alpha"]
        self.assertIsInstance(value, Decimal)
        self.assertEqual(value, Decimal("0.65"))

    def test_to_resource_dictionary_nested_list_decimal(self):
        d = self._model().to_resource_dictionary(include_indexes=False)
        self.assertIsInstance(d["configuration"]["series"][0]["opacity"], Decimal)

    def test_to_resource_dictionary_top_level_float_decimal(self):
        d = self._model().to_resource_dictionary(include_indexes=False)
        self.assertIsInstance(d["ratio"], Decimal)

    # ---- to_client_dictionary(): typed attribute map (unchanged) -------------

    def test_to_client_dictionary_still_number_attribute(self):
        # to_client_dictionary is DynamoDB-write-bound: the fractional value is
        # still represented as a Number ("N") attribute, never a plain String.
        # (We assert on the serialized form rather than a brittle nested path,
        # since the native-numbers change must NOT alter this serializer.)
        d = self._model().to_client_dictionary(include_indexes=False)
        # The top-level float is serialized as a Number attribute, unchanged.
        self.assertEqual(d["ratio"], {"N": "0.65"})

    # ---- non-numeric handling unchanged --------------------------------------

    def test_datetime_serializes_to_isoformat_in_both(self):
        m = self._model()
        m.created = dt.datetime(2026, 1, 2, 3, 4, 5)
        native = m.to_dictionary()
        resource = m.to_resource_dictionary(include_indexes=False)
        self.assertEqual(native["created"], "2026-01-02T03:04:05")
        self.assertEqual(resource["created"], "2026-01-02T03:04:05")


if __name__ == "__main__":
    unittest.main()
