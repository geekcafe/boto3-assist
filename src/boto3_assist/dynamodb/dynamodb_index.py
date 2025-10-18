"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
https://github.com/geekcafe/boto3-assist
"""

from __future__ import annotations
from typing import Optional, Any
from boto3.dynamodb.conditions import (
    ConditionBase,
    Key,
    Equals,
    ComparisonCondition,
    And,
)
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class DynamoDBIndexes:
    """Track the indexes"""

    PRIMARY_INDEX = "primary"

    def __init__(self) -> None:
        self.__indexes: dict[str, DynamoDBIndex] = {}

    def remove_primary(self):
        """Remove the primary index"""
        if DynamoDBIndexes.PRIMARY_INDEX in self.__indexes:
            del self.__indexes[DynamoDBIndexes.PRIMARY_INDEX]

    def add_primary(self, index: DynamoDBIndex):
        """Add an index"""
        index.name = DynamoDBIndexes.PRIMARY_INDEX

        if index.name in self.__indexes:
            raise ValueError(
                f"The index {index.name} is already defined in your model somewhere. "
                "This error is generated to protect you from unforeseen issues. "
                "If you models are inheriting from other models, you may have the primary defined twice."
            )

        self.__indexes[DynamoDBIndexes.PRIMARY_INDEX] = index

    def add_secondary(self, index: DynamoDBIndex):
        """Add a GSI/LSI index"""
        if index.name is None:
            raise ValueError("Index name cannot be None")

        # if the index already exists, raise an exception
        if index.name in self.__indexes:
            raise ValueError(
                f"The index {index.name} is already defined in your model somewhere. "
                "This error is generated to protect you from unforseen issues. "
                "If you models are inheriting from other models, you may have the primary defined twice."
            )
        if index.name == DynamoDBIndexes.PRIMARY_INDEX:
            raise ValueError(f"Index {index.name} is reserved for the primary index")
        if index.partition_key is None:
            raise ValueError("Index must have a partition key")

        # check if the index.partition_key.attribute_name is already in the index
        for _, v in self.__indexes.items():
            if v.partition_key.attribute_name == index.partition_key.attribute_name:
                raise ValueError(
                    f"The attribute {index.partition_key.attribute_name} is already being used by index "
                    f"{v.name}. "
                    f"Reusing this attribute would over write the value on index {v.name}"
                )
        # check if the gsi1.sort_key.attribute_name exists
        if index.sort_key is not None:
            for _, v in self.__indexes.items():
                if v.sort_key.attribute_name == index.sort_key.attribute_name:
                    raise ValueError(
                        f"The attribute {index.sort_key.attribute_name} is already being used by index "
                        f"{v.name}. "
                        f"Reusing this attribute would over write the value on index {v.name}"
                    )

        self.__indexes[index.name] = index

    def get(self, index_name: str) -> DynamoDBIndex:
        """Get an index"""
        if index_name not in self.__indexes:
            raise ValueError(f"Index {index_name} not found")
        return self.__indexes[index_name]

    @property
    def primary(self) -> DynamoDBIndex | None:
        """Get the primary index"""
        if DynamoDBIndexes.PRIMARY_INDEX not in self.__indexes:
            return None
            # raise ValueError("Primary index not found")
        return self.__indexes[DynamoDBIndexes.PRIMARY_INDEX]

    @property
    def secondaries(self) -> dict[str, DynamoDBIndex]:
        """Get the secondary indexes"""
        # get all indexes that are not the primary index
        indexes = {
            k: v
            for k, v in self.__indexes.items()
            if k != DynamoDBIndexes.PRIMARY_INDEX
        }

        return indexes

    def values(self) -> list[DynamoDBIndex]:
        """Get the values of the indexes"""
        return list(self.__indexes.values())


class DynamoDBIndex:
    """A DynamoDB Index"""

    def __init__(
        self,
        index_name: Optional[str] = None,
        partition_key: Optional[DynamoDBKey] = None,
        sort_key: Optional[DynamoDBKey] = None,
        description: Optional[str] = None,
    ):
        self.name: Optional[str] = index_name
        self.description: Optional[str] = description
        """Optional description information.  Used for self documentation."""
        self.__pk: Optional[DynamoDBKey] = partition_key
        self.__sk: Optional[DynamoDBKey] = sort_key

    @property
    def partition_key(self) -> DynamoDBKey:
        """Get the primary key"""
        if not self.__pk:
            self.__pk = DynamoDBKey()
        return self.__pk

    @partition_key.setter
    def partition_key(self, value: DynamoDBKey):
        self.__pk = value

    @property
    def sort_key(self) -> DynamoDBKey:
        """Get the sort key"""
        if not self.__sk:
            self.__sk = DynamoDBKey()
        return self.__sk

    @sort_key.setter
    def sort_key(self, value: DynamoDBKey | None):
        self.__sk = value

    def to_dict(self, include_sort_key: bool = True) -> dict[str, str]:
        """
        Return a dictionary representation of this index's keys for debugging.
        
        This is particularly useful for:
        - Debugging key generation logic
        - Logging DynamoDB operations
        - Verifying composite key structure
        - Testing key values
        
        Args:
            include_sort_key: Whether to include the sort key (default: True)
            
        Returns:
            Dictionary with partition key and optionally sort key.
            
        Example:
            >>> index = DynamoDBIndex()
            >>> index.partition_key.attribute_name = "pk"
            >>> index.partition_key.value = lambda: "user#123"
            >>> index.sort_key.attribute_name = "sk"
            >>> index.sort_key.value = lambda: "user#123"
            >>> index.to_dict()
            {'pk': 'user#123', 'sk': 'user#123'}
            
            >>> # Partition key only
            >>> index.to_dict(include_sort_key=False)
            {'pk': 'user#123'}
            
            >>> # Useful for debugging
            >>> print(f"Querying with key: {index.to_dict()}")
            Querying with key: {'pk': 'user#123', 'sk': 'user#123'}
        """
        result = {}
        
        # Always include partition key
        if self.__pk:
            result[self.partition_key.attribute_name] = self.partition_key.value
        
        # Optionally include sort key
        if include_sort_key and self.__sk and self.sort_key.attribute_name:
            try:
                result[self.sort_key.attribute_name] = self.sort_key.value
            except ValueError:
                # Sort key value not set, skip it
                pass
                
        return result

    def debug_info(
        self,
        *,
        include_sort_key: bool = True,
        condition: str = "begins_with",
        low_value: Any = None,
        high_value: Any = None,
    ) -> dict[str, Any]:
        """
        Return detailed debugging information about this index and how it would be queried.
        
        This is useful for understanding:
        - What keys are defined
        - What condition would be used in a query
        - What the actual key values are
        - What index name would be used
        
        Args:
            include_sort_key: Whether to include the sort key (default: True)
            condition: The condition type being used (default: "begins_with")
            low_value: Low value for "between" condition
            high_value: High value for "between" condition
            
        Returns:
            Dictionary with debugging information including keys, condition, and index details.
            
        Example:
            >>> index = product.indexes.get("gsi1")
            >>> debug = index.debug_info(condition="begins_with")
            >>> print(debug)
            {
                'index_name': 'gsi1',
                'partition_key': {
                    'attribute': 'gsi1_pk',
                    'value': 'category#electronics'
                },
                'sort_key': {
                    'attribute': 'gsi1_sk',
                    'value': 'product#prod_123',
                    'condition': 'begins_with'
                },
                'keys_dict': {'gsi1_pk': 'category#electronics', 'gsi1_sk': 'product#prod_123'},
                'query_type': 'GSI' or 'Primary'
            }
            
            >>> # Check condition type
            >>> if debug['sort_key']['condition'] == 'begins_with':
            ...     print("This query uses begins_with")
        """
        result = {
            'index_name': self.name,
            'query_type': 'Primary' if self.name == DynamoDBIndexes.PRIMARY_INDEX else 'GSI/LSI'
        }
        
        # Partition key info
        if self.__pk:
            result['partition_key'] = {
                'attribute': self.partition_key.attribute_name,
                'value': self.partition_key.value
            }
        
        # Sort key info with condition
        if include_sort_key and self.__sk and self.sort_key.attribute_name:
            try:
                sk_info = {
                    'attribute': self.sort_key.attribute_name,
                    'value': self.sort_key.value,
                    'condition': condition
                }
                
                # Add range info for between condition
                if condition == "between" and low_value is not None and high_value is not None:
                    sk_info['low_value'] = low_value
                    sk_info['high_value'] = high_value
                    sk_info['full_range'] = {
                        'low': f"{self.sort_key.value}{low_value}",
                        'high': f"{self.sort_key.value}{high_value}"
                    }
                
                result['sort_key'] = sk_info
            except ValueError:
                # Sort key value not set
                result['sort_key'] = {
                    'attribute': self.sort_key.attribute_name,
                    'value': None,
                    'condition': condition,
                    'note': 'Sort key value not set'
                }
        
        # Include the keys dictionary for convenience
        result['keys_dict'] = self.to_dict(include_sort_key=include_sort_key)
        
        return result

    def key(
        self,
        *,
        include_sort_key: bool = True,
        condition: str = "begins_with",
        low_value: Any = None,
        high_value: Any = None,
        query_key: bool = False,
        # sk_value_2: Optional[str | int | float] = None,
    ) -> dict | Key | ConditionBase | ComparisonCondition | Equals:
        """Get the key for a given index"""
        key: dict | Key | ConditionBase | ComparisonCondition | Equals

        if query_key:
            key = self._build_query_key(
                include_sort_key=include_sort_key,
                condition=condition,
                low_value=low_value,
                high_value=high_value,
            )
            return key

        elif self.name == DynamoDBIndexes.PRIMARY_INDEX and include_sort_key:
            # this is a direct primary key which is used in a get call
            # this is different than query keys
            key = {}
            key[self.partition_key.attribute_name] = self.partition_key.value

            if self.sort_key and self.sort_key.attribute_name:
                key[self.sort_key.attribute_name] = self.sort_key.value

            return key

        # catch all (TODO: decide if this is the best pattern or should we raise an error)
        key = self._build_query_key(
            include_sort_key=include_sort_key,
            condition=condition,
            low_value=low_value,
            high_value=high_value,
        )
        return key

    def _build_query_key(
        self,
        *,
        include_sort_key: bool = True,
        condition: str = "begins_with",
        low_value: Any = None,
        high_value: Any = None,
    ) -> And | Equals:
        """Get the GSI index name and key"""

        key: And | Equals = Key(f"{self.partition_key.attribute_name}").eq(
            self.partition_key.value
        )

        if (
            include_sort_key
            and self.sort_key.attribute_name
            and (
                self.sort_key.value
                or (low_value is not None and high_value is not None)
            )
        ):
            # if self.sk_value_2:
            if low_value is not None and high_value is not None:
                match condition:
                    case "between":
                        low = f"{self.sort_key.value}{low_value}"
                        high = f"{self.sort_key.value}{high_value}"
                        key = key & Key(f"{self.sort_key.attribute_name}").between(
                            low, high
                        )

            else:
                match condition:
                    case "begins_with":
                        key = key & Key(f"{self.sort_key.attribute_name}").begins_with(
                            self.sort_key.value
                        )
                    case "eq":
                        key = key & Key(f"{self.sort_key.attribute_name}").eq(
                            self.sort_key.value
                        )
                    case "gt":
                        key = key & Key(f"{self.sort_key.attribute_name}").gt(
                            self.sort_key.value
                        )
                    case "gte":
                        key = key & Key(f"{self.sort_key.attribute_name}").gte(
                            self.sort_key.value
                        )
                    case "lt":
                        key = key & Key(f"{self.sort_key.attribute_name}").lt(
                            self.sort_key.value
                        )

        return key

    @staticmethod
    def extract_key_values(
        key_expression: And | Equals,
        index: Optional[str | DynamoDBIndex] = None
    ) -> dict[str, Any]:
        """
        Extract key values and condition information from a boto3 Key condition expression.
        
        This is useful for debugging queries at runtime to see exactly what values
        are being used in the KeyConditionExpression.
        
        Args:
            key_expression: The Key condition expression (from key() or _build_query_key())
            index: Optional index name (str) or DynamoDBIndex object to include in results
            
        Returns:
            Dictionary containing:
                - index_name: str (if index parameter provided)
                - partition_key: {'attribute': str, 'value': str}
                - sort_key: {'attribute': str, 'value': str, 'operator': str, 'format': str} (if present)
                
        Example:
            >>> index = model.indexes.get("gsi1")
            >>> key_expr = index.key(query_key=True, condition="begins_with")
            >>> debug = DynamoDBIndex.extract_key_values(key_expr, index)
            >>> print(debug)
            {
                'index_name': 'gsi1',
                'partition_key': {
                    'attribute': 'gsi1_pk',
                    'value': 'inbox#support#status#open'
                },
                'sort_key': {
                    'attribute': 'gsi1_sk',
                    'value': 'priority#medium#ts#',
                    'operator': 'begins_with',
                    'format': '{operator}({0}, {1})'
                }
            }
            
            >>> # Or pass just the index name
            >>> debug = DynamoDBIndex.extract_key_values(key_expr, "gsi1")
            
            >>> # Quick access to values
            >>> pk_value = debug['partition_key']['value']
            >>> sk_value = debug['sort_key']['value']
            >>> condition = debug['sort_key']['operator']
            >>> index_name = debug.get('index_name')
        """
        result = {}
        
        # Include index name if provided
        if index is not None:
            if isinstance(index, str):
                result['index_name'] = index
            elif isinstance(index, DynamoDBIndex):
                result['index_name'] = index.name
        
        try:
            # The key_expression._values is a list of conditions
            # [0] is the partition key (Equals condition)
            # [1] is the sort key (ComparisonCondition) if present
            
            if hasattr(key_expression, '_values') and len(key_expression._values) > 0:
                # Extract partition key
                pk_condition = key_expression._values[0]
                if hasattr(pk_condition, '_values') and len(pk_condition._values) >= 2:
                    pk_attr = pk_condition._values[0]
                    result['partition_key'] = {
                        'attribute': pk_attr.name if hasattr(pk_attr, 'name') else str(pk_attr),
                        'value': pk_condition._values[1]
                    }
                
                # Extract sort key if present
                if len(key_expression._values) > 1:
                    sk_condition = key_expression._values[1]
                    if hasattr(sk_condition, '_values'):
                        sk_attr = sk_condition._values[0] if len(sk_condition._values) > 0 else None
                        sk_info = {
                            'attribute': sk_attr.name if (sk_attr and hasattr(sk_attr, 'name')) else str(sk_attr),
                        }
                        
                        # Get value(s)
                        if len(sk_condition._values) > 1:
                            sk_info['value'] = sk_condition._values[1]
                        
                        # For 'between' condition, there are two values
                        if len(sk_condition._values) > 2:
                            sk_info['value_low'] = sk_condition._values[1]
                            sk_info['value_high'] = sk_condition._values[2]
                            del sk_info['value']  # Remove single value key
                        
                        # Get operator and format
                        if hasattr(sk_condition, 'expression_operator'):
                            sk_info['operator'] = sk_condition.expression_operator
                        if hasattr(sk_condition, 'expression_format'):
                            sk_info['format'] = sk_condition.expression_format
                        
                        result['sort_key'] = sk_info
            
            # If no _values found, handle single Equals condition (no sort key)
            elif isinstance(key_expression, Equals):
                if hasattr(key_expression, '_values') and len(key_expression._values) >= 2:
                    pk_attr = key_expression._values[0]
                    result['partition_key'] = {
                        'attribute': pk_attr.name if hasattr(pk_attr, 'name') else str(pk_attr),
                        'value': key_expression._values[1]
                    }
                    
        except (AttributeError, IndexError) as e:
            result['error'] = f"Unable to extract key values: {str(e)}"
            result['note'] = "The Key expression structure may have changed"
        
        return result
