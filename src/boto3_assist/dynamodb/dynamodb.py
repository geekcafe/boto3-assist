"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
from typing import List, Optional, overload, Dict, Any
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import (
    Key,
    # And,
    # Equals,
    ComparisonCondition,
    ConditionBase,
)
from .dynamodb_connection import DynamoDBConnection
from .dynamodb_helpers import DynamoDBHelpers
from .dynamodb_model_base import DynamoDBModelBase
from ..utilities.string_utility import StringUtility
from ..utilities.decimal_conversion_utility import DecimalConversionUtility
from .dynamodb_index import DynamoDBIndex

logger = Logger()


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

    def save(
        self,
        item: dict | DynamoDBModelBase,
        table_name: str,
        source: Optional[str] = None,
        fail_if_exists: bool = False,
        condition_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        expression_attribute_values: Optional[dict] = None,
    ) -> dict:
        """
        Save an item to the database with optional conditional expressions.

        Args:
            item (dict): DynamoDB Dictionary Object or DynamoDBModelBase.
                Supports the "client" or "resource" syntax
            table_name (str): The DynamoDb Table Name
            source (str, optional): The source of the call, used for logging. Defaults to None.
            fail_if_exists (bool, optional): Only allow it to insert once.
                Fail if it already exits. This is useful for loggers, historical records,
                tasks, etc. that should only be created once
            condition_expression (str, optional): Custom condition expression.
                Example: "attribute_not_exists(#pk)" or "#version = :expected_version"
            expression_attribute_names (dict, optional): Attribute name mappings.
                Example: {"#version": "version", "#status": "status"}
            expression_attribute_values (dict, optional): Attribute value mappings.
                Example: {":expected_version": 1, ":active": "active"}

        Raises:
            ClientError: Client specific errors
            RuntimeError: Conditional check failed
            Exception: Any Error Raised

        Returns:
            dict: The Response from DynamoDB's put_item actions.
            It does not return the saved object, only the response.

        Examples:
            >>> # Simple save
            >>> db.save(item=user, table_name="users")

            >>> # Prevent duplicates
            >>> db.save(item=user, table_name="users", fail_if_exists=True)

            >>> # Optimistic locking with version check
            >>> db.save(
            ...     item=user,
            ...     table_name="users",
            ...     condition_expression="#version = :expected_version",
            ...     expression_attribute_names={"#version": "version"},
            ...     expression_attribute_values={":expected_version": 5}
            ... )
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
                        params["ExpressionAttributeValues"] = (
                            expression_attribute_values
                        )
                elif fail_if_exists:
                    # only insert if the item does *not* already exist
                    params["ConditionExpression"] = (
                        "attribute_not_exists(#pk) AND attribute_not_exists(#sk)"
                    )
                    params["ExpressionAttributeNames"] = {"#pk": "pk", "#sk": "sk"}

                response = dict(self.dynamodb_client.put_item(**params))

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
                        put_params["ExpressionAttributeNames"] = (
                            expression_attribute_names
                        )
                    if expression_attribute_values:
                        put_params["ExpressionAttributeValues"] = (
                            expression_attribute_values
                        )
                elif fail_if_exists:
                    put_params["ConditionExpression"] = (
                        Attr("pk").not_exists() & Attr("sk").not_exists()
                    )

                response = dict(table.put_item(**put_params))

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
                    raise RuntimeError(
                        f"Conditional check failed for item in {table_name}"
                    ) from e

            logger.exception(
                {"source": f"{source}", "metric_filter": "put_item", "error": str(e)}
            )
            raise

        except Exception as e:  # pylint: disable=w0718
            logger.exception(
                {"source": f"{source}", "metric_filter": "put_item", "error": str(e)}
            )
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
        expression_attribute_names: Optional[dict] = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> Dict[str, Any]: ...

    @overload
    def get(
        self,
        key: dict,
        table_name: str,
        *,
        strongly_consistent: bool = False,
        return_consumed_capacity: Optional[str] = None,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> Dict[str, Any]: ...

    def get(
        self,
        key: Optional[dict] = None,
        table_name: Optional[str] = None,
        model: Optional[DynamoDBModelBase] = None,
        do_projections: bool = False,
        strongly_consistent: bool = False,
        return_consumed_capacity: Optional[str] = None,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> Dict[str, Any]:
        """
        Description:
            generic get_item dynamoDb call
        Parameters:
            key: a dictionary object representing the primary key
            model: a model instance of DynamoDBModelBase
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
                response = dict(table.get_item(Key=key, **valid_kwargs))  # type: ignore[arg-type]
            elif call_type == "client":
                response = dict(
                    self.dynamodb_client.get_item(
                        Key=key,
                        TableName=table_name,
                        **valid_kwargs,  # type: ignore[arg-type]
                    )
                )
            else:
                raise ValueError(
                    f"Unknown call_type of {call_type}. Supported call_types [resource | client]"
                )
        except Exception as e:  # pylint: disable=w0718
            logger.exception(
                {"source": f"{source}", "metric_filter": "get_item", "error": str(e)}
            )

            response = {"exception": str(e)}
            if self.raise_on_error:
                raise e

        # Apply decimal conversion to the response
        return self._apply_decimal_conversion(response)

    def update_item(
        self,
        table_name: str,
        key: dict,
        update_expression: str,
        expression_attribute_values: Optional[dict] = None,
        expression_attribute_names: Optional[dict] = None,
        condition_expression: Optional[str] = None,
        return_values: str = "NONE",
    ) -> dict:
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
            response = dict(table.update_item(**params))

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
        key: dict | Key | ConditionBase | ComparisonCondition | DynamoDBIndex,
        table_name: str,
        *,
        index_name: Optional[str] = None,
        ascending: bool = False,
        source: Optional[str] = None,
        strongly_consistent: bool = False,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        start_key: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> dict:
        """
        Run a query and return a list of items
        Args:
            key (Key): _description_
            index_name (str, optional): _description_. Defaults to None.
            ascending (bool, optional): _description_. Defaults to False.
            table_name (str, optional): _description_. Defaults to None.
            source (str, optional): The source of the query.  Used for logging. Defaults to None.

        Returns:
            dict: dynamodb response dictionary
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
            response = dict(table.query(**kwargs))
        except Exception as e:  # pylint: disable=w0718
            logger.exception(
                {"source": f"{source}", "metric_filter": "query", "error": str(e)}
            )
            response = {"exception": str(e)}
            if self.raise_on_error:
                raise e

        # Apply decimal conversion to the response
        return self._apply_decimal_conversion(response)

    @overload
    def delete(self, *, table_name: str, model: DynamoDBModelBase) -> dict:
        pass

    @overload
    def delete(
        self,
        *,
        table_name: str,
        primary_key: dict,
    ) -> dict:
        pass

    def delete(
        self,
        *,
        primary_key: Optional[dict] = None,
        table_name: Optional[str] = None,
        model: Optional[DynamoDBModelBase] = None,
    ):
        """deletes an item from the database"""

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
        response = table.delete_item(Key=primary_key)

        return response

    def list_tables(self) -> List[str]:
        """Get a list of tables from the current connection"""
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
        key: dict | Key | ConditionBase | ComparisonCondition,
        start_key: Optional[dict] = None,
        do_projections: bool = False,
        ascending: bool = False,
        strongly_consistent: bool = False,
        limit: Optional[int] = None,
    ) -> dict:
        """Helper function to list by criteria"""

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

    def has_more_records(self, response: dict) -> bool:
        """
        Check if there are more records to process.
        This based on the existance of the LastEvaluatedKey in the response.
        Parameters:
            response (dict): dynamodb response dictionary

        Returns:
            bool: True if there are more records, False otherwise
        """

        return "LastEvaluatedKey" in response

    def last_key(self, response: dict) -> dict | None:
        """
        Get the LastEvaluatedKey, which can be used to continue processing the results
        Parameters:
            response (dict): dynamodb response dictionary

        Returns:
            dict | None: The last key or None if not found
        """

        return response.get("LastEvaluatedKey")

    def items(self, response: dict) -> list:
        """
        Get the Items from the dynamodb response
        Parameters:
            response (dict): dynamodb response dictionary

        Returns:
            list: A list or empty array/list if no items found
        """

        return response.get("Items", [])

    def item(self, response: dict) -> dict:
        """
        Get the Item from the dynamodb response
        Parameters:
            response (dict): dynamodb response dictionary

        Returns:
            dict: A dictionary or empty dictionary if no item found
        """

        return response.get("Item", {})

    def batch_get_item(
        self,
        keys: list[dict],
        table_name: str,
        *,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        consistent_read: bool = False,
    ) -> dict:
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
            request_items = {
                table_name: {"Keys": batch_keys, "ConsistentRead": consistent_read}
            }

            # Add projection if provided
            if projection_expression:
                request_items[table_name][
                    "ProjectionExpression"
                ] = projection_expression
            if expression_attribute_names:
                request_items[table_name][
                    "ExpressionAttributeNames"
                ] = expression_attribute_names

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
        self, items: list[dict], table_name: str, *, operation: str = "put"
    ) -> dict:
        """
        Write or delete multiple items in a single request.

        DynamoDB allows up to 25 write operations per batch_write_item call.
        This method automatically chunks larger requests and handles unprocessed
        items with exponential backoff retry logic.

        Args:
            items: List of items to write or delete
                   - For 'put': Full item dictionaries
                   - For 'delete': Key-only dictionaries (pk, sk)
            table_name: The DynamoDB table name
            operation: Either 'put' (default) or 'delete'

        Returns:
            dict: Response containing:
                - 'UnprocessedItems': Items that couldn't be processed after retries
                - 'ProcessedCount': Number of successfully processed items
                - 'UnprocessedCount': Number of unprocessed items

        Example (Put):
            >>> items = [
            ...     {"pk": "user#1", "sk": "user#1", "name": "Alice"},
            ...     {"pk": "user#2", "sk": "user#2", "name": "Bob"},
            ...     {"pk": "user#3", "sk": "user#3", "name": "Charlie"}
            ... ]
            >>> response = db.batch_write_item(items=items, table_name="users")
            >>> print(f"Processed {response['ProcessedCount']} items")

        Example (Delete):
            >>> keys = [
            ...     {"pk": "user#1", "sk": "user#1"},
            ...     {"pk": "user#2", "sk": "user#2"}
            ... ]
            >>> response = db.batch_write_item(
            ...     items=keys,
            ...     table_name="users",
            ...     operation="delete"
            ... )

        Note:
            - Maximum 25 operations per request (automatically chunked)
            - Each item can be up to 400 KB
            - Maximum 16 MB total request size
            - No conditional writes in batch operations
            - Unprocessed items are automatically retried with exponential backoff
        """
        import time

        if operation not in ["put", "delete"]:
            raise ValueError(
                f"Invalid operation '{operation}'. Must be 'put' or 'delete'"
            )

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
        operations: list[dict],
        *,
        client_request_token: Optional[str] = None,
        return_consumed_capacity: str = "NONE",
        return_item_collection_metrics: str = "NONE",
    ) -> dict:
        """
        Execute multiple write operations as an atomic transaction.

        All operations succeed or all fail together. This is critical for
        maintaining data consistency across multiple items. Supports up to
        100 operations per transaction (increased from 25 in 2023).

        Args:
            operations: List of transaction operation dictionaries. Each dict must
                       have one of: 'Put', 'Update', 'Delete', or 'ConditionCheck'
                       Example:
                       [
                           {
                               'Put': {
                                   'TableName': 'users',
                                   'Item': {'pk': 'user#1', 'sk': 'user#1', 'name': 'Alice'}
                               }
                           },
                           {
                               'Update': {
                                   'TableName': 'accounts',
                                   'Key': {'pk': 'account#1', 'sk': 'account#1'},
                                   'UpdateExpression': 'SET balance = balance - :amount',
                                   'ExpressionAttributeValues': {':amount': 100}
                               }
                           }
                       ]
            client_request_token: Optional idempotency token for retry safety
            return_consumed_capacity: 'INDEXES', 'TOTAL', or 'NONE' (default)
            return_item_collection_metrics: 'SIZE' or 'NONE' (default)

        Returns:
            dict: Transaction response containing:
                - 'ConsumedCapacity': Capacity consumed (if requested)
                - 'ItemCollectionMetrics': Metrics (if requested)

        Raises:
            TransactionCanceledException: If transaction fails due to:
                - Conditional check failure
                - Item size too large
                - Throughput exceeded
                - Duplicate request

        Example:
            >>> # Transfer money between accounts atomically
            >>> operations = [
            ...     {
            ...         'Update': {
            ...             'TableName': 'accounts',
            ...             'Key': {'pk': 'account#123', 'sk': 'account#123'},
            ...             'UpdateExpression': 'SET balance = balance - :amount',
            ...             'ExpressionAttributeValues': {':amount': 100},
            ...             'ConditionExpression': 'balance >= :amount'
            ...         }
            ...     },
            ...     {
            ...         'Update': {
            ...             'TableName': 'accounts',
            ...             'Key': {'pk': 'account#456', 'sk': 'account#456'},
            ...             'UpdateExpression': 'SET balance = balance + :amount',
            ...             'ExpressionAttributeValues': {':amount': 100}
            ...         }
            ...     }
            ... ]
            >>> response = db.transact_write_items(operations=operations)

        Note:
            - Maximum 100 operations per transaction (AWS limit as of 2023)
            - Each item can be up to 400 KB
            - Maximum 4 MB total transaction size
            - Cannot target same item multiple times in one transaction
            - All operations must succeed or all fail (atomic)
            - Uses strongly consistent reads for condition checks
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

                    raise RuntimeError(
                        f"Transaction failed: {'; '.join(reason_messages)}"
                    ) from e

            logger.exception(f"Error in transact_write_items: {str(e)}")
            raise

    def transact_get_items(
        self, keys: list[dict], *, return_consumed_capacity: str = "NONE"
    ) -> dict:
        """
        Retrieve multiple items with strong consistency as a transaction.

        Unlike batch_get_item, this provides a consistent snapshot across all items
        using strongly consistent reads. Maximum 100 items per transaction.

        Args:
            keys: List of get operation dictionaries. Each dict must specify:
                  - 'Key': The item's primary key
                  - 'TableName': The table name
                  - 'ProjectionExpression': Optional projection
                  - 'ExpressionAttributeNames': Optional attribute names
                  Example:
                  [
                      {
                          'Key': {'pk': 'user#1', 'sk': 'user#1'},
                          'TableName': 'users'
                      },
                      {
                          'Key': {'pk': 'order#123', 'sk': 'order#123'},
                          'TableName': 'orders',
                          'ProjectionExpression': 'id,total,#status',
                          'ExpressionAttributeNames': {'#status': 'status'}
                      }
                  ]
            return_consumed_capacity: 'INDEXES', 'TOTAL', or 'NONE' (default)

        Returns:
            dict: Response containing:
                - 'Items': List of retrieved items (with Decimal conversion)
                - 'ConsumedCapacity': Capacity consumed (if requested)

        Example:
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

        Note:
            - Maximum 100 items per transaction
            - Always uses strongly consistent reads
            - More expensive than batch_get_item (2x RCUs)
            - Provides snapshot isolation across items
            - Cannot be combined with transact_write_items
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
