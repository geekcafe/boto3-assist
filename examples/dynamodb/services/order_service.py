"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from boto3.dynamodb.conditions import Key
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
        item: dict = model.to_resource_dictionary()

        self.db.save(item=item, table_name=self.table_name)

        return item

    def list(self, user_id: str) -> list:
        """
        Lists users using a global secondary index.

        Args:
            user_id (str): Gets orders by a user id.

        Returns:
            list: A list of users.
        """
        model: Order = Order()
        model.user_id = user_id

        index_name: str = "gsi0"
        key = model.get_key(index_name).key()

        projections_ex = model.projection_expression
        ex_attributes_names = model.projection_expression_attribute_names
        user_list = self.db.query(
            key=key,
            index_name=index_name,
            table_name=self.table_name,
            projection_expression=projections_ex,
            expression_attribute_names=ex_attributes_names,
        )
        if "Items" in user_list:
            user_list = user_list.get("Items")

        return user_list

    def get(
        self, order_id: str, include_childern: bool = False, do_projections: bool = True
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

        if include_childern:
            # exclude the sort key as a filter
            key = model.indexes.primary.key(include_sort_key=False)
            response = self.db.query(
                key=key,
                table_name=self.table_name,
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
