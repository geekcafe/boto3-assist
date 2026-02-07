"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from __future__ import annotations

import datetime as dt
from enum import Enum

# import decimal
# import inspect
# import uuid
from typing import Any, Dict, List, Set, TypeVar

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

from boto3_assist.dynamodb.dynamodb_helpers import DynamoDBHelpers
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBIndexes
from boto3_assist.dynamodb.dynamodb_reserved_words import DynamoDBReservedWords
from boto3_assist.models.serializable_model import SerializableModel
from boto3_assist.utilities.datetime_utility import DatetimeUtility
from boto3_assist.utilities.decimal_conversion_utility import DecimalConversionUtility
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.utilities.string_utility import StringUtility


class MergeStrategy(Enum):
    """Strategy for merging updates into an existing model."""

    NON_NULL_WINS = "non_null_wins"
    """Only overwrite if the update value is not None (default, most common)."""

    UPDATES_WIN = "updates_win"
    """Update values always win, even if None."""

    EXISTING_WINS = "existing_wins"
    """Only fill in fields that are currently None in the existing model."""


class _ClearFieldSentinel:
    """Sentinel class to explicitly mark a field for clearing to None."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "CLEAR_FIELD"


# Singleton sentinel value - use this to explicitly clear a field to None
CLEAR_FIELD = _ClearFieldSentinel()


def exclude_from_serialization(method):
    """
    Decorator to mark methods or properties to be excluded from serialization.
    """
    method.exclude_from_serialization = True
    return method


def exclude_indexes_from_serialization(method):
    """
    Decorator to mark methods or properties to be excluded from serialization.
    """
    method.exclude_indexes_from_serialization = True
    return method


class DynamoDBModelBase(SerializableModel):
    """DynamoDb Model Base"""

    T = TypeVar("T", bound="DynamoDBModelBase")

    def __init__(self, auto_generate_projections: bool = True) -> None:
        self.__projection_expression: str | None = None
        self.__projection_expression_attribute_names: dict | None = None
        self.__helpers: DynamoDBHelpers | None = None
        self.__indexes: DynamoDBIndexes | None = None
        self.__reserved_words: DynamoDBReservedWords = DynamoDBReservedWords()
        self.__auto_generate_projections: bool = auto_generate_projections
        self.__actively_serializing_data__: bool = False

    def serialization_in_progress(self) -> bool:
        return self.__actively_serializing_data__

    @property
    @exclude_from_serialization
    def indexes(self) -> DynamoDBIndexes:
        """Gets the indexes"""
        # although this is marked as excluded, the indexes are add
        # but in a more specialized way
        if self.__indexes is None:
            self.__indexes = DynamoDBIndexes()
        return self.__indexes

    @property
    @exclude_from_serialization
    def projection_expression(self) -> str | None:
        """Gets the projection expression"""
        prop_list: List[str] = []
        if self.__projection_expression is None and self.auto_generate_projections:
            props = self.to_dictionary()
            # turn props to a list[str]
            prop_list = list(props.keys())
        else:
            if self.__projection_expression:
                prop_list = self.__projection_expression.split(",")
                prop_list = [p.strip() for p in prop_list]

        if len(prop_list) == 0:
            return None

        transformed_list = self.__reserved_words.tranform_projections(prop_list)
        self.projection_expression = ",".join(transformed_list)

        return self.__projection_expression

    @projection_expression.setter
    def projection_expression(self, value: str | None):
        self.__projection_expression = value

    @property
    @exclude_from_serialization
    def auto_generate_projections(self) -> bool:
        """Gets the auto generate projections"""
        return self.__auto_generate_projections

    @auto_generate_projections.setter
    def auto_generate_projections(self, value: bool):
        self.__auto_generate_projections = value

    @property
    @exclude_from_serialization
    def projection_expression_attribute_names(self) -> dict | None:
        """
        Gets the projection expression attribute names

        """
        if self.__projection_expression_attribute_names is None and self.auto_generate_projections:
            props = self.to_dictionary()
            # turn props to a list[str]
            prop_list = list(props.keys())
            self.projection_expression_attribute_names = self.__reserved_words.transform_attributes(
                prop_list
            )
        else:
            if self.projection_expression:
                expression_list = self.projection_expression.replace("#", "").split(",")
                self.projection_expression_attribute_names = (
                    self.__reserved_words.transform_attributes(expression_list)
                )

        return self.__projection_expression_attribute_names

    @projection_expression_attribute_names.setter
    def projection_expression_attribute_names(self, value: dict | None):
        self.__projection_expression_attribute_names = value

    def map(self: T, item: Dict[str, Any] | DynamoDBModelBase | None) -> T:
        """
        Map the item to the instance.  If the item is a DynamoDBModelBase,
        it will be converted to a dictionary first and then mapped.

        Args:
            self (T): The Type of object you are converting it to.
            item (dict | DynamoDBModelBase): _description_

        Raises:
            ValueError: If the object is not a dictionary or DynamoDBModelBase

        Returns:
            T | None: An object of type T with properties set matching
            that of the dictionary object or None
        """
        if item is None:
            item = {}

        if isinstance(item, DynamoDBModelBase):
            item = item.to_resource_dictionary()

        if isinstance(item, dict):
            # Handle DynamoDB response structures
            if "ResponseMetadata" in item:
                # Full DynamoDB response with metadata
                response: dict | None = item.get("Item")
                if response is None:
                    response = {}
                item = response
            elif "Item" in item and not any(key in item for key in ["id", "name", "pk", "sk"]):
                # Response with Item key but no direct model attributes (likely a DynamoDB response)
                # This handles cases like {'Item': {...}} or {'Item': {...}, 'Count': 1}
                item = item.get("Item", {})

            # Convert any Decimal objects to native Python types for easier handling
            item = DecimalConversionUtility.convert_decimals_to_native_types(item)

        else:
            raise ValueError("Item must be a dictionary or DynamoDBModelBase")
        # attempt to map it
        return DynamoDBSerializer.map(source=item, target=self)

    def merge(
        self: T,
        updates: Dict[str, Any] | DynamoDBModelBase | None,
        strategy: MergeStrategy = MergeStrategy.NON_NULL_WINS,
        include_fields: Set[str] | List[str] | None = None,
        exclude_fields: Set[str] | List[str] | None = None,
    ) -> T:
        """
        Merge updates into this instance based on the specified strategy.

        Unlike map() which overwrites all fields, merge() selectively updates
        fields based on the strategy and handles the common case where you want
        to apply partial updates from an API request.

        Args:
            updates: The source of updates - can be a dict or another model instance.
            strategy: How to handle the merge:
                - NON_NULL_WINS (default): Only overwrite if update value is not None.
                  Use CLEAR_FIELD sentinel to explicitly set a field to None.
                - UPDATES_WIN: Update values always win, even if None.
                - EXISTING_WINS: Only fill in fields that are currently None.
            include_fields: If provided, only these fields will be considered for merge.
            exclude_fields: Fields to exclude from the merge (e.g., 'id', 'created_at').

        Returns:
            Self with merged updates applied.

        Example:
            # Load existing from DB
            existing = Product().map(db_response)

            # Merge partial updates (only non-null fields applied)
            existing.merge({"name": "New Name", "price": None})  # price unchanged

            # Explicitly clear a field
            from boto3_assist.dynamodb import CLEAR_FIELD
            existing.merge({"description": CLEAR_FIELD})  # description set to None

            # Fill gaps only (useful for defaults)
            existing.merge(defaults, strategy=MergeStrategy.EXISTING_WINS)
        """
        if updates is None:
            return self

        # Convert to dict if needed
        updates_dict: Dict[str, Any]
        if isinstance(updates, DynamoDBModelBase):
            updates_dict = updates.to_resource_dictionary(include_indexes=False)
        elif isinstance(updates, dict):
            updates_dict = updates.copy()
        else:
            raise ValueError("Updates must be a dictionary or DynamoDBModelBase")

        # Convert decimals if present
        updates_dict = DecimalConversionUtility.convert_decimals_to_native_types(updates_dict)

        # Apply field filters
        if include_fields is not None:
            include_set = set(include_fields)
            updates_dict = {k: v for k, v in updates_dict.items() if k in include_set}

        if exclude_fields is not None:
            exclude_set = set(exclude_fields)
            updates_dict = {k: v for k, v in updates_dict.items() if k not in exclude_set}

        # Apply merge based on strategy
        return DynamoDBSerializer.merge(updates=updates_dict, target=self, strategy=strategy)

    def to_client_dictionary(self, include_indexes: bool = True):
        """
        Convert the instance to a dictionary suitable for DynamoDB client.
        """
        return DynamoDBSerializer.to_client_dictionary(self, include_indexes=include_indexes)

    def to_resource_dictionary(self, include_indexes: bool = True, include_none: bool = False):
        """
        Convert the instance to a dictionary suitable for DynamoDB resource.
        """
        return DynamoDBSerializer.to_resource_dictionary(
            self, include_indexes=include_indexes, include_none=include_none
        )

    def to_dict(self, include_none: bool = True):
        """
        Convert the instance to a dictionary suitable for DynamoDB client.
        """
        return self.to_dictionary(include_none=include_none)

    def to_dictionary(self, include_none: bool = True):
        """
        Convert the instance to a dictionary without an indexes/keys.
        Useful for turning an object into a dictionary for serialization.
        This is the same as to_resource_dictionary(include_indexes=False)
        """
        return DynamoDBSerializer.to_resource_dictionary(
            self, include_indexes=False, include_none=include_none
        )

    def get_key(self, index_name: str) -> DynamoDBIndex:
        """Get the index name and key"""

        if index_name is None:
            raise ValueError("Index name cannot be None")

        return self.indexes.get(index_name)

    @staticmethod
    def generate_uuid(sortable: bool = True) -> str:
        if sortable:
            return StringUtility.generate_sortable_uuid()

        return StringUtility.generate_uuid()

    @property
    @exclude_from_serialization
    def helpers(self) -> DynamoDBHelpers:
        """Get the helpers"""
        if self.__helpers is None:
            self.__helpers = DynamoDBHelpers()
        return self.__helpers

    def list_keys(self, exclude_pk: bool = False) -> List[DynamoDBIndex]:
        """List the keys"""
        values = self.indexes.values()
        if exclude_pk:
            values = [v for v in values if not v.name == DynamoDBIndexes.PRIMARY_INDEX]

        return values

    def to_timestamp_or_none(self, value: str | dt.datetime | None) -> float | None:
        """
        Convert a value to a timestamp (float) or None

        Exceptions:
            ValueError: If the value is not a datetime string or datetime
        """

        if isinstance(value, str):
            # value = dt.datetime.fromisoformat(value)
            value = DatetimeUtility.to_datetime_utc(value)

        if value is None:
            return None

        if isinstance(value, dt.datetime):
            return value.timestamp()

        raise ValueError("Value must be a None, a string in a valid datetime format or datetime")

    def to_utc(self, value: str | dt.datetime | None) -> dt.datetime | None:
        """
        Convert a datetime to UTC. This ensures all datetimes are stored in UTC format

        Exceptions:
            ValueError: If the value is not a datetime string or datetime
        """

        value = DatetimeUtility.to_datetime_utc(value)
        return value


class DynamoDBSerializer:
    """Library to Serialize object to a DynamoDB Format"""

    T = TypeVar("T", bound=DynamoDBModelBase)

    @staticmethod
    def map(source: dict, target: T) -> T:
        """
        Map the source dictionary to the target object.

        Args:
        - source: The dictionary to map from.
        - target: The object to map to.
        """
        mapped = Serialization.map(source, target)
        if mapped is None:
            raise ValueError("Unable to map source to target")

        return mapped

    @staticmethod
    def to_client_dictionary(
        instance: DynamoDBModelBase, include_indexes: bool = True
    ) -> Dict[str, Any]:
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB client.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB client.
        """
        serializer = TypeSerializer()
        d = Serialization.to_dict(instance, serializer.serialize)

        if include_indexes:
            d = DynamoDBSerializer._add_indexes(instance=instance, instance_dict=d)

        return d

    @staticmethod
    def to_resource_dictionary(
        instance: DynamoDBModelBase,
        include_indexes: bool = True,
        include_none: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert a Python class instance to a dictionary suitable for DynamoDB resource.

        Args:
        - instance: The class instance to be converted.

        Returns:
        - dict: A dictionary representation of the class instance suitable for DynamoDB resource.
        """
        d = Serialization.to_dict(
            instance,
            lambda x: x,
            include_none=include_none,
        )

        if include_indexes:
            d = DynamoDBSerializer._add_indexes(instance=instance, instance_dict=d)

        return d

    @staticmethod
    def _add_indexes(instance: DynamoDBModelBase, instance_dict: dict) -> dict:
        if not issubclass(type(instance), DynamoDBModelBase):
            return instance_dict

        if instance.indexes is None:
            return instance_dict

        primary = instance.indexes.primary

        if primary:
            instance_dict[primary.partition_key.attribute_name] = primary.partition_key.value
            if primary.sort_key.attribute_name is not None and primary.sort_key.value is not None:
                instance_dict[primary.sort_key.attribute_name] = primary.sort_key.value

        secondaries = instance.indexes.secondaries

        key: DynamoDBIndex
        for _, key in secondaries.items():
            if key.partition_key.attribute_name is not None and key.partition_key.value is not None:
                instance_dict[key.partition_key.attribute_name] = key.partition_key.value
            if key.sort_key.value is not None and key.sort_key.value is not None:
                instance_dict[key.sort_key.attribute_name] = key.sort_key.value

        return instance_dict

    @staticmethod
    def merge(updates: Dict[str, Any], target: T, strategy: MergeStrategy) -> T:
        """
        Merge updates into the target object based on the specified strategy.

        Args:
            updates: Dictionary of field updates to apply.
            target: The target object to merge into.
            strategy: The merge strategy to use.

        Returns:
            The target object with updates merged.
        """
        for key, update_value in updates.items():
            if not Serialization.has_attribute(target, key):
                continue

            current_value = getattr(target, key, None)

            # Handle CLEAR_FIELD sentinel - always clears to None
            if isinstance(update_value, _ClearFieldSentinel):
                try:
                    setattr(target, key, None)
                except (AttributeError, TypeError):
                    pass  # Property without setter or type issue
                continue

            # Apply strategy
            should_update = False

            if strategy == MergeStrategy.UPDATES_WIN:
                # Updates always win
                should_update = True

            elif strategy == MergeStrategy.NON_NULL_WINS:
                # Only update if the new value is not None
                should_update = update_value is not None

            elif strategy == MergeStrategy.EXISTING_WINS:
                # Only update if current value is None
                should_update = current_value is None

            if should_update:
                try:
                    # Handle nested objects/dicts
                    if (
                        isinstance(current_value, dict)
                        and isinstance(update_value, dict)
                        and strategy != MergeStrategy.UPDATES_WIN
                    ):
                        # Recursively merge dicts
                        DynamoDBSerializer._merge_dict(current_value, update_value, strategy)
                    elif hasattr(current_value, "__dict__") and isinstance(update_value, dict):
                        # Nested object - recursively merge
                        DynamoDBSerializer.merge(
                            updates=update_value,
                            target=current_value,
                            strategy=strategy,
                        )
                    else:
                        setattr(target, key, update_value)
                except (AttributeError, TypeError):
                    pass  # Property without setter or type issue

        return target

    @staticmethod
    def _merge_dict(
        target_dict: Dict[str, Any],
        updates_dict: Dict[str, Any],
        strategy: MergeStrategy,
    ) -> None:
        """
        Merge updates into a target dictionary based on strategy.

        Args:
            target_dict: The dictionary to merge into (modified in place).
            updates_dict: The dictionary of updates.
            strategy: The merge strategy to use.
        """
        for key, update_value in updates_dict.items():
            current_value = target_dict.get(key)

            # Handle CLEAR_FIELD sentinel
            if isinstance(update_value, _ClearFieldSentinel):
                target_dict[key] = None
                continue

            should_update = False

            if strategy == MergeStrategy.UPDATES_WIN:
                should_update = True
            elif strategy == MergeStrategy.NON_NULL_WINS:
                should_update = update_value is not None
            elif strategy == MergeStrategy.EXISTING_WINS:
                should_update = current_value is None

            if should_update:
                if (
                    isinstance(current_value, dict)
                    and isinstance(update_value, dict)
                    and strategy != MergeStrategy.UPDATES_WIN
                ):
                    DynamoDBSerializer._merge_dict(current_value, update_value, strategy)
                else:
                    target_dict[key] = update_value
