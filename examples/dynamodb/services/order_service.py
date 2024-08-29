"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import json
from datetime import datetime
from typing import Optional, List, Any, Dict
from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.models.order_model import Order
from src.boto3_assist.utilities.datetime_utility import DatetimeUtility
from src.boto3_assist.utilities.string_utility import StringUtility


class OrderService:
    """
    A service class to handle user operations on a DynamoDB table.

    Attributes:
        db (DynamoDB): An instance of DynamoDB to interact with the database.
    """

    def __init__(self, db: DynamoDB, table_name: str) -> None:
        """
        Initializes the OrderService with a DynamoDB instance.

        Args:
            db (DynamoDB): An instance of DynamoDB.
        """
        self.db: DynamoDB = db
        self.table_name: str = table_name

    def save(
        self,
        *,
        model: Optional[Order] = None,
    ) -> dict:
        if not model.completed_utc:
            model.completed_utc = DatetimeUtility.get_utc_now()
        item: dict = model.to_resource_dictionary()

        self.db.save(item=item, table_name=self.table_name)

        return item

    def list(
        self,
        user_id: str,
        start_range: Optional[datetime] = None,
        end_range: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists users using a global secondary index.

        Args:
            user_id (str): Gets orders by a user id.

        Returns:
           dict: The retrieved orders as a dictionary.
        """
        model: Order = Order()
        model.user_id = user_id

        index_name: str = "gsi1"
        key = model.get_key(index_name).key()

        if start_range and end_range:
            # we'll override the key and do a between
            low_value = start_range.timestamp()
            high_value = end_range.timestamp()
            key = model.get_key(index_name).key(
                condition="between", low_value=low_value, high_value=high_value
            )

        # just for demo / debugging purposes so you can "see" when the filters are doing
        expression = model.helpers.get_filter_expressions(key)
        print(json.dumps(expression, indent=2, default=str))

        projections_ex = model.projection_expression
        ex_attributes_names = model.projection_expression_attribute_names
        response = self.db.query(
            key=key,
            index_name=index_name,
            table_name=self.table_name,
            projection_expression=projections_ex,
            expression_attribute_names=ex_attributes_names,
        )
        if "Items" in response:
            response = response.get("Items")
        return response

    def get(
        self,
        order_id: str,
        include_order_items: bool = False,
        do_projections: bool = True,
    ) -> dict:
        """
        Retrieves a user by user ID from the specified DynamoDB table.

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            dict: The retrieved user as a dictionary.
        """

        response: dict = {}
        model: Order = Order(id=order_id)
        p: str | None = model.projection_expression if do_projections else None
        e: dict | None = (
            model.projection_expression_attribute_names if do_projections else None
        )

        if include_order_items:
            # exclude the sort key as a filter
            key = model.indexes.primary.key(include_sort_key=False)
            response = self.db.query(
                key=key,
                table_name=self.table_name,
                projection_expression=p,
                expression_attribute_names=e,
            )
            # manual way to do this
            # key = Key("pk").eq(f"order#{order_id}")
            # table = self.db.dynamodb_resource.Table(self.table_name)
            # response = table.query(KeyConditionExpression=key)
        else:
            response = self.db.get(
                model=model,
                table_name=self.table_name,
                projection_expression=p,
                expression_attribute_names=e,
            )

        return response

    @staticmethod
    def new_order_object(user_id: str) -> Order:
        order: Order = Order()
        order.id = StringUtility.generate_uuid()
        order.user_id = user_id
        order.created_utc = DatetimeUtility.get_utc_now()

        return order
