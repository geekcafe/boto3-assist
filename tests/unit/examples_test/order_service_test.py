"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.

Unit tests demonstrating one-to-many relationship queries (Order → OrderItems)
This test shows the three different query patterns for 1:many relationships:
1. Get only the parent (order)
2. Get parent + all children (order + items)
3. Get only the children (items)
"""

import unittest
from datetime import datetime, timezone

import boto3
from moto import mock_aws

from boto3_assist.dynamodb.dynamodb import DynamoDB
from examples.dynamodb.models.order_item_model import OrderItem
from examples.dynamodb.models.order_model import Order
from examples.dynamodb.services.order_item_service import OrderItemService
from examples.dynamodb.services.order_service import OrderService
from examples.dynamodb.services.table_service import DynamoDBTableService


@mock_aws
class OrderServiceTest(unittest.TestCase):
    """
    Unit Tests for Order Service demonstrating 1:many relationships.

    This test suite demonstrates:
    - How parent (Order) and children (OrderItems) share the same partition key
    - Three different query patterns for accessing related data
    - Using Moto to test locally without AWS
    """

    def setUp(self):
        """Set up mock DynamoDB environment before each test"""
        # Create mock DynamoDB instance
        self.dynamodb: DynamoDB = DynamoDB()
        self.dynamodb.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")

        # Create test table
        self.table_name = "test_orders_table"
        table_service = DynamoDBTableService(self.dynamodb)
        table_service.create_a_table(table_name=self.table_name)

        # Initialize services
        self.order_service = OrderService(self.dynamodb, self.table_name)
        self.order_item_service = OrderItemService(self.dynamodb, self.table_name)

    def _create_test_order(self, order_id: str, user_id: str = "user-123") -> Order:
        """Helper: Create a test order"""
        order = Order(id=order_id)
        order.user_id = user_id
        order.created_utc = datetime.now(timezone.utc)
        order.completed_utc = datetime.now(timezone.utc)
        order.status = "pending"
        order.total = 0.0
        order.tax_total = 0.0

        # Save order
        self.order_service.save(model=order)
        return order

    def _create_test_order_item(self, order_id: str, item_id: str, quantity: int = 1) -> OrderItem:
        """Helper: Create a test order item"""
        item = OrderItem()
        item.id = item_id
        item.order_id = order_id
        item.quantity = quantity
        item.total = 10.0 * quantity

        # Save item
        self.order_item_service.save(model=item)
        return item

    def test_pattern_1_get_order_only(self):
        """
        Pattern 1: Get ONLY the parent (order)

        Query: pk = "order#123" AND sk = "order#123"
        Result: Just the order (no items)

        This uses db.get() which requires both pk and sk.
        """
        # Create test data
        order_id = "order-001"
        self._create_test_order(order_id)
        self._create_test_order_item(order_id, "item-001", quantity=2)
        self._create_test_order_item(order_id, "item-002", quantity=1)

        # Get order only (include_order_items=False)
        # Turn off projections so we can get key data to e.g. pk, sk
        result = self.order_service.get(
            order_id=order_id, include_order_items=False, do_projections=False
        )

        # Verify we got only the order
        self.assertIn("Item", result)
        order_data = result["Item"]
        self.assertEqual(order_data["id"], order_id)
        self.assertEqual(order_data["sk"], f"order#{order_id}")

        # Verify it's not a list (just a single item via get)
        self.assertNotIn("Items", result)

    def test_pattern_2_get_order_with_all_items(self):
        """
        Pattern 2: Get parent + ALL children in ONE query

        Query: pk = "order#123" (no sk filter)
        Result: Order + all its items

        This is the power of single table design! By querying with just
        the partition key, we get everything that shares that pk.
        """
        # Create test data
        order_id = "order-002"
        self._create_test_order(order_id)
        self._create_test_order_item(order_id, "item-001", quantity=2)
        self._create_test_order_item(order_id, "item-002", quantity=1)
        self._create_test_order_item(order_id, "item-003", quantity=5)

        # Get order with items (include_order_items=True)
        # Turn off projections so we can get key data to e.g. pk, sk
        result = self.order_service.get(
            order_id=order_id, include_order_items=True, do_projections=False
        )

        # Verify we got multiple items back
        self.assertIn("Items", result)
        items = result["Items"]

        # Should have 4 items: 1 order + 3 order items
        self.assertEqual(len(items), 4)

        # Separate order from items
        order = None
        order_items = []

        for item in items:
            if item["sk"].startswith("order#"):
                order = item
            elif item["sk"].startswith("item#"):
                order_items.append(item)

        # Verify we got the order
        self.assertIsNotNone(order)
        self.assertEqual(order["id"], order_id)

        # Verify we got all 3 items
        self.assertEqual(len(order_items), 3)

        # Verify all items have the same partition key as the order
        for item in order_items:
            self.assertEqual(item["pk"], f"order#{order_id}")

    def test_pattern_3_get_only_items(self):
        """
        Pattern 3: Get ONLY children (items)

        Query: pk = "order#123" AND sk begins_with "item#"
        Result: Only the order items (no order)

        This filters by both pk and sk to get only items.
        """
        # Create test data
        order_id = "order-003"
        self._create_test_order(order_id)
        self._create_test_order_item(order_id, "item-001", quantity=1)
        self._create_test_order_item(order_id, "item-002", quantity=2)

        # Query for items only using begins_with on sort key
        from boto3.dynamodb.conditions import Key

        key_condition = Key("pk").eq(f"order#{order_id}") & Key("sk").begins_with("item#")

        result = self.dynamodb.query(key=key_condition, table_name=self.table_name)

        # Verify we got only items (no order)
        self.assertIn("Items", result)
        items = result["Items"]
        self.assertEqual(len(items), 2)

        # Verify all are items
        for item in items:
            self.assertTrue(item["sk"].startswith("item#"))
            self.assertEqual(item["pk"], f"order#{order_id}")

    def test_key_structure_verification(self):
        """
        Verify the key structure that enables 1:many relationships.

        This test explicitly shows how the keys are structured to
        enable querying parent and children together.
        """
        order_id = "order-004"

        # Create order
        order = self._create_test_order(order_id)

        # Create items
        item1 = self._create_test_order_item(order_id, "item-001")
        item2 = self._create_test_order_item(order_id, "item-002")

        # Verify key structure using model's to_dict()
        order_keys = order.indexes.primary.to_dict()
        item1_keys = item1.indexes.primary.to_dict()
        item2_keys = item2.indexes.primary.to_dict()

        print("\n=== Key Structure Demonstration ===")
        print(f"Order keys:  {order_keys}")
        print(f"Item 1 keys: {item1_keys}")
        print(f"Item 2 keys: {item2_keys}")

        # CRITICAL: Order and items share the SAME partition key
        self.assertEqual(order_keys["pk"], item1_keys["pk"])
        self.assertEqual(order_keys["pk"], item2_keys["pk"])
        self.assertEqual(order_keys["pk"], f"order#{order_id}")

        # BUT: They have DIFFERENT sort keys
        self.assertEqual(order_keys["sk"], f"order#{order_id}")
        self.assertEqual(item1_keys["sk"], "item#item-001")
        self.assertEqual(item2_keys["sk"], "item#item-002")

        # This structure is what enables:
        # - Query by pk only → gets order + items
        # - Query by pk + sk = "order#..." → gets just order
        # - Query by pk + sk begins_with "item#" → gets just items

    def test_multiple_orders_isolation(self):
        """
        Verify that different orders are properly isolated.

        Each order (and its items) has a unique partition key,
        so queries don't accidentally return items from other orders.
        """
        # Create two different orders with items
        order1_id = "order-005"
        order2_id = "order-006"

        self._create_test_order(order1_id)
        self._create_test_order_item(order1_id, "item-001")
        self._create_test_order_item(order1_id, "item-002")

        self._create_test_order(order2_id)
        self._create_test_order_item(order2_id, "item-003")
        self._create_test_order_item(order2_id, "item-004")

        # Query order 1 with items
        result1 = self.order_service.get(
            order_id=order1_id, include_order_items=True, do_projections=False
        )

        # Verify we only get order 1's items
        items1 = result1["Items"]
        self.assertEqual(len(items1), 3)  # 1 order + 2 items

        for item in items1:
            # All items should belong to order1
            self.assertEqual(item["pk"], f"order#{order1_id}")
            # Should NOT have order2's items
            self.assertNotIn("item-003", item.get("id", ""))
            self.assertNotIn("item-004", item.get("id", ""))

    def test_empty_order_no_items(self):
        """
        Verify behavior when order has no items.

        Query should return just the order.
        """
        order_id = "order-007"
        self._create_test_order(order_id)
        # Don't create any items
        # Turn off projections so we can get key data to e.g. pk, sk
        result = self.order_service.get(
            order_id=order_id, include_order_items=True, do_projections=False
        )

        # Should get result with Items list
        self.assertIn("Items", result)
        items = result["Items"]

        # Should have only 1 item (the order itself)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], order_id)
        self.assertEqual(items[0]["sk"], f"order#{order_id}")


def main():
    """Run the tests"""
    unittest.main()


if __name__ == "__main__":
    main()
