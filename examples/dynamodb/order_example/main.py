"""
DynamoDB Example
"""

import json
import os
from pathlib import Path

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from boto3_assist.utilities.serialization_utility import JsonEncoder
from boto3_assist.utilities.string_utility import StringUtility
from examples.dynamodb.services.table_service import DynamoDBTableService
from examples.dynamodb.services.order_service import OrderService, Order
from examples.dynamodb.services.order_item_service import OrderItemService, OrderItem


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

        self.order_ids: list[str] = []

    def run_examples(self):
        """Run a basic examples with some CRUD examples"""

        # I'm going to use a single table design pattern but you don't have to
        self.table_service.create_a_table(table_name=self.table_name)
        self.__generate_some_orders()
        self.__list_orders()

    def __generate_some_orders(self):
        for _ in range(5):
            random_user_id: str = StringUtility.generate_uuid()
            order: Order = OrderService.new_order_object(random_user_id)
            # technically we don't need to save this first
            self.order_service.save(model=order)
            # store the orders for later use

            self.order_ids.append(order.id)

            for p in range(15):
                order_item: OrderItem = OrderItem()
                order_item.order_id = order.id
                order_item.id = StringUtility.generate_uuid()
                order_item.product_name = f"Product {p}"
                order_item.product_id = "xxxxxxxx"
                order_item.quantity = 1
                order_item.price = 9.99
                self.order_item_service.save(model=order_item)
                order.total += order_item.price * order_item.quantity

            self.order_service.save(model=order)

    def __list_orders(self):
        """List the orders"""
        for order_id in self.order_ids:
            item: dict = self.order_service.get(
                order_id=order_id, include_childern=True
            )
            print(json.dumps(item, indent=2, cls=JsonEncoder))


def main():
    """Main"""
    # get an environment file name or default to .env.docker
    env_file_name: str = os.getenv("ENVRIONMENT_FILE", ".env.docker")
    path = os.path.join(str(Path(__file__).parents[3].absolute()), env_file_name)
    el: EnvironmentLoader = EnvironmentLoader()
    if not os.path.exists(path=path):
        raise FileNotFoundError("Failed to find the environmetn file")
    loaded: bool = el.load_environment_file(path)
    if not loaded:
        raise RuntimeError("Failed to load my local environment")

    table_name = "application_table"
    example: DynamoDBExample = DynamoDBExample(table_name=table_name)
    # load a single table design
    example.run_examples()


if __name__ == "__main__":
    main()
