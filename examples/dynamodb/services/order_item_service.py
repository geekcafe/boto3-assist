"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.models.order_item_model import OrderItem


class OrderItemService:
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
        model: Optional[OrderItem] = None,
    ) -> dict:
        item: dict = model.to_resource_dictionary()

        self.db.save(item=item, table_name=self.table_name)

        return item

    def list(self, order_id: str) -> list:
        """
        Lists using a global secondary index.

        Args:
            user_id (str): Gets orders by a user id.

        Returns:
            list: A list of users.
        """
        model: OrderItem = OrderItem()
        model.order_id = order_id

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

    def get(self, order_id: str, item_id: str, do_projections: bool = True) -> dict:
        """
        Retrieves a user by user ID from the specified DynamoDB table.

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            dict: The retrieved user as a dictionary.
        """

        # Alternative way to get the key from the model
        model: OrderItem = OrderItem()
        model.id = item_id
        model.order_id = order_id

        p: str | None = None
        e: dict | None = None
        if do_projections:
            p = model.projection_expression
            e = model.projection_expression_attribute_names

        response = self.db.get(
            model=model,
            table_name=self.table_name,
            projection_expression=p,
            expression_attribute_names=e,
        )

        item: dict = {}
        if "Item" in response:
            item = response.get("Item")

        return item
