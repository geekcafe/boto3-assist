"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
from typing import List, Optional, Tuple

from aws_lambda_powertools import Tracer, Logger
from boto3.dynamodb.conditions import Key, And
from boto3_assist.dynamodb.dynamodb_connection import DynamoDbConnection
from boto3_assist.dynamodb.dynamodb_helpers import DynamoDbHelpers
from boto3_assist.utilities.string_utility import StringUtility


logger = Logger()
tracer = Tracer()


class DynamoDb(DynamoDbConnection):
    """
        DynamoDb. Wrapper for basic DynamoDb Connection and Actions

    Inherits:
        DynamoDbConnection
    """

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.helpers: DynamoDbHelpers = DynamoDbHelpers()
        self.log_dynamodb_item_size = (
            str(os.getenv("LOG_DYNAMODB_ITEM_SIZE", "false")).lower() == "true"
        )

    @tracer.capture_method
    def save(self, item: dict, table_name: str, source: Optional[str] = None) -> dict:
        """
        Save an item to the database
        Args:
            item (dict): DynamoDb Dictionay Object.  Supports the "client" or
            "resource" syntax
            table_name (str): The DyamoDb Table Name
            source (str, optional): The source of the call, used for logging. Defaults to None.

        Raises:
            e: Any Error Raised

        Returns:
            dict: The Response from DynamoDb's put_item actions
        """
        response = None

        try:
            if self.log_dynamodb_item_size:
                size_bytes: int = StringUtility.get_size_in_bytes(item)
                size_kb: int = StringUtility.get_size_in_kb(item)

                print(f"Size of item: {size_bytes}bytes")
                print(f"Size of item: {size_kb:.2f}kb")
            if isinstance(next(iter(item.values())), dict):
                # Use boto3.client syntax
                response = self.dynamodb_client.put_item(
                    TableName=table_name, Item=item
                )
            else:
                # Use boto3.resource syntax
                table = self.dynamodb_resource.Table(table_name)
                response = table.put_item(Item=item)

            # response = self.dynamodb_client.put_item(
            #     TableName=f"{table_name}", Item=item
            # )
        except Exception as e:  # pylint: disable=w0718
            logger.exception(
                {"source": f"{source}", "metric_filter": "put_item", "error": str(e)}
            )
            raise e

        return response

    @tracer.capture_method
    def get(
        self,
        key: dict,
        table_name: str,
        *,
        strongly_consistent: bool = False,
        return_consumed_capacity: str | None = None,
        projection_expression: str | None = None,
        expression_attribute_names: dict | None = None,
        source: Optional[str] = None,
        call_type: str = "resource",
    ) -> dict:
        """
        Description:
            generic get_item dynamoDb call
        Parameters:
            key: a dictionary object representing the primary key
        """

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

            if call_type == "resource":
                table = self.dynamodb_resource.Table(table_name)
                response = table.get_item(Key=key, **valid_kwargs)
            elif call_type == "client":
                response = self.dynamodb_client.get_item(
                    Key=key, TableName=table_name, **valid_kwargs
                )
            else:
                raise ValueError(
                    f"Uknown call_type of {call_type}.  Supported call_types [resource | client]"
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
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

        return response

    def query(
        self,
        key: Key,
        index_name: Optional[str] = None,
        ascending: bool = False,
        table_name: Optional[str] = None,
        source: Optional[str] = None,
        strongly_consistent: bool = False,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        start_key: Optional[str] = None,
    ) -> List[dict]:
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

        table = self.dynamodb_resource.Table(table_name)
        response = table.query(**kwargs)

        return response

    @tracer.capture_method
    def delete(self, primary_key: Key, table_name: Optional[str] = None):
        """deletes an item from the database"""

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

    def get_key(
        self, index_name: str, pk_value: str, sk_value: str | None = None
    ) -> Tuple[str, And]:
        """Get the GSI index name and key"""

        pk_value = self.get_pk(index_name)  # pylint: disable=e1101
        sk_value = self.get_sk(index_name)  # pylint: disable=e1101

        key = Key(f"{index_name}_pk").eq(pk_value) & Key(
            f"{index_name}_sk"
        ).begins_with(sk_value)

        return index_name, key
