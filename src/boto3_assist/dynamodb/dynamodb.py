"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
from typing import Any, Dict, List, Optional, Type, TypedDict, TypeVar, Union, overload

from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Attr, ComparisonCondition, ConditionBase, Key  # And,; Equals,
from botocore.exceptions import ClientError

from ..utilities.decimal_conversion_utility import DecimalConversionUtility
from ..utilities.string_utility import StringUtility
from .dynamodb_connection import DynamoDBConnection
from .dynamodb_helpers import DynamoDBHelpers
from .dynamodb_index import DynamoDBIndex
from .dynamodb_model_base import DynamoDBModelBase

logger = Logger()

# Type variable for generic model support
T = TypeVar("T", bound=DynamoDBModelBase)


# TypedDict definitions for common DynamoDB structures
class DynamoDBKey(TypedDict, total=False):
    """Primary key structure for DynamoDB items."""

    pk: str
    sk: str


class QueryResponse(TypedDict, total=False):
    """Response structure from DynamoDB query operations."""

    Items: List[Dict[str, Any]]
    Count: int
    ScannedCount: int
    LastEvaluatedKey: Optional[Dict[str, Any]]
    ConsumedCapacity: Optional[Dict[str, Any]]


class GetResponse(TypedDict, total=False):
    """Response structure from DynamoDB get operations."""

    Item: Optional[Dict[str, Any]]
    ConsumedCapacity: Optional[Dict[str, Any]]


class TransactWriteOperation(TypedDict, total=False):
    """Single operation in a DynamoDB transaction write."""

    Put: Optional[Dict[str, Any]]
    Update: Optional[Dict[str, Any]]
    Delete: Optional[Dict[str, Any]]
    ConditionCheck: Optional[Dict[str, Any]]


class DynamoDB(DynamoDBConnection):
    """
        DynamoDB. Wrapper for basic DynamoDB Connection and Actions

    Inherits:
        DynamoDBConnection
    """

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        assume_role_arn: Optional[str] = None,
        assume_role_chain: Optional[List[str]] = None,
        assume_role_duration_seconds: Optional[int] = 3600,
        use_connection_pool: bool = True,
    ) -> None:
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            assume_role_arn=assume_role_arn,
            assume_role_chain=assume_role_chain,
            assume_role_duration_seconds=assume_role_duration_seconds,
            use_connection_pool=use_connection_pool,
        )
        self.helpers: DynamoDBHelpers = DynamoDBHelpers()
        self.log_dynamodb_item_size: bool = bool(
            os.getenv("LOG_DYNAMODB_ITEM_SIZE", "False").lower() == "true"
        )
        self.convert_decimals: bool = bool(
            os.getenv("DYNAMODB_CONVERT_DECIMALS", "True").lower() == "true"
        )
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    @classmethod
    def from_pool(
        cls,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        **kwargs,
    ) -> "DynamoDB":
        """
        Create DynamoDB connection using connection pool (recommended for Lambda).

        This is the recommended pattern for Lambda functions as it reuses
        boto3 sessions across invocations in warm containers.

        Args:
            aws_profile: AWS profile name (optional)
            aws_region: AWS region (optional)
            aws_end_point_url: Custom endpoint URL (optional, for moto testing)
            **kwargs: Additional DynamoDB parameters

        Returns:
            DynamoDB instance configured to use connection pool

        Example:
            >>> # Recommended pattern for Lambda
            >>> db = DynamoDB.from_pool()
            >>> result = db.get(table_name="my-table", key={"id": "123"})
            >>>
            >>> # Subsequent calls reuse the same connection
            >>> db2 = DynamoDB.from_pool()
            >>> assert db.session is db2.session
        """
        return cls(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            use_connection_pool=True,
            **kwargs,
        )

    def _apply_decimal_conversion(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply decimal conversion to DynamoDB response if enabled.

        Args:
            response: The DynamoDB response dictionary

        Returns:
            The response with decimal conversion applied if enabled
        """
        if not self.convert_decimals:
            return response

        return DecimalConversionUtility.convert_decimals_to_native_types(response)

    def _retry_on_throttle(
        self,
        operation,
        *,
        max_retries: int = 5,
        initial_backoff: float = 0.1,
        operation_name: str = "DynamoDB operation",
    ):
        """
        Execute a DynamoDB operation with exponential backoff retry on throttling.

        DynamoDB on-demand tables auto-scale but can temporarily throttle during
        burst traffic (e.g., hundreds of concurrent Lambda invocations). This
        method retries with exponential backoff to ride out the scaling lag.

        Args:
            operation: Callable that performs the DynamoDB operation
            max_retries: Maximum number of retry attempts (default 5)
            initial_backoff: Initial backoff in seconds (default 0.1s, doubles each retry)
            operation_name: Name for logging (e.g., "update_item", "save")

        Returns:
            The return value of the operation callable

        Raises:
            ClientError: If max retries exceeded or non-throttle error occurs
        """
        import time

        retry_count = 0
        backoff_time = initial_backoff

        while True:
            try:
                return operation()
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if (
                    error_code == "ProvisionedThroughputExceededException"
                    and retry_count < max_retries
                ):
                    logger.warning(
                        f"{operation_name}: Throughput exceeded. "
                        f"Retrying in {backoff_time}s (attempt {retry_count + 1}/{max_retries})"
                    )
                    time.sleep(backoff_time)
                    backoff_time *= 2
                    retry_count += 1
                    continue
                raise

    def save(
        self,
        item: Union[Dict[str, Any], DynamoDBModelBase],
        table_name: str,
        source: Optional[str] = None,
        fail_if_exists: bool = False,
        condition_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Save (create or update) an item in DynamoDB.

        This method performs a PutItem operation, which creates a new item or
        completely replaces an existing item with the same primary key.

        Args:
            item: Item to save. Can be a dictionary or DynamoDBModelBase instance.
                Must include all primary key attributes.
            table_name: Name of the DynamoDB table.
            source: Optional identifier for logging/tracking. Default: None.
            fail_if_exists: If True, only allow insert if item doesn't exist.
                Useful for loggers, historical records, tasks that should only be
                created once. Default: False.
            condition_expression: Optional condition that must be satisfied for the
                save to succeed. Can be a string or boto3 ConditionBase object.
                Example: "attribute_not_exists(pk)" to prevent overwriting.
                If provided, overrides `fail_if_exists`.
            expression_attribute_names: Map of placeholder names to actual attribute
                names. Required when using reserved words in conditions.
                Example: {"#status": "status"}.
            expression_attribute_values: Map of placeholder values used in condition
                expressions. Example: {":min_age": 18}.

        Returns:
            Dictionary containing the response from DynamoDB. May include:
            - "Attributes": The item (if return_values specified)
            - "ConsumedCapacity": Capacity info (if requested)
            - "ItemCollectionMetrics": Collection metrics (if requested)

        Raises:
            RuntimeError: If condition_expression is not satisfied, or if item
                conversion fails.
            ClientError: If DynamoDB operation fails.

        Examples:
            Basic save:
                >>> db = DynamoDB()
                >>> db.save(
                ...     item={"pk": "user#123", "sk": "user#123", "name": "John"},
                ...     table_name="users"
                ... )

            Prevent overwriting existing item:
                >>> db.save(
                ...     item={"pk": "user#123", "sk": "user#123", "name": "John"},
                ...     table_name="users",
                ...     fail_if_exists=True
                ... )

            Conditional save with values:
                >>> db.save(
                ...     item={"pk": "user#123", "sk": "user#123", "age": 25},
                ...     table_name="users",
                ...     condition_expression="age < :max_age",
                ...     expression_attribute_values={":max_age": 100}
                ... )

            Save and return old value (requires additional parameters):
                >>> # Note: Current implementation doesn't support return_values
                >>> # This is a future enhancement
                >>> db.save(
                ...     item={"pk": "user#123", "sk": "user#123", "name": "Jane"},
                ...     table_name="users"
                ... )

            Save a model:
                >>> user = User(id="123", name="John", email="john@example.com")
                >>> db.save(item=user, table_name="users")

            Using boto3 conditions:
                >>> from boto3.dynamodb.conditions import Attr
                >>> db.save(
                ...     item={"pk": "user#123", "sk": "user#123", "status": "active"},
                ...     table_name="users",
                ...     condition_expression=Attr("status").ne("banned")
                ... )

            Optimistic locking with version check:
                >>> db.save(
                ...     item=user,
                ...     table_name="users",
                ...     condition_expression="#version = :expected_version",
                ...     expression_attribute_names={"#version": "version"},
                ...     expression_attribute_values={":expected_version": 5}
                ... )

        Note:
            - PutItem replaces the entire item. Use update_item() for partial updates.
            - Condition expressions are evaluated before the write occurs.
            - Failed condition checks raise RuntimeError with descriptive message.
            - Models are automatically converted to dictionaries before saving.
            - Decimal types are handled automatically for numeric values.
            - If `fail_if_exists=True`, the condition checks for non-existence of
              both pk and sk attributes.

        See Also:
            - update_item(): Update specific attributes without replacing entire item
            - batch_write(): Save multiple items in a single request
            - delete(): Remove an item from the table
        """
        response: Dict[str, Any] = {}

        try:
            if not isinstance(item, dict):
                # attempt to convert it
                if not isinstance(item, DynamoDBModelBase):
                    raise RuntimeError(
                        f"Item is not a dictionary or DynamoDBModelBase. Type: {type(item).__name__}. "
                        "In order to prep the model for saving, it needs to already be dictionary or support "
                        "the to_resource_dictionary() method, which is available when you inherit from DynamoDBModelBase. "
                        "Unable to save item to DynamoDB.  The entry was not saved."
                    )
                try:
                    item = item.to_resource_dictionary()
                except Exception as e:  # pylint: disable=w0718
                    logger.exception(e)
                    raise RuntimeError(
                        "An error occurred during model conversion.  The entry was not saved. "
                    ) from e

            if isinstance(item, dict):
                self.__log_item_size(item=item)

                # Convert native numeric types to Decimal for DynamoDB
                # (DynamoDB doesn't accept float, requires Decimal)
                item = DecimalConversionUtility.convert_native_types_to_decimals(item)

            if isinstance(item, dict) and isinstance(next(iter(item.values())), dict):
                # Use boto3.client syntax
                # client API style
                params = {
                    "TableName": table_name,
                    "Item": item,
                }

                # Handle conditional expressions
                if condition_expression:
                    # Custom condition provided
                    params["ConditionExpression"] = condition_expression
                    if expression_attribute_names:
                        params["ExpressionAttributeNames"] = expression_attribute_names
                    if expression_attribute_values:
                        params["ExpressionAttributeValues"] = expression_attribute_values
                elif fail_if_exists:
                    # only insert if the item does *not* already exist
                    params["ConditionExpression"] = (
                        "attribute_not_exists(#pk) AND attribute_not_exists(#sk)"
                    )
                    params["ExpressionAttributeNames"] = {"#pk": "pk", "#sk": "sk"}

                response = dict(
                    self._retry_on_throttle(
                        lambda: self.dynamodb_client.put_item(**params),
                        operation_name="save(client)",
                    )
                )

            else:
                # Use boto3.resource syntax
                table = self.dynamodb_resource.Table(table_name)

                # Build put_item parameters
                put_params = {"Item": item}

                # Handle conditional expressions
                if condition_expression:
                    # Custom condition provided
                    # Convert string condition to boto3 condition object if needed
                    put_params["ConditionExpression"] = condition_expression
                    if expression_attribute_names:
                        put_params["ExpressionAttributeNames"] = expression_attribute_names
                    if expression_attribute_values:
                        put_params["ExpressionAttributeValues"] = expression_attribute_values
                elif fail_if_exists:
                    put_params["ConditionExpression"] = (
                        Attr("pk").not_exists() & Attr("sk").not_exists()
                    )

                response = dict(
                    self._retry_on_throttle(
                        lambda: table.put_item(**put_params),
                        operation_name="save(resource)",
                    )
                )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "ConditionalCheckFailedException":
                # Enhanced error message for conditional check failures
                if fail_if_exists:
                    raise RuntimeError(
                        f"Item with pk={item['pk']} already exists in {table_name}"
                    ) from e
                elif condition_expression:
                    raise RuntimeError(
                        f"Conditional check failed for item in {table_name}. "
                        f"Condition: {condition_expression}"
                    ) from e
                else:
                    raise RuntimeError(f"Conditional check failed for item in {table_name}") from e

            logger.exception({"source": f"{source}", "metric_filter": "put_item", "error": str(e)})
            raise

        except Exception as e:  # pylint: disable=w0718
            logger.exception({"source": f"{source}", "metric_filter": "put_item", "error": str(e)})
            raise

        return response

    def __log_item_size(self, item: dict):
        if not isinstance(item, dict):
            warning = f"Item is not a dictionary. Type: {type(item).__name__}"
            logger.warning(warning)
            return

        if self.log_dynamodb_item_size:
            size_bytes: int = StringUtility.get_size_in_bytes(item)
            size_kb: float = StringUtility.get_size_in_kb(item)
            logger.info({"item_size": {"bytes": size_bytes, "kb": f"{size_kb:.2f}kb"}})

            if size_kb > 390:
                logger.warning(
                    {
                        "item_size": {
                            "bytes": size_bytes,
                            "kb": f"{size_kb:.2f}kb",
                        },
                        "warning": "approaching limit",
                    }
                )

    @overload
    def get(
        self,
        *,
        table_name: str,
        model: DynamoDBModelBase,
        do_projections: bool = False,
        strongly_consistent: bool = False,
        return_consumed_capacity: Optional[str] = None,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> Dict[str, Any]: ...

    @overload
    def get(
        self,
        key: Dict[str, Any],
        table_name: str,
        *,
        strongly_consistent: bool = False,
        return_consumed_capacity: Optional[str] = None,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> Dict[str, Any]: ...

    def get(
        self,
        key: Optional[Dict[str, Any]] = None,
        table_name: Optional[str] = None,
        model: Optional[DynamoDBModelBase] = None,
        do_projections: bool = False,
        strongly_consistent: bool = False,
        return_consumed_capacity: Optional[str] = None,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> Dict[str, Any]:
        """
        Retrieve a single item from DynamoDB by its primary key.

        This method supports two usage patterns:
        1. Direct key lookup: Provide `key` and `table_name`
        2. Model-based lookup: Provide `model` with keys already set

        Args:
            key: Primary key dictionary (e.g., {"pk": "user#123", "sk": "user#123"}).
                Required if `model` is not provided.
            table_name: Name of the DynamoDB table. Required.
            model: DynamoDBModelBase instance with keys already set. If provided,
                keys will be extracted from the model. Cannot be used with `key`.
            do_projections: If True and using a model, apply the model's projection
                expression to limit returned attributes. Default: False.
            strongly_consistent: If True, perform a strongly consistent read.
                Default: False (eventually consistent).
            return_consumed_capacity: Return information about consumed capacity.
                Options: "INDEXES", "TOTAL", "NONE". Default: None.
            projection_expression: Comma-separated list of attributes to retrieve.
                Example: "id,name,email". Default: None (all attributes).
            expression_attribute_names: Map of placeholder names to actual attribute
                names. Required when attribute names are reserved words.
                Example: {"#status": "status"}. Default: None.
            source: Optional identifier for logging/tracking. Default: None.
            call_type: Internal parameter for connection type. Default: "resource".

        Returns:
            Dictionary containing the item's attributes, or empty dict if not found.

        Raises:
            ValueError: If both `key` and `model` are provided, or if `table_name`
                is missing when using `model`.
            ClientError: If DynamoDB operation fails (network, permissions, etc.).

        Examples:
            Basic retrieval:
                >>> db = DynamoDB()
                >>> item = db.get(
                ...     key={"pk": "user#123", "sk": "user#123"},
                ...     table_name="users"
                ... )
                >>> print(item.get("name"))
                'John Doe'

            With projection (only get specific fields):
                >>> item = db.get(
                ...     key={"pk": "user#123", "sk": "user#123"},
                ...     table_name="users",
                ...     projection_expression="id,name,email"
                ... )

            Strongly consistent read:
                >>> item = db.get(
                ...     key={"pk": "user#123", "sk": "user#123"},
                ...     table_name="users",
                ...     strongly_consistent=True
                ... )

            Using a model:
                >>> user = User(id="123")  # Model with keys set
                >>> item = db.get(
                ...     model=user,
                ...     table_name="users",
                ...     do_projections=True  # Use model's projection
                ... )

            Handling reserved words:
                >>> item = db.get(
                ...     key={"pk": "user#123", "sk": "user#123"},
                ...     table_name="users",
                ...     projection_expression="id,#status",
                ...     expression_attribute_names={"#status": "status"}
                ... )

        Note:
            - Eventually consistent reads are faster and cheaper but may not reflect
              recent writes. Use `strongly_consistent=True` when you need the latest data.
            - Empty dict is returned if item doesn't exist (no exception raised).
            - Use projections to reduce data transfer and improve performance.
            - Reserved words (like "status", "name", "type") must use expression
              attribute names.

        See Also:
            - query(): Retrieve multiple items matching a partition key
            - scan(): Retrieve all items (expensive operation)
            - batch_get(): Retrieve multiple items by their keys
        """

        if model is not None:
            if table_name is None:
                raise ValueError("table_name must be provided when model is used.")
            if key is not None:
                raise ValueError(
                    "key cannot be provided when model is used. "
                    "When using the model, we'll automatically use the key defined."
                )
            key = model.indexes.primary.key()
            if do_projections:
                projection_expression = model.projection_expression
                expression_attribute_names = model.projection_expression_attribute_names
        elif key is None and model is None:
            raise ValueError("Either 'key'  or 'model'  must be provided.")

        response = None
        try:
            kwargs = {
                "ConsistentRead": strongly_consistent,
                "ReturnConsumedCapacity": return_consumed_capacity,
                "ProjectionExpression": projection_expression,
                "ExpressionAttributeNames": expression_attribute_names,
            }
            # only pass in args that aren't none
            valid_kwargs = {k: v for k, v in kwargs.items() if v is not None}

            if table_name is None:
                raise ValueError("table_name must be provided.")
            if call_type == "resource":
                table = self.dynamodb_resource.Table(table_name)
                response = dict(
                    self._retry_on_throttle(
                        lambda: table.get_item(Key=key, **valid_kwargs),  # type: ignore[arg-type]
                        operation_name="get(resource)",
                    )
                )
            elif call_type == "client":
                response = dict(
                    self._retry_on_throttle(
                        lambda: self.dynamodb_client.get_item(
                            Key=key,
                            TableName=table_name,
                            **valid_kwargs,  # type: ignore[arg-type]
                        ),
                        operation_name="get(client)",
                    )
                )
            else:
                raise ValueError(
                    f"Unknown call_type of {call_type}. Supported call_types [resource | client]"
                )
        except Exception as e:  # pylint: disable=w0718
            logger.exception({"source": f"{source}", "metric_filter": "get_item", "error": str(e)})

            response = {"exception": str(e)}
            if self.raise_on_error:
                raise e

        # Apply decimal conversion to the response
        return self._apply_decimal_conversion(response)

    def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        condition_expression: Optional[str] = None,
        return_values: str = "NONE",
    ) -> Dict[str, Any]:
        """
        Update an item in DynamoDB with an update expression.

        Update expressions allow you to modify specific attributes without replacing
        the entire item. Supports SET, ADD, REMOVE, and DELETE operations.

        Args:
            table_name: The DynamoDB table name
            key: Primary key dict, e.g., {"pk": "user#123", "sk": "user#123"}
            update_expression: Update expression string, e.g., "SET #name = :name, age = age + :inc"
            expression_attribute_values: Value mappings, e.g., {":name": "Alice", ":inc": 1}
            expression_attribute_names: Attribute name mappings for reserved words, e.g., {"#name": "name"}
            condition_expression: Optional condition that must be met, e.g., "attribute_exists(pk)"
            return_values: What to return after update:
                - "NONE" (default): Nothing
                - "ALL_OLD": All attributes before update
                - "UPDATED_OLD": Only updated attributes before update
                - "ALL_NEW": All attributes after update
                - "UPDATED_NEW": Only updated attributes after update

        Returns:
            dict: DynamoDB response with optional Attributes based on return_values

        Raises:
            RuntimeError: If condition expression fails
            ClientError: For other DynamoDB errors

        Examples:
            >>> # Simple SET operation
            >>> db.update_item(
            ...     table_name="users",
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     update_expression="SET email = :email",
            ...     expression_attribute_values={":email": "new@example.com"}
            ... )

            >>> # Atomic counter
            >>> db.update_item(
            ...     table_name="users",
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     update_expression="ADD view_count :inc",
            ...     expression_attribute_values={":inc": 1}
            ... )

            >>> # Multiple operations with reserved word
            >>> db.update_item(
            ...     table_name="users",
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     update_expression="SET #status = :status, updated_at = :now REMOVE temp_field",
            ...     expression_attribute_names={"#status": "status"},
            ...     expression_attribute_values={":status": "active", ":now": "2024-10-15"}
            ... )

            >>> # Conditional update with return value
            >>> response = db.update_item(
            ...     table_name="users",
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     update_expression="SET email = :email",
            ...     expression_attribute_values={":email": "new@example.com"},
            ...     condition_expression="attribute_exists(pk)",
            ...     return_values="ALL_NEW"
            ... )
            >>> updated_user = response['Attributes']
        """
        table = self.dynamodb_resource.Table(table_name)

        # Build update parameters
        params = {
            "Key": key,
            "UpdateExpression": update_expression,
            "ReturnValues": return_values,
        }

        if expression_attribute_values:
            params["ExpressionAttributeValues"] = expression_attribute_values

        if expression_attribute_names:
            params["ExpressionAttributeNames"] = expression_attribute_names

        if condition_expression:
            params["ConditionExpression"] = condition_expression

        try:
            response = dict(
                self._retry_on_throttle(
                    lambda: table.update_item(**params),
                    operation_name="update_item",
                )
            )

            # Apply decimal conversion if response contains attributes
            return self._apply_decimal_conversion(response)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "ConditionalCheckFailedException":
                raise RuntimeError(
                    f"Conditional check failed for update in {table_name}. "
                    f"Condition: {condition_expression}"
                ) from e

            logger.exception(f"Error in update_item: {str(e)}")
            raise

    def query(
        self,
        key: Union[Dict[str, Any], Key, ConditionBase, ComparisonCondition, DynamoDBIndex],
        table_name: str,
        *,
        index_name: Optional[str] = None,
        ascending: bool = False,
        source: Optional[str] = None,
        strongly_consistent: bool = False,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        start_key: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Query items from DynamoDB using a partition key and optional sort key condition.

        Query is the most efficient way to retrieve multiple items from DynamoDB.
        It requires a partition key value and can optionally filter by sort key.

        Args:
            key: Key condition expression. Can be:
                - dict: Simple key dictionary
                - Key: boto3 Key condition (e.g., Key("pk").eq("user#123"))
                - ConditionBase: boto3 condition object
                - ComparisonCondition: boto3 comparison condition
                - DynamoDBIndex: Index object with key information
            table_name: Name of the DynamoDB table.
            index_name: Name of the Global Secondary Index (GSI) or Local Secondary
                Index (LSI) to query. If None, queries the main table. If using
                DynamoDBIndex for `key`, this is extracted automatically.
            ascending: If True, sort results in ascending order by sort key.
                If False, descending order. Default: False.
            source: Optional identifier for logging/tracking. Default: None.
            strongly_consistent: If True, perform strongly consistent read.
                Only valid for table queries, not GSI queries. Default: False.
            projection_expression: Comma-separated list of attributes to retrieve.
                Reduces data transfer. Example: "id,name,email".
            expression_attribute_names: Map of placeholder names to actual names.
                Required for reserved words. Example: {"#status": "status"}.
            start_key: Key of the item to start from (for pagination).
                Use LastEvaluatedKey from previous query response.
            limit: Maximum number of items to evaluate (not necessarily return).
                Note: Filters are applied after this limit. Default: None (all items).

        Returns:
            Dictionary containing:
            - "Items": List of items matching the query
            - "Count": Number of items returned
            - "ScannedCount": Number of items evaluated
            - "LastEvaluatedKey": Key for pagination (if more results exist)
            - "ConsumedCapacity": Capacity info (if requested)

        Raises:
            ValueError: If key or table_name is missing or invalid.
            ClientError: If DynamoDB operation fails.

        Examples:
            Basic query by partition key:
                >>> from boto3.dynamodb.conditions import Key
                >>> db = DynamoDB()
                >>> response = db.query(
                ...     key=Key("pk").eq("user#123"),
                ...     table_name="users"
                ... )
                >>> items = response["Items"]

            Query with sort key condition:
                >>> response = db.query(
                ...     key=Key("pk").eq("user#123") & Key("sk").begins_with("order#"),
                ...     table_name="orders"
                ... )

            Query a GSI:
                >>> response = db.query(
                ...     key=Key("email").eq("john@example.com"),
                ...     table_name="users",
                ...     index_name="email-index"
                ... )

            Query with projection (specific fields only):
                >>> response = db.query(
                ...     key=Key("pk").eq("user#123"),
                ...     table_name="users",
                ...     projection_expression="id,name,email"
                ... )

            Reverse order (newest first):
                >>> response = db.query(
                ...     key=Key("pk").eq("user#123"),
                ...     table_name="posts",
                ...     ascending=False  # Descending order (default)
                ... )

            Pagination:
                >>> # First page
                >>> response = db.query(
                ...     key=Key("pk").eq("users#"),
                ...     table_name="users",
                ...     limit=10
                ... )
                >>> items = response["Items"]
                >>> last_key = response.get("LastEvaluatedKey")
                >>>
                >>> # Next page
                >>> if last_key:
                ...     response = db.query(
                ...         key=Key("pk").eq("users#"),
                ...         table_name="users",
                ...         limit=10,
                ...         start_key=last_key
                ...     )

            Using DynamoDBIndex:
                >>> index = DynamoDBIndex(name="email-index", pk="email", sk="created_at")
                >>> index.set_pk("john@example.com")
                >>> response = db.query(
                ...     key=index,
                ...     table_name="users"
                ... )

            Handling reserved words:
                >>> response = db.query(
                ...     key=Key("pk").eq("user#123"),
                ...     table_name="users",
                ...     projection_expression="id,#status",
                ...     expression_attribute_names={"#status": "status"}
                ... )

        Note:
            - Query is much more efficient than scan for retrieving items.
            - Partition key condition is required; sort key condition is optional.
            - GSI queries cannot use strongly_consistent reads.
            - Results are automatically paginated if more than 1MB of data.
            - Use limit for pagination, not for reducing costs (still evaluates items).
            - The `ascending` parameter defaults to False (descending order).
            - Use `start_key` with `LastEvaluatedKey` for pagination.

        See Also:
            - get(): Retrieve a single item by primary key
            - scan(): Retrieve all items (less efficient)
            - batch_get(): Retrieve multiple specific items
            - query_by_criteria(): Helper for model-based queries with projections
        """

        logger.debug({"action": "query", "source": source})
        if not key:
            raise ValueError("Query failed: key must be provided.")

        if not table_name:
            raise ValueError("Query failed: table_name must be provided.")

        if isinstance(key, DynamoDBIndex):
            if not index_name:
                index_name = key.name
            # turn it into a key expected by dynamodb
            key = key.key(query_key=True)

        kwargs: dict = {}

        if index_name and index_name != "primary":
            # only include the index_name if we are not using our "primary" pk/sk
            kwargs["IndexName"] = f"{index_name}"
        kwargs["TableName"] = f"{table_name}"
        kwargs["KeyConditionExpression"] = key
        kwargs["ScanIndexForward"] = ascending
        kwargs["ConsistentRead"] = strongly_consistent

        if projection_expression:
            kwargs["ProjectionExpression"] = projection_expression

        if expression_attribute_names:
            kwargs["ExpressionAttributeNames"] = expression_attribute_names

        if start_key:
            kwargs["ExclusiveStartKey"] = start_key

        if limit:
            kwargs["Limit"] = limit

        if table_name is None:
            raise ValueError("Query failed: table_name must be provided.")

        table = self.dynamodb_resource.Table(table_name)
        response: dict = {}
        try:
            response = dict(
                self._retry_on_throttle(
                    lambda: table.query(**kwargs),
                    operation_name="query",
                )
            )
        except Exception as e:  # pylint: disable=w0718
            logger.exception({"source": f"{source}", "metric_filter": "query", "error": str(e)})
            response = {"exception": str(e)}
            if self.raise_on_error:
                raise e

        # Apply decimal conversion to the response
        return self._apply_decimal_conversion(response)

    @overload
    def delete(self, *, table_name: str, model: DynamoDBModelBase) -> Dict[str, Any]:
        pass

    @overload
    def delete(
        self,
        *,
        table_name: str,
        primary_key: Dict[str, Any],
    ) -> Dict[str, Any]:
        pass

    def delete(
        self,
        *,
        primary_key: Optional[Dict[str, Any]] = None,
        table_name: Optional[str] = None,
        model: Optional[DynamoDBModelBase] = None,
    ) -> Dict[str, Any]:
        """
        Delete an item from DynamoDB.

        This method performs a DeleteItem operation, permanently removing an item
        from the table. The item is identified by its primary key (partition key
        and sort key if applicable).

        Args:
            primary_key: Primary key dictionary identifying the item to delete.
                Example: {"pk": "user#123", "sk": "profile#123"}.
                Cannot be used with `model` parameter.
            table_name: Name of the DynamoDB table. Required.
            model: DynamoDBModelBase instance to delete. The primary key will be
                extracted from the model's indexes. Cannot be used with `primary_key`.

        Returns:
            dict: DynamoDB response containing metadata about the deletion.
                Does not include the deleted item unless return_values is specified
                (not currently supported in this method).

        Raises:
            ValueError: If table_name is not provided, or if both primary_key and
                model are provided, or if neither is provided.
            ClientError: For DynamoDB errors (item not found, permission denied, etc.)

        Example:
            Delete by primary key::

                >>> db = DynamoDB()
                >>> db.delete(
                ...     table_name="users",
                ...     primary_key={"pk": "user#123", "sk": "profile#123"}
                ... )

            Delete using model::

                >>> user = User(id="123")
                >>> db.delete(table_name="users", model=user)

            Verify deletion::

                >>> db.delete(table_name="users", primary_key={"pk": "user#123"})
                >>> result = db.get(
                ...     table_name="users",
                ...     key={"pk": "user#123"}
                ... )
                >>> assert result is None  # Item was deleted

        Note:
            - This operation is permanent and cannot be undone
            - Consider implementing soft deletes (setting a deleted flag) for
              important data that may need to be recovered
            - For conditional deletes, use update_item() with a condition expression
            - For batch deletions, use batch_write() for better performance
            - DynamoDB does not return an error if the item doesn't exist

        See Also:
            - :meth:`batch_write`: For deleting multiple items efficiently
            - :meth:`update_item`: For conditional operations or soft deletes
            - :meth:`save`: For creating or updating items
        """

        if model is not None:
            if table_name is None:
                raise ValueError("table_name must be provided when model is used.")
            if primary_key is not None:
                raise ValueError("primary_key cannot be provided when model is used.")
            primary_key = model.indexes.primary.key()

        response = None

        if table_name is None or primary_key is None:
            raise ValueError("table_name and primary_key must be provided.")

        table = self.dynamodb_resource.Table(table_name)
        response = self._retry_on_throttle(
            lambda: table.delete_item(Key=primary_key),
            operation_name="delete",
        )

        return response

    def list_tables(self) -> List[str]:
        """
        Get a list of all table names from the current DynamoDB connection.

        This method retrieves all tables accessible with the current AWS credentials
        and region. Useful for discovery, validation, or administrative tasks.

        Returns:
            List[str]: List of table names. Empty list if no tables exist.

        Example:
            List all tables::

                >>> db = DynamoDB()
                >>> tables = db.list_tables()
                >>> print(f"Found {len(tables)} tables")
                >>> for table in tables:
                ...     print(f"  - {table}")

            Check if a table exists::

                >>> tables = db.list_tables()
                >>> if "users" in tables:
                ...     print("Users table exists")
                >>> else:
                ...     print("Users table not found")

        Note:
            - Returns only tables in the current region
            - Requires ListTables permission
            - May be slow if you have many tables (100+)
            - Consider caching the result if called frequently

        See Also:
            - :meth:`get`: For retrieving items from a table
            - :meth:`query`: For querying a specific table
        """
        tables = list(self.dynamodb_resource.tables.all())
        table_list: List[str] = []
        if len(tables) > 0:
            for table in tables:
                table_list.append(table.name)

        return table_list

    def query_by_criteria(
        self,
        *,
        model: DynamoDBModelBase,
        table_name: str,
        index_name: str,
        key: Union[Dict[str, Any], Key, ConditionBase, ComparisonCondition],
        start_key: Optional[Dict[str, Any]] = None,
        do_projections: bool = False,
        ascending: bool = False,
        strongly_consistent: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Query items using model-based projections and criteria.

        This is a convenience method that wraps the query() method with automatic
        projection expression handling from DynamoDBModelBase instances. Useful
        when you want to query with model-defined projections.

        Args:
            model: DynamoDBModelBase instance that defines projection expressions
            table_name: Name of the DynamoDB table
            index_name: Name of the GSI or LSI to query
            key: Key condition expression (dict, Key, or ConditionBase)
            start_key: Pagination key from previous query (optional)
            do_projections: If True, use model's projection expression (default: False)
            ascending: If True, sort results in ascending order (default: False)
            strongly_consistent: If True, use strongly consistent reads (default: False)
            limit: Maximum number of items to return (optional)

        Returns:
            dict: Query response with Items, Count, and optional LastEvaluatedKey

        Example:
            Query with model projections::

                >>> user = User()  # DynamoDBModelBase instance
                >>> response = db.query_by_criteria(
                ...     model=user,
                ...     table_name="users",
                ...     index_name="email-index",
                ...     key=Key("email").eq("user@example.com"),
                ...     do_projections=True
                ... )

        Note:
            - This is a convenience wrapper around query()
            - For more control, use query() directly
            - Projections are only applied if do_projections=True

        See Also:
            - :meth:`query`: For direct query operations
            - :class:`DynamoDBModelBase`: For model definitions
        """

        projection_expression: str | None = None
        expression_attribute_names: dict | None = None

        if do_projections:
            projection_expression = model.projection_expression
            expression_attribute_names = model.projection_expression_attribute_names

        response = self.query(
            key=key,
            index_name=index_name,
            table_name=table_name,
            start_key=start_key,
            projection_expression=projection_expression,
            expression_attribute_names=expression_attribute_names,
            ascending=ascending,
            strongly_consistent=strongly_consistent,
            limit=limit,
        )

        return response

    def has_more_records(self, response: Dict[str, Any]) -> bool:
        """
        Check if a DynamoDB response has more records to paginate through.

        This method checks for the presence of LastEvaluatedKey in the response,
        which indicates that the query or scan operation has more results available.

        Args:
            response: DynamoDB response dictionary from query() or scan()

        Returns:
            bool: True if more records exist, False if this was the last page

        Example:
            Paginate through all results::

                >>> db = DynamoDB()
                >>> start_key = None
                >>> all_items = []
                >>>
                >>> while True:
                ...     response = db.query(
                ...         key=Key("pk").eq("user#123"),
                ...         table_name="users",
                ...         start_key=start_key
                ...     )
                ...     all_items.extend(response['Items'])
                ...
                ...     if not db.has_more_records(response):
                ...         break
                ...     start_key = db.last_key(response)
                >>>
                >>> print(f"Retrieved {len(all_items)} total items")

        See Also:
            - :meth:`last_key`: Get the pagination key for the next request
            - :meth:`query`: For querying with pagination
        """

        return "LastEvaluatedKey" in response

    def last_key(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract the LastEvaluatedKey from a DynamoDB response for pagination.

        The LastEvaluatedKey is used as the start_key parameter in the next
        query or scan request to continue retrieving results.

        Args:
            response: DynamoDB response dictionary from query() or scan()

        Returns:
            dict | None: The LastEvaluatedKey dictionary if more results exist,
                None if this was the last page

        Example:
            Use last_key for pagination::

                >>> response = db.query(
                ...     key=Key("pk").eq("user#123"),
                ...     table_name="users"
                ... )
                >>>
                >>> next_key = db.last_key(response)
                >>> if next_key:
                ...     next_response = db.query(
                ...         key=Key("pk").eq("user#123"),
                ...         table_name="users",
                ...         start_key=next_key
                ...     )

        See Also:
            - :meth:`has_more_records`: Check if more records exist
            - :meth:`query`: For querying with pagination
        """

        return response.get("LastEvaluatedKey")

    def items(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract the Items list from a DynamoDB response.

        This is a convenience method to safely extract items from query(),
        scan(), or batch_get_item() responses.

        Args:
            response: DynamoDB response dictionary

        Returns:
            list: List of items from the response. Empty list if no items found.

        Example:
            Extract items from query response::

                >>> response = db.query(
                ...     key=Key("pk").eq("user#123"),
                ...     table_name="users"
                ... )
                >>> items = db.items(response)
                >>> for item in items:
                ...     print(item['name'])

            Safe extraction (no KeyError)::

                >>> response = db.query(...)
                >>> items = db.items(response)  # Returns [] if no Items key
                >>> print(f"Found {len(items)} items")

        See Also:
            - :meth:`item`: Extract single item from get() response
            - :meth:`query`: For querying items
        """

        return response.get("Items", [])

    def item(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the Item from a DynamoDB get() response.

        This is a convenience method to safely extract a single item from
        a get() operation response.

        Args:
            response: DynamoDB response dictionary from get()

        Returns:
            dict: The item dictionary. Empty dict if item not found.

        Example:
            Extract item from get response::

                >>> response = db.get(
                ...     table_name="users",
                ...     key={"pk": "user#123", "sk": "user#123"}
                ... )
                >>> item = db.item(response)
                >>> if item:
                ...     print(f"User: {item['name']}")
                >>> else:
                ...     print("User not found")

        Note:
            - Returns empty dict {} if item doesn't exist
            - For query/scan responses, use items() instead

        See Also:
            - :meth:`items`: Extract items list from query/scan response
            - :meth:`get`: For retrieving single items
        """

        return response.get("Item", {})

        return response.get("Item", {})

    def batch_get_item(
        self,
        keys: List[Dict[str, Any]],
        table_name: str,
        *,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        consistent_read: bool = False,
    ) -> Dict[str, Any]:
        """
        Retrieve multiple items from DynamoDB in a single request.

        DynamoDB allows up to 100 items per batch_get_item call. This method
        automatically chunks larger requests and handles unprocessed keys with
        exponential backoff retry logic.

        Args:
            keys: List of key dictionaries. Each dict must contain the primary key
                  (and sort key if applicable) for the items to retrieve.
                  Example: [{"pk": "user#1", "sk": "user#1"}, {"pk": "user#2", "sk": "user#2"}]
            table_name: The DynamoDB table name
            projection_expression: Optional comma-separated list of attributes to retrieve
            expression_attribute_names: Optional dict mapping attribute name placeholders to actual names
            consistent_read: If True, uses strongly consistent reads (costs more RCUs)

        Returns:
            dict: Response containing:
                - 'Items': List of retrieved items (with Decimal conversion applied)
                - 'UnprocessedKeys': Any keys that couldn't be processed after retries
                - 'ConsumedCapacity': Capacity units consumed (if available)

        Example:
            >>> keys = [
            ...     {"pk": "user#user-001", "sk": "user#user-001"},
            ...     {"pk": "user#user-002", "sk": "user#user-002"},
            ...     {"pk": "user#user-003", "sk": "user#user-003"}
            ... ]
            >>> response = db.batch_get_item(keys=keys, table_name="users")
            >>> items = response['Items']
            >>> print(f"Retrieved {len(items)} items")

        Note:
            - Maximum 100 items per request (automatically chunked)
            - Each item can be up to 400 KB
            - Maximum 16 MB total response size
            - Unprocessed keys are automatically retried with exponential backoff
        """
        import time

        all_items = []
        unprocessed_keys = []

        # DynamoDB limit: 100 items per batch_get_item call
        BATCH_SIZE = 100

        # Chunk keys into batches of 100
        for i in range(0, len(keys), BATCH_SIZE):
            batch_keys = keys[i : i + BATCH_SIZE]

            # Build request parameters
            request_items = {table_name: {"Keys": batch_keys, "ConsistentRead": consistent_read}}

            # Add projection if provided
            if projection_expression:
                request_items[table_name]["ProjectionExpression"] = projection_expression
            if expression_attribute_names:
                request_items[table_name]["ExpressionAttributeNames"] = expression_attribute_names

            # Retry logic for unprocessed keys
            max_retries = 5
            retry_count = 0
            backoff_time = 0.1  # Start with 100ms

            while retry_count <= max_retries:
                try:
                    response = self.dynamodb_resource.meta.client.batch_get_item(
                        RequestItems=request_items
                    )

                    # Collect items from this batch
                    if "Responses" in response and table_name in response["Responses"]:
                        batch_items = response["Responses"][table_name]
                        all_items.extend(batch_items)

                    # Check for unprocessed keys
                    if "UnprocessedKeys" in response and response["UnprocessedKeys"]:
                        if table_name in response["UnprocessedKeys"]:
                            unprocessed = response["UnprocessedKeys"][table_name]

                            if retry_count < max_retries:
                                # Retry with exponential backoff
                                logger.warning(
                                    f"Batch get has {len(unprocessed['Keys'])} unprocessed keys. "
                                    f"Retrying in {backoff_time}s (attempt {retry_count + 1}/{max_retries})"
                                )
                                time.sleep(backoff_time)
                                request_items = {table_name: unprocessed}
                                backoff_time *= 2  # Exponential backoff
                                retry_count += 1
                                continue
                            else:
                                # Max retries reached, collect remaining unprocessed keys
                                logger.error(
                                    f"Max retries reached. {len(unprocessed['Keys'])} keys remain unprocessed"
                                )
                                unprocessed_keys.extend(unprocessed["Keys"])
                                break
                    else:
                        # No unprocessed keys, we're done with this batch
                        break

                except ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    if (
                        error_code == "ProvisionedThroughputExceededException"
                        and retry_count < max_retries
                    ):
                        logger.warning(
                            f"Throughput exceeded. Retrying in {backoff_time}s (attempt {retry_count + 1}/{max_retries})"
                        )
                        time.sleep(backoff_time)
                        backoff_time *= 2
                        retry_count += 1
                        continue
                    else:
                        logger.exception(f"Error in batch_get_item: {str(e)}")
                        raise

        # Apply decimal conversion to all items
        result = {
            "Items": all_items,
            "Count": len(all_items),
            "UnprocessedKeys": unprocessed_keys,
        }

        return self._apply_decimal_conversion(result)

    def batch_write_item(
        self, items: List[Dict[str, Any]], table_name: str, *, operation: str = "put"
    ) -> Dict[str, Any]:
        """
        Write or delete multiple items in a single batch request.

        Batch write operations allow you to efficiently put or delete up to 25 items
        in a single request. This method automatically handles chunking for larger
        batches and retries unprocessed items with exponential backoff.

        Important: Batch writes are NOT atomic. If some items fail, others may still
        succeed. For atomic multi-item operations, use transact_write_items() instead.

        Args:
            items: List of item dictionaries to write or delete.
                - For 'put' operation: Full item dictionaries with all attributes
                  Example: [{"pk": "user#1", "name": "Alice", "email": "alice@example.com"}]
                - For 'delete' operation: Key-only dictionaries (partition key and sort key)
                  Example: [{"pk": "user#1", "sk": "profile#1"}]
            table_name: Name of the DynamoDB table.
            operation: Operation type. Either 'put' (default) or 'delete'.
                - 'put': Creates new items or replaces existing items
                - 'delete': Removes items by their primary keys

        Returns:
            dict: Response containing:
                - 'ProcessedCount': Number of successfully processed items
                - 'UnprocessedCount': Number of items that couldn't be processed
                - 'UnprocessedItems': List of items that failed after all retries

        Raises:
            ValueError: If operation is not 'put' or 'delete'
            ClientError: For DynamoDB errors (throttling, permission denied, etc.)

        Example:
            Batch put multiple items::

                >>> db = DynamoDB()
                >>> items = [
                ...     {"pk": "user#1", "sk": "user#1", "name": "Alice", "age": 30},
                ...     {"pk": "user#2", "sk": "user#2", "name": "Bob", "age": 25},
                ...     {"pk": "user#3", "sk": "user#3", "name": "Charlie", "age": 35}
                ... ]
                >>> response = db.batch_write_item(items=items, table_name="users")
                >>> print(f"Processed {response['ProcessedCount']} items")
                Processed 3 items

            Batch delete multiple items::

                >>> keys = [
                ...     {"pk": "user#1", "sk": "user#1"},
                ...     {"pk": "user#2", "sk": "user#2"}
                ... ]
                >>> response = db.batch_write_item(
                ...     items=keys,
                ...     table_name="users",
                ...     operation="delete"
                ... )

            Handle unprocessed items::

                >>> response = db.batch_write_item(items=large_batch, table_name="users")
                >>> if response['UnprocessedCount'] > 0:
                ...     print(f"Warning: {response['UnprocessedCount']} items not processed")
                ...     # Optionally retry or log unprocessed items
                ...     unprocessed = response['UnprocessedItems']

            Mixed operations (put and delete in same batch)::

                >>> # Note: This requires manual construction
                >>> # Use separate batch_write_item calls for put and delete
                >>> db.batch_write_item(items=items_to_add, table_name="users", operation="put")
                >>> db.batch_write_item(items=keys_to_delete, table_name="users", operation="delete")

        Note:
            - **Maximum 25 operations per request** (automatically chunked for larger batches)
            - Each item can be up to 400 KB
            - Maximum 16 MB total request size
            - **Not atomic**: Some items may succeed while others fail
            - No conditional writes in batch operations (use transact_write for conditions)
            - Unprocessed items are automatically retried up to 5 times with exponential backoff
            - DynamoDB may throttle batch operations during high traffic
            - For atomic operations, use transact_write_items() instead

        See Also:
            - :meth:`batch_get_item`: For batch read operations
            - :meth:`transact_write_items`: For atomic multi-item writes
            - :meth:`save`: For single item writes with conditions
            - :meth:`delete`: For single item deletes
        """
        import time

        if operation not in ["put", "delete"]:
            raise ValueError(f"Invalid operation '{operation}'. Must be 'put' or 'delete'")

        # DynamoDB limit: 25 operations per batch_write_item call
        BATCH_SIZE = 25

        total_processed = 0
        all_unprocessed = []

        # Chunk items into batches of 25
        for i in range(0, len(items), BATCH_SIZE):
            batch_items = items[i : i + BATCH_SIZE]

            # Build request items
            write_requests = []
            for item in batch_items:
                if operation == "put":
                    write_requests.append({"PutRequest": {"Item": item}})
                else:  # delete
                    write_requests.append({"DeleteRequest": {"Key": item}})

            request_items = {table_name: write_requests}

            # Retry logic for unprocessed items
            max_retries = 5
            retry_count = 0
            backoff_time = 0.1  # Start with 100ms

            while retry_count <= max_retries:
                try:
                    response = self.dynamodb_resource.meta.client.batch_write_item(
                        RequestItems=request_items
                    )

                    # Count processed items from this batch
                    processed_in_batch = len(batch_items)

                    # Check for unprocessed items
                    if "UnprocessedItems" in response and response["UnprocessedItems"]:
                        if table_name in response["UnprocessedItems"]:
                            unprocessed = response["UnprocessedItems"][table_name]
                            unprocessed_count = len(unprocessed)
                            processed_in_batch -= unprocessed_count

                            if retry_count < max_retries:
                                # Retry with exponential backoff
                                logger.warning(
                                    f"Batch write has {unprocessed_count} unprocessed items. "
                                    f"Retrying in {backoff_time}s (attempt {retry_count + 1}/{max_retries})"
                                )
                                time.sleep(backoff_time)
                                request_items = {table_name: unprocessed}
                                backoff_time *= 2  # Exponential backoff
                                retry_count += 1
                                continue
                            else:
                                # Max retries reached
                                logger.error(
                                    f"Max retries reached. {unprocessed_count} items remain unprocessed"
                                )
                                all_unprocessed.extend(unprocessed)
                                break

                    # Successfully processed this batch
                    total_processed += processed_in_batch
                    break

                except ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    if (
                        error_code == "ProvisionedThroughputExceededException"
                        and retry_count < max_retries
                    ):
                        logger.warning(
                            f"Throughput exceeded. Retrying in {backoff_time}s (attempt {retry_count + 1}/{max_retries})"
                        )
                        time.sleep(backoff_time)
                        backoff_time *= 2
                        retry_count += 1
                        continue
                    else:
                        logger.exception(f"Error in batch_write_item: {str(e)}")
                        raise

        return {
            "ProcessedCount": total_processed,
            "UnprocessedCount": len(all_unprocessed),
            "UnprocessedItems": all_unprocessed,
        }

    def transact_write_items(
        self,
        operations: List[Dict[str, Any]],
        *,
        client_request_token: Optional[str] = None,
        return_consumed_capacity: str = "NONE",
        return_item_collection_metrics: str = "NONE",
    ) -> Dict[str, Any]:
        """
        Execute multiple write operations as an ACID transaction.

        Transactions provide atomicity, consistency, isolation, and durability (ACID)
        guarantees. All operations in the transaction succeed together or fail together,
        ensuring data consistency across multiple items and tables.

        This is essential for operations like:
        - Transferring money between accounts
        - Updating inventory and order status together
        - Maintaining referential integrity across items

        Args:
            operations: List of transaction operation dictionaries. Each operation must
                contain exactly one of: 'Put', 'Update', 'Delete', or 'ConditionCheck'.

                Operation types:
                - **Put**: Insert or replace an item
                - **Update**: Modify specific attributes
                - **Delete**: Remove an item
                - **ConditionCheck**: Verify a condition without modifying data

                Example structure::

                    [
                        {
                            'Put': {
                                'TableName': 'users',
                                'Item': {'pk': 'user#1', 'name': 'Alice'},
                                'ConditionExpression': 'attribute_not_exists(pk)'
                            }
                        },
                        {
                            'Update': {
                                'TableName': 'accounts',
                                'Key': {'pk': 'account#1'},
                                'UpdateExpression': 'SET balance = balance - :amt',
                                'ExpressionAttributeValues': {':amt': 100}
                            }
                        }
                    ]

            client_request_token: Optional idempotency token (UUID recommended).
                Ensures the same transaction isn't executed twice if retried.
            return_consumed_capacity: Capacity reporting level:
                - 'NONE' (default): No capacity information
                - 'TOTAL': Total capacity consumed
                - 'INDEXES': Capacity per table and index
            return_item_collection_metrics: Collection metrics level:
                - 'NONE' (default): No metrics
                - 'SIZE': Size metrics for affected items

        Returns:
            dict: Transaction response containing:
                - 'ConsumedCapacity': List of capacity consumed per table (if requested)
                - 'ItemCollectionMetrics': Metrics about affected items (if requested)

        Raises:
            ValueError: If operations list is empty or exceeds 100 items
            TransactionCanceledException: If transaction fails due to:
                - Conditional check failure on any operation
                - Item size exceeds 400 KB
                - Throughput exceeded
                - Duplicate item in transaction
            ClientError: For other DynamoDB errors

        Example:
            Transfer money between accounts atomically::

                >>> db = DynamoDB()
                >>> operations = [
                ...     {
                ...         'Update': {
                ...             'TableName': 'accounts',
                ...             'Key': {'pk': 'account#sender', 'sk': 'account#sender'},
                ...             'UpdateExpression': 'SET balance = balance - :amount',
                ...             'ExpressionAttributeValues': {':amount': 100},
                ...             'ConditionExpression': 'balance >= :amount'  # Prevent overdraft
                ...         }
                ...     },
                ...     {
                ...         'Update': {
                ...             'TableName': 'accounts',
                ...             'Key': {'pk': 'account#receiver', 'sk': 'account#receiver'},
                ...             'UpdateExpression': 'SET balance = balance + :amount',
                ...             'ExpressionAttributeValues': {':amount': 100}
                ...         }
                ...     }
                ... ]
                >>> try:
                ...     response = db.transact_write_items(operations=operations)
                ...     print("Transfer successful!")
                ... except Exception as e:
                ...     print(f"Transfer failed: {e}")
                ...     # Both accounts remain unchanged

            Create order and update inventory atomically::

                >>> operations = [
                ...     {
                ...         'Put': {
                ...             'TableName': 'orders',
                ...             'Item': {
                ...                 'pk': 'order#123',
                ...                 'sk': 'order#123',
                ...                 'user_id': 'user#456',
                ...                 'product_id': 'product#789',
                ...                 'quantity': 2,
                ...                 'status': 'pending'
                ...             },
                ...             'ConditionExpression': 'attribute_not_exists(pk)'
                ...         }
                ...     },
                ...     {
                ...         'Update': {
                ...             'TableName': 'inventory',
                ...             'Key': {'pk': 'product#789', 'sk': 'inventory'},
                ...             'UpdateExpression': 'SET stock = stock - :qty',
                ...             'ExpressionAttributeValues': {':qty': 2},
                ...             'ConditionExpression': 'stock >= :qty'  # Ensure stock available
                ...         }
                ...     }
                ... ]
                >>> response = db.transact_write_items(operations=operations)

            Use condition check to verify state::

                >>> operations = [
                ...     {
                ...         'ConditionCheck': {
                ...             'TableName': 'users',
                ...             'Key': {'pk': 'user#123', 'sk': 'user#123'},
                ...             'ConditionExpression': 'account_status = :status',
                ...             'ExpressionAttributeValues': {':status': 'active'}
                ...         }
                ...     },
                ...     {
                ...         'Put': {
                ...             'TableName': 'orders',
                ...             'Item': {'pk': 'order#456', 'user_id': 'user#123'}
                ...         }
                ...     }
                ... ]
                >>> response = db.transact_write_items(operations=operations)

            With idempotency token for safe retries::

                >>> import uuid
                >>> token = str(uuid.uuid4())
                >>> response = db.transact_write_items(
                ...     operations=operations,
                ...     client_request_token=token
                ... )
                >>> # Safe to retry with same token if network fails

        Note:
            - **ACID Guarantees**: All operations succeed or all fail (atomicity)
            - **Maximum 100 operations** per transaction (AWS limit as of 2023)
            - Each item can be up to 400 KB
            - Maximum 4 MB total transaction size
            - **Cannot target the same item twice** in one transaction
            - Uses **strongly consistent reads** for all condition checks
            - More expensive than batch operations (2x write capacity units)
            - Transactions can fail due to conflicts with other transactions
            - Consider using idempotency tokens for retry safety
            - For non-atomic batch operations, use batch_write_item() instead

        See Also:
            - :meth:`transact_get_items`: For atomic multi-item reads
            - :meth:`batch_write_item`: For non-atomic batch writes
            - :meth:`update_item`: For single item updates with conditions
            - :meth:`save`: For single item writes
        """
        if not operations:
            raise ValueError("At least one operation is required")

        if len(operations) > 100:
            raise ValueError(
                f"Transaction supports maximum 100 operations, got {len(operations)}. "
                "Consider splitting into multiple transactions."
            )

        params = {
            "TransactItems": operations,
            "ReturnConsumedCapacity": return_consumed_capacity,
            "ReturnItemCollectionMetrics": return_item_collection_metrics,
        }

        if client_request_token:
            params["ClientRequestToken"] = client_request_token

        try:
            response = self.dynamodb_resource.meta.client.transact_write_items(**params)
            return response

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "TransactionCanceledException":
                # Parse cancellation reasons
                reasons = e.response.get("CancellationReasons", [])
                logger.error(f"Transaction cancelled. Reasons: {reasons}")

                # Enhance error message with specific reason
                if reasons:
                    reason_messages = []
                    for idx, reason in enumerate(reasons):
                        if reason.get("Code"):
                            reason_messages.append(
                                f"Operation {idx}: {reason['Code']} - {reason.get('Message', '')}"
                            )

                    raise RuntimeError(f"Transaction failed: {'; '.join(reason_messages)}") from e

            logger.exception(f"Error in transact_write_items: {str(e)}")
            raise

    def transact_get_items(
        self, keys: List[Dict[str, Any]], *, return_consumed_capacity: str = "NONE"
    ) -> Dict[str, Any]:
        """
        Retrieve multiple items with strong consistency in a single transaction.

        Transaction get provides a consistent snapshot across all requested items,
        ensuring you read all items as they existed at the same point in time.
        This is essential when you need to read related items that must be consistent
        with each other (e.g., reading an order and its associated inventory levels).

        Unlike batch_get_item which may return eventually consistent data, transact_get
        always uses strongly consistent reads and provides snapshot isolation.

        Args:
            keys: List of get operation dictionaries. Each dictionary specifies one
                item to retrieve and must contain:

                Required fields:
                - **Key**: Primary key dictionary (partition key and sort key if applicable)
                - **TableName**: Name of the table

                Optional fields:
                - **ProjectionExpression**: Comma-separated list of attributes to retrieve
                - **ExpressionAttributeNames**: Mapping for reserved words or special characters

                Example structure::

                    [
                        {
                            'Key': {'pk': 'user#1', 'sk': 'user#1'},
                            'TableName': 'users'
                        },
                        {
                            'Key': {'pk': 'order#123', 'sk': 'order#123'},
                            'TableName': 'orders',
                            'ProjectionExpression': 'id, total, #status',
                            'ExpressionAttributeNames': {'#status': 'status'}
                        }
                    ]

            return_consumed_capacity: Capacity reporting level:
                - 'NONE' (default): No capacity information
                - 'TOTAL': Total capacity consumed
                - 'INDEXES': Capacity per table and index

        Returns:
            dict: Response containing:
                - 'Items': List of retrieved items (with Decimal conversion applied)
                - 'Count': Number of items retrieved
                - 'ConsumedCapacity': Capacity consumed per table (if requested)

        Raises:
            ValueError: If keys list is empty or exceeds 100 items
            ClientError: For DynamoDB errors (item not found, permission denied, etc.)

        Example:
            Get multiple items with consistent snapshot::

                >>> db = DynamoDB()
                >>> keys = [
                ...     {
                ...         'Key': {'pk': 'user#123', 'sk': 'user#123'},
                ...         'TableName': 'users'
                ...     },
                ...     {
                ...         'Key': {'pk': 'account#123', 'sk': 'account#123'},
                ...         'TableName': 'accounts'
                ...     }
                ... ]
                >>> response = db.transact_get_items(keys=keys)
                >>> items = response['Items']
                >>> print(f"Retrieved {response['Count']} items")

            Get items with projection::

                >>> keys = [
                ...     {
                ...         'Key': {'pk': 'order#123', 'sk': 'order#123'},
                ...         'TableName': 'orders',
                ...         'ProjectionExpression': 'id, total, items'
                ...     },
                ...     {
                ...         'Key': {'pk': 'user#456', 'sk': 'user#456'},
                ...         'TableName': 'users',
                ...         'ProjectionExpression': 'id, email, #name',
                ...         'ExpressionAttributeNames': {'#name': 'name'}
                ...     }
                ... ]
                >>> response = db.transact_get_items(keys=keys)

            Cross-table consistent read::

                >>> # Read order and inventory levels consistently
                >>> keys = [
                ...     {
                ...         'Key': {'pk': 'order#789', 'sk': 'order#789'},
                ...         'TableName': 'orders'
                ...     },
                ...     {
                ...         'Key': {'pk': 'product#123', 'sk': 'inventory'},
                ...         'TableName': 'inventory'
                ...     },
                ...     {
                ...         'Key': {'pk': 'product#456', 'sk': 'inventory'},
                ...         'TableName': 'inventory'
                ...     }
                ... ]
                >>> response = db.transact_get_items(keys=keys)
                >>> order, inv1, inv2 = response['Items']
                >>> # All items reflect the same point in time

            Handle missing items::

                >>> response = db.transact_get_items(keys=keys)
                >>> if response['Count'] < len(keys):
                ...     print("Some items were not found")
                >>> # Items that don't exist are simply not included in response

        Note:
            - **Maximum 100 items** per transaction (AWS limit)
            - **Always uses strongly consistent reads** (cannot be eventually consistent)
            - **More expensive than batch_get_item** (2x read capacity units)
            - Provides **snapshot isolation** - all items read at same point in time
            - Items that don't exist are not included in the response (no error)
            - Cannot be combined with transact_write_items in same transaction
            - Each item can be up to 400 KB
            - Maximum 4 MB total response size
            - Use batch_get_item for eventually consistent reads or > 100 items

        See Also:
            - :meth:`transact_write_items`: For atomic multi-item writes
            - :meth:`batch_get_item`: For eventually consistent batch reads
            - :meth:`get`: For single item reads
            - :meth:`query`: For querying multiple items with a partition key
        """
        if not keys:
            raise ValueError("At least one key is required")

        if len(keys) > 100:
            raise ValueError(
                f"Transaction supports maximum 100 items, got {len(keys)}. "
                "Use batch_get_item for larger requests."
            )

        # Build transaction get items
        transact_items = []
        for key_spec in keys:
            get_item = {"Get": key_spec}
            transact_items.append(get_item)

        params = {
            "TransactItems": transact_items,
            "ReturnConsumedCapacity": return_consumed_capacity,
        }

        try:
            response = self.dynamodb_resource.meta.client.transact_get_items(**params)

            # Extract items from response
            items = []
            if "Responses" in response:
                for item_response in response["Responses"]:
                    if "Item" in item_response:
                        items.append(item_response["Item"])

            result = {"Items": items, "Count": len(items)}

            if "ConsumedCapacity" in response:
                result["ConsumedCapacity"] = response["ConsumedCapacity"]

            # Apply decimal conversion
            return self._apply_decimal_conversion(result)

        except ClientError as e:
            logger.exception(f"Error in transact_get_items: {str(e)}")
            raise
