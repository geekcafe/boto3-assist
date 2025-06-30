"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
from typing import List, Optional, overload, Dict, Any

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
    ) -> None:
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            assume_role_arn=assume_role_arn,
            assume_role_chain=assume_role_chain,
            assume_role_duration_seconds=assume_role_duration_seconds,
        )
        self.helpers: DynamoDBHelpers = DynamoDBHelpers()
        self.log_dynamodb_item_size = (
            str(os.getenv("LOG_DYNAMODB_ITEM_SIZE", "false")).lower() == "true"
        )
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    def save(
        self,
        item: dict | DynamoDBModelBase,
        table_name: str,
        source: Optional[str] = None,
    ) -> dict:
        """
        Save an item to the database
        Args:
            item (dict): DynamoDB Dictionary Object or DynamoDBModelBase.  Supports the "client" or
            "resource" syntax
            table_name (str): The DynamoDb Table Name
            source (str, optional): The source of the call, used for logging. Defaults to None.

        Raises:
            e: Any Error Raised

        Returns:
            dict: The Response from DynamoDB's put_item actions.
            It does not return the saved object, only the response.
        """
        response: Dict[str, Any] = {}

        try:
            if not isinstance(item, dict):
                # attemp to convert it
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

            if isinstance(item, dict) and isinstance(next(iter(item.values())), dict):
                # Use boto3.client syntax
                response = dict(
                    self.dynamodb_client.put_item(TableName=table_name, Item=item)
                )
            else:
                # Use boto3.resource syntax
                table = self.dynamodb_resource.Table(table_name)
                response = dict(table.put_item(Item=item))  # type: ignore[arg-type]

        except Exception as e:  # pylint: disable=w0718
            logger.exception(
                {"source": f"{source}", "metric_filter": "put_item", "error": str(e)}
            )
            raise e

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

        return response

    def update_item(
        self,
        table_name: str,
        key: dict,
        update_expression: str,
        expression_attribute_values: dict,
    ) -> dict:
        """_summary_

        Args:
            table_name (str): table name
            key (dict): pk or pk and sk (composite key)
            update_expression (str): update expression
            expression_attribute_values (dict): expression attribute values

        Returns:
            dict: dynamodb response dictionary
        """
        table = self.dynamodb_resource.Table(table_name)
        response = dict(
            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
            )
        )

        return response

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
            key = key.key()

        kwargs: dict = {}
        if index_name:
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

        return response

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
