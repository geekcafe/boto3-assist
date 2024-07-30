"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import List
from boto3.dynamodb.conditions import ConditionBase, Key
from aws_lambda_powertools import Tracer, Logger

logger = Logger()
tracer = Tracer()


class DynamoDbHelpers:
    """Dynamo DB Helper Functions"""

    def __init__(self) -> None:
        pass

    def get_filter_expressions(self, key: ConditionBase) -> dict:
        """Get the filter expression"""
        value = None
        try:
            expression = {
                "expression_format": key.expression_format,
                "expression_operator": key.expression_operator,
                "keys": [],
            }

            count = 0
            key_values = key.get_expression()["values"]
            for v in key_values:
                kv = self.get_key_info(v)
                k = {f"key_{count}": kv}
                expression["keys"].append(k)

            expression["sort"] = self.get_key_sort(key)

            value = expression
        except Exception as e:  # pylint: disable=w0718
            logger.error(str(e))

        return value

    def get_key_info(self, value: ConditionBase) -> dict:
        """
        Get Key Information.  This is helpful for logging and
        visualizing what the key looks like
        """
        key_values = value.get_expression()["values"]
        key: Key = key_values[0]
        key_name = key.name
        key_value = key_values[1]
        values = {}
        try:
            index = 0
            for v in value._values:  # pylint: disable=w0212
                if index > 0:
                    values[f"value_{index}"] = v
                index += 1
        except:  # noqa e722, pylint: disable=w0702
            pass

        key_info = {
            "name": key_name,
            "key": key_value,
            "expression_format": value.expression_format,
            "expression_operator": value.expression_operator,
            "has_grouped_values": value.has_grouped_values,
            "values": values,
        }

        return key_info

    def get_key_sort(self, condition: ConditionBase) -> str:
        """Gets the sort key"""
        try:
            and_values: ConditionBase = condition.get_expression()["values"][1]
            keys = and_values.get_expression()["values"]
            # second is the sort (element 0 is pk)
            sort = str(keys[1])
            return sort
        except Exception as e:  # pylint: disable=w0718
            logger.error({"exception": str(e)})
            return "unknown"

    @tracer.capture_method(capture_response=False)
    def wrap_response(self, items, dynamodb_response: dict, diagnostics) -> dict:
        """A wrapper for response data"""
        last_key = dynamodb_response.get("LastEvaluatedKey", None)
        more = last_key is not None

        # conform the dynamod dy responses
        response = {
            "Items": items,
            "LastKey": last_key,
            "Count": dynamodb_response.get("Count"),
            "Scanned": dynamodb_response.get("ScannedCount"),
            "MoreRecords": more,
            "Diagnostics": diagnostics,
        }

        return response

    @tracer.capture_method(capture_response=False)
    def wrap_collection_response(self, collection: List[dict]):
        """
        Wraps Up Some usefull information when dealing with

        """
        response = {"Items": [], "Batches": []}
        record_start = 0
        for item in collection:
            record_start += 1
            record_end = record_start + len(collection)
            response["Items"].extend(item["Items"])
            response["Batches"].append(
                {
                    "LastKey": item["LastKey"],
                    "Count": item["Count"],
                    "Scanned": item["Scanned"],
                    "MoreRecords": item["MoreRecords"],
                    "Records": {"start": record_start, "end": record_end},
                }
            )

            record_start = record_end

        return response
