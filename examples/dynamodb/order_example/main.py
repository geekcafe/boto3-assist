"""
DynamoDB Example
"""

import json
import os
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import List

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.utilities.serialization_utility import JsonEncoder
from boto3_assist.utilities.string_utility import StringUtility
from examples.dynamodb.models.product_model import Product
from examples.dynamodb.services.order_item_service import OrderItem, OrderItemService
from examples.dynamodb.services.order_service import Order, OrderService
from examples.dynamodb.services.table_service import DynamoDBTableService


class DynamoDBExample:
    """An example of using and debuggin DynamoDB"""

    def __init__(self, table_name: str) -> None:
        self.db: DynamoDB = DynamoDB()
        self.table_service: DynamoDBTableService = DynamoDBTableService(self.db)

        self.table_name = table_name

        self.order_service: OrderService = OrderService(self.db, table_name=table_name)
        self.order_item_service: OrderItemService = OrderItemService(
            self.db, table_name=table_name
        )

        self.__products: List[Product] = []
        self.order_ids: list[str] = []

        self.__load_products()

    def __load_products(self):
        """Load products"""
        path = os.path.join(str(Path(__file__).parent.absolute()), "products.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                prodcut_list = json.load(file)
                self.__products = [Product(**product) for product in prodcut_list]
        else:
            raise FileNotFoundError("Failed to find the products file")

    def run_examples(self):
        """Run a basic examples with some CRUD examples"""

        # I'm going to use a single table design pattern but you don't have to
        self.table_service.create_a_table(table_name=self.table_name)
        user_1 = StringUtility.generate_uuid()
        five_days_ago = datetime.now(UTC) - timedelta(days=5)
        four_days_ago = datetime.now(UTC) - timedelta(days=4)
        user_2 = StringUtility.generate_uuid()
        user_3 = StringUtility.generate_uuid()
        user_4 = StringUtility.generate_uuid()
        self.__generate_order(user_id=user_1, override_competed_date_utc=five_days_ago)
        self.__generate_order(user_id=user_1, override_competed_date_utc=four_days_ago)
        self.__generate_order(user_id=user_2)
        self.__generate_order(user_id=user_3)
        self.__generate_order(user_id=user_4)

        self.__list_orders_from_known_id()

        low = five_days_ago - timedelta(hours=1)
        high = datetime.now(UTC)
        print(f"checking for orders between {low} and {high} for {user_1}. Expecting 2")
        self.__list_orders_for_user(
            user_id=user_1, start_date_range=low, end_date_range=high
        )

        low = four_days_ago
        high = low + timedelta(days=1)
        print(
            f"checking for orders between {low} and {high} for {user_1}. Expecting One"
        )
        self.__list_orders_for_user(
            user_id=user_1, start_date_range=low, end_date_range=high
        )

    def __generate_order(
        self,
        user_id: str = None,
        override_competed_date_utc: datetime | None = None,
    ):
        user_id = user_id or StringUtility.generate_uuid()
        completed_date_utc = override_competed_date_utc or datetime.now(UTC)
        order: Order = OrderService.new_order_object(user_id)
        # technically we don't need to save this first
        self.order_service.save(model=order)
        # store the orders for later use

        self.order_ids.append(order.id)
        random_product_count = random.randint(1, 15)
        for _ in range(random_product_count):
            product: Product = self.__get_random_product()
            order_item: OrderItem = OrderItem()
            order_item.order_id = order.id
            order_item.id = StringUtility.generate_uuid()
            order_item.product = product
            order_item.quantity = 1

            self.order_item_service.save(model=order_item)
            order.total += order_item.product.price * order_item.quantity

        order.completed_utc = completed_date_utc
        self.order_service.save(model=order)

    def __get_random_product(self) -> Product:
        """Return a random product from the list"""
        if not self.__products:
            raise ValueError("No products available")
        return random.choice(self.__products)

    def __list_orders_from_known_id(self):
        """List the orders"""
        print("######################################################")
        print("Listing orders - looping through Order Ids")
        for order_id in self.order_ids:
            item: dict = self.order_service.get(
                order_id=order_id, include_order_items=True
            )
            print(json.dumps(item, indent=2, cls=JsonEncoder))

        print("End / Listing orders - looping through Order Ids")

    def __list_orders_for_user(
        self,
        user_id: str,
        start_date_range: datetime | None = None,
        end_date_range: datetime | None = None,
    ):
        """List the orders for a user"""
        print("######################################################")
        print(f"Listing orders for user {user_id}")
        items: list[dict] = self.order_service.list(
            user_id=user_id, start_range=start_date_range, end_range=end_date_range
        )
        print(f"Found {len(items)} orders for user {user_id}")
        # for item in items:
        #     print(json.dumps(item, indent=2, cls=JsonEncoder))
        print("End / Listing orders for user")


def main():
    """Main"""
    # get an environment file name or default to .env.docker
    env_file_name: str = os.getenv("ENVRIONMENT_FILE", ".env.docker")
    path = os.path.join(str(Path(__file__).parents[3].absolute()), env_file_name)
    el: EnvironmentLoader = EnvironmentLoader()
    if not os.path.exists(path=path):
        raise FileNotFoundError("Failed to find the environmetn file")
    loaded: bool = el.load_environment_file(path=path)
    if not loaded:
        raise RuntimeError("Failed to load my local environment")

    table_name = "application_table"
    example: DynamoDBExample = DynamoDBExample(table_name=table_name)
    # load a single table design
    example.run_examples()


if __name__ == "__main__":
    main()
