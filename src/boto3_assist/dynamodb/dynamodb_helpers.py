"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import List, Any, Dict
from boto3.dynamodb.conditions import ConditionBase, Key
from aws_lambda_powertools import Tracer, Logger

logger = Logger()
tracer = Tracer()


class DynamoDbHelpers:
    """Dynamo DB Helper Functions"""

    def __init__(self) -> None:
        pass

    def get_filter_expressions(self, key: ConditionBase) -> Dict[str, Any] | None:
        """Get the filter expression"""
        value = None
        try:
            expression = {
                "expression_format": key.expression_format,
                "expression_operator": key.expression_operator,
                "keys": List[Dict[str, Any]],
            }

            count = 0
            key_values = key.get_expression()["values"]
            for v in key_values:
                kv = self.get_key_info(v)
                k: dict[str, dict[str, Any]] = {f"key_{count}": kv}
                keys: List[Dict[str, Any]] | Any = expression["keys"]
                # if isinstance(keys, List):
                if k:
                    keys.append(k)

                expression["keys"] = keys

            expression["sort"] = self.get_key_sort(key)

            value = expression
        except Exception as e:  # pylint: disable=w0718
            logger.error(str(e))

        return value

    def get_key_info(self, value: ConditionBase) -> dict[str, Any]:
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
            sub_values = value.get_expression()["values"]
            if sub_values:
                for v in sub_values:  # value._values:  # pylint: disable=w0212,w0012,
                    if index > 0:
                        values[f"value_{index}"] = v
                    index += 1
        except:  # noqa e722, pylint: disable=w0702
            pass

        key_info: Dict[str, Any] = {
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
    def wrap_collection_response(self, collection: List[dict]) -> dict[str, List]:
        """
        Wraps Up Some usefull information when dealing with

        """
        response: dict[str, List] = {"Items": [], "Batches": []}
        record_start: int = 0
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

    @staticmethod
    def validate_dynamodb_format(item):
        """validate_dynamodb_format"""

        def validate_attribute(key, value, path):
            logger.debug({"key": key, "value": value, "path": path})
            if not isinstance(value, dict):
                return (
                    False,
                    f"Error at key [{path}]: Expected a dictionary, got {type(value).__name__}. Review [{path}] it should have an M ",
                )
            if len(value) != 1:
                return (
                    False,
                    f"Error at {path}: Dictionary should contain exactly one key-value pair",
                )
            type_key = list(value.keys())[0]
            if type_key not in [
                "S",
                "N",
                "B",
                "SS",
                "NS",
                "BS",
                "M",
                "L",
                "NULL",
                "BOOL",
            ]:
                return False, f"Error at {path}: Invalid type key '{type_key}'"
            type_value = value[type_key]
            if type_key == "S" and not isinstance(type_value, str):
                return (
                    False,
                    f"Error at {path}: Expected a string for type 'S', got {type(type_value).__name__}",
                )
            if type_key == "N" and not isinstance(type_value, (int, float, str)):
                return (
                    False,
                    f"Error at {path}: Expected a number for type 'N', got {type(type_value).__name__}",
                )
            if type_key == "B" and not isinstance(type_value, bytes):
                return (
                    False,
                    f"Error at {path}: Expected bytes for type 'B', got {type(type_value).__name__}",
                )
            if type_key == "SS" and not (
                isinstance(type_value, list)
                and all(isinstance(i, str) for i in type_value)
            ):
                return (
                    False,
                    f"Error at {path}: Expected a list of strings for type 'SS', got {type(type_value).__name__}",
                )
            if type_key == "NS" and not (
                isinstance(type_value, list)
                and all(isinstance(i, (int, float, str)) for i in type_value)
            ):
                return (
                    False,
                    f"Error at {path}: Expected a list of numbers for type 'NS', got {type(type_value).__name__}",
                )
            if type_key == "BS" and not (
                isinstance(type_value, list)
                and all(isinstance(i, bytes) for i in type_value)
            ):
                return (
                    False,
                    f"Error at {path}: Expected a list of bytes for type 'BS', got {type(type_value).__name__}",
                )
            if type_key == "M":
                if not isinstance(type_value, dict):
                    return (
                        False,
                        f"Error at {path}: Expected a dictionary for type 'M', got {type(type_value).__name__}",
                    )
                for k, v in type_value.items():
                    valid, error = validate_attribute(k, v, f"{path}.{k}")
                    if not valid:
                        return False, error
            if type_key == "L":
                if not isinstance(type_value, list):
                    return (
                        False,
                        f"Error at {path}: Expected a list for type 'L', got {type(type_value).__name__}",
                    )
                for index, item in enumerate(type_value):
                    valid, error = validate_attribute(
                        f"{index}", item, f"{path}[{index}]"
                    )
                    if not valid:
                        return False, error
            if type_key == "NULL" and type_value is not True:
                return (
                    False,
                    f"Error at {path}: Expected True for type 'NULL', got {type(type_value).__name__}",
                )
            if type_key == "BOOL" and not isinstance(type_value, bool):
                return (
                    False,
                    f"Error at {path}: Expected a boolean for type 'BOOL', got {type(type_value).__name__}",
                )
            return True, None

        if not isinstance(item, dict):
            return False, f"Error: Item ({item}) should be a dictionary"
        for key, value in item.items():
            if not isinstance(key, str):
                return (
                    False,
                    f"Error: Key '{key}' should be a string, got {type(key).__name__}",
                )
            valid, error = validate_attribute(key, value, key)
            if not valid:
                return False, error
        return True, None

    @staticmethod
    def clean_null_values(item):
        """
        Recursively traverse the dictionary and handle "null" values.
        Args:
            item (dict or list): The dictionary or list to clean.
        Returns:
            The cleaned dictionary or list.
        """
        if isinstance(item, dict):
            cleaned = {}
            for k, v in item.items():
                if v == "null":
                    print(f"Found 'null' value at key: {k}, replacing with None")
                    cleaned[k] = ""  # Or handle it as you see fit
                elif isinstance(v, (dict, list)):
                    cleaned[k] = DynamoDbHelpers.clean_null_values(v)
                else:
                    cleaned[k] = v
            return cleaned
        elif isinstance(item, list):
            return [DynamoDbHelpers.clean_null_values(i) for i in item]
        else:
            return item
