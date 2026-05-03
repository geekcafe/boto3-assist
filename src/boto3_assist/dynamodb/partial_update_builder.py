"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Partial Update Builder for DynamoDB

This module provides the PartialUpdateBuilder class which generates DynamoDB update
expressions from model fields, handling reserved keywords and field filtering.
"""

from dataclasses import dataclass
from typing import Any, Dict, Set, Tuple

from boto3_assist.dynamodb.dynamodb_reserved_words import DynamoDBReservedWords


@dataclass
class UpdateExpressionComponents:
    """
    Components of a DynamoDB update expression.

    This dataclass encapsulates all the components needed to execute a DynamoDB
    UpdateItem operation with an update expression.

    Attributes:
        update_expression: The complete update expression string (e.g., "SET #name = :name REMOVE temp_field").
            This is the main expression that DynamoDB will execute.
        expression_attribute_names: Mapping of placeholders to actual attribute names
            (e.g., {"#status": "status"}). Used to handle reserved keywords and special characters
            in attribute names.
        expression_attribute_values: Mapping of placeholders to values
            (e.g., {":name": "John"}). Contains the actual values to be set in the update.
    """

    update_expression: str
    """The complete update expression (e.g., "SET #name = :name REMOVE temp_field")"""

    expression_attribute_names: Dict[str, str]
    """Mapping of placeholders to actual attribute names (e.g., {"#status": "status"})"""

    expression_attribute_values: Dict[str, Any]
    """Mapping of placeholders to values (e.g., {":name": "John"})"""


class PartialUpdateBuilder:
    """
    Builds DynamoDB update expressions for partial updates.

    This class encapsulates the logic for generating DynamoDB update expressions
    from a set of fields to update. It handles:
    - Separating fields into SET and REMOVE operations
    - Detecting and handling reserved keywords
    - Generating expression attribute names and values
    - Combining clauses into a complete update expression

    The builder is designed to work with DynamoDBModelBase instances and generates
    expressions that can be used with DynamoDB.update_item().

    Example:
        >>> builder = PartialUpdateBuilder()
        >>> fields_to_update = {"name": "John", "status": "active"}
        >>> components = builder.build_update_expression(fields_to_update)
        >>> # components.update_expression = "SET name = :name, #status = :status"
        >>> # components.expression_attribute_names = {"#status": "status"}
        >>> # components.expression_attribute_values = {":name": "John", ":status": "active"}
    """

    def __init__(self) -> None:
        """
        Initialize the PartialUpdateBuilder.

        Sets up the reserved words detector for identifying DynamoDB reserved keywords.
        """
        self.reserved_words = DynamoDBReservedWords()

    def build_update_expression(
        self,
        fields_to_update: Dict[str, Any],
        fields_to_clear: Set[str] | None = None,
    ) -> UpdateExpressionComponents:
        """
        Build update expression components from fields to update and clear.

        This method orchestrates the entire expression building process:
        1. Separates fields into SET and REMOVE operations
        2. Builds the SET clause with reserved keyword handling
        3. Builds the REMOVE clause with reserved keyword handling
        4. Combines clauses into a final update expression
        5. Returns all components needed for DynamoDB.update_item()

        Args:
            fields_to_update: Dictionary of {field_name: field_value} to update.
                Only non-None values should be included.
            fields_to_clear: Optional set of field names to remove from the item.
                These will be included in a REMOVE clause.

        Returns:
            UpdateExpressionComponents containing:
            - update_expression: The complete expression string
            - expression_attribute_names: Mapping for reserved keywords
            - expression_attribute_values: Mapping for field values

        Raises:
            ValueError: If no fields are provided to update or clear.

        Example:
            >>> builder = PartialUpdateBuilder()
            >>> components = builder.build_update_expression(
            ...     fields_to_update={"name": "John", "status": "active"},
            ...     fields_to_clear={"temp_field"}
            ... )
        """
        if fields_to_clear is None:
            fields_to_clear = set()

        # Build SET clause
        set_clause, set_names, set_values = self._build_set_clause(fields_to_update)

        # Build REMOVE clause
        remove_clause, remove_names = self._build_remove_clause(fields_to_clear)

        # Combine clauses
        clauses = []
        if set_clause:
            clauses.append(set_clause)
        if remove_clause:
            clauses.append(remove_clause)

        if not clauses:
            raise ValueError("No fields to update or clear")

        update_expression = " ".join(clauses)

        # Merge expression attribute names and values
        expression_attribute_names = {**set_names, **remove_names}
        expression_attribute_values = set_values

        return UpdateExpressionComponents(
            update_expression=update_expression,
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values,
        )

    def _separate_operations(
        self,
        fields_to_update: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Set[str]]:
        """
        Separate fields into SET operations and REMOVE operations.

        This method identifies which fields should be SET (non-None values) and
        which should be REMOVED (None values or CLEAR_FIELD sentinels).

        Args:
            fields_to_update: Dictionary of {field_name: field_value} to process.

        Returns:
            Tuple of (set_fields, remove_fields) where:
            - set_fields: {field_name: value} for SET clause (non-None values)
            - remove_fields: {field_name} for REMOVE clause (None values)

        Note:
            This method is primarily used internally by build_update_expression().
            In the current implementation, None values are excluded from the input,
            so this method mainly validates the input structure.
        """
        set_fields: Dict[str, Any] = {}
        remove_fields: Set[str] = set()

        for field_name, field_value in fields_to_update.items():
            if field_value is not None:
                set_fields[field_name] = field_value
            # Note: None values are excluded from both SET and REMOVE
            # Only explicitly passed fields_to_clear are added to REMOVE

        return set_fields, remove_fields

    def _build_set_clause(
        self,
        set_fields: Dict[str, Any],
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Build SET clause with reserved keyword handling.

        This method generates the SET clause of an update expression, handling
        reserved keywords by generating expression attribute names.

        For each field:
        - If it's a reserved keyword, use a placeholder (#field_name)
        - If it's not reserved, use the field name directly
        - Generate a value placeholder (:field_name)
        - Add to expression_attribute_names if reserved
        - Add to expression_attribute_values

        Args:
            set_fields: Dictionary of {field_name: field_value} to include in SET clause.

        Returns:
            Tuple of (set_clause_str, expression_attribute_names, expression_attribute_values) where:
            - set_clause_str: The SET clause string (e.g., "SET name = :name, #status = :status")
            - expression_attribute_names: Mapping for reserved keywords (e.g., {"#status": "status"})
            - expression_attribute_values: Mapping for values (e.g., {":name": "John", ":status": "active"})

        Example:
            >>> builder = PartialUpdateBuilder()
            >>> clause, names, values = builder._build_set_clause(
            ...     {"name": "John", "status": "active"}
            ... )
            >>> # clause = "SET name = :name, #status = :status"
            >>> # names = {"#status": "status"}
            >>> # values = {":name": "John", ":status": "active"}
        """
        if not set_fields:
            return "", {}, {}

        set_clauses = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        for field_name, field_value in set_fields.items():
            # Get placeholders
            name_placeholder = self._get_placeholder_name(field_name)
            value_placeholder = self._get_placeholder_value(field_name)

            # Check if field is reserved keyword
            if self.reserved_words.is_reserved_word(field_name):
                # Use placeholder for reserved keyword
                expression_attribute_names[name_placeholder] = field_name
                set_clauses.append(f"{name_placeholder} = {value_placeholder}")
            else:
                # Use field name directly
                set_clauses.append(f"{field_name} = {value_placeholder}")

            # Add value to expression_attribute_values
            expression_attribute_values[value_placeholder] = field_value

        set_clause = "SET " + ", ".join(set_clauses)
        return set_clause, expression_attribute_names, expression_attribute_values

    def _build_remove_clause(
        self,
        remove_fields: Set[str],
    ) -> Tuple[str, Dict[str, str]]:
        """
        Build REMOVE clause with reserved keyword handling.

        This method generates the REMOVE clause of an update expression, handling
        reserved keywords by generating expression attribute names.

        For each field:
        - If it's a reserved keyword, use a placeholder (#field_name)
        - If it's not reserved, use the field name directly
        - Add to expression_attribute_names if reserved

        Args:
            remove_fields: Set of field names to include in REMOVE clause.

        Returns:
            Tuple of (remove_clause_str, expression_attribute_names) where:
            - remove_clause_str: The REMOVE clause string (e.g., "REMOVE temp_field, #status")
            - expression_attribute_names: Mapping for reserved keywords (e.g., {"#status": "status"})

        Example:
            >>> builder = PartialUpdateBuilder()
            >>> clause, names = builder._build_remove_clause({"temp_field", "status"})
            >>> # clause = "REMOVE temp_field, #status"
            >>> # names = {"#status": "status"}
        """
        if not remove_fields:
            return "", {}

        remove_clauses = []
        expression_attribute_names = {}

        for field_name in sorted(remove_fields):  # Sort for consistent output
            # Get placeholder
            name_placeholder = self._get_placeholder_name(field_name)

            # Check if field is reserved keyword
            if self.reserved_words.is_reserved_word(field_name):
                # Use placeholder for reserved keyword
                expression_attribute_names[name_placeholder] = field_name
                remove_clauses.append(name_placeholder)
            else:
                # Use field name directly
                remove_clauses.append(field_name)

        remove_clause = "REMOVE " + ", ".join(remove_clauses)
        return remove_clause, expression_attribute_names

    def _get_placeholder_name(self, field_name: str) -> str:
        """
        Get expression attribute name placeholder for a field.

        Generates a placeholder in the format #field_name for use in
        expression attribute names mapping.

        Args:
            field_name: The field name to generate a placeholder for.

        Returns:
            The placeholder string (e.g., "#status" for field "status").

        Example:
            >>> builder = PartialUpdateBuilder()
            >>> placeholder = builder._get_placeholder_name("status")
            >>> # placeholder = "#status"
        """
        return f"#{field_name}"

    def _get_placeholder_value(self, field_name: str) -> str:
        """
        Get expression attribute value placeholder for a field.

        Generates a placeholder in the format :field_name for use in
        expression attribute values mapping.

        Args:
            field_name: The field name to generate a placeholder for.

        Returns:
            The placeholder string (e.g., ":status" for field "status").

        Example:
            >>> builder = PartialUpdateBuilder()
            >>> placeholder = builder._get_placeholder_value("status")
            >>> # placeholder = ":status"
        """
        return f":{field_name}"
