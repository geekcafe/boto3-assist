"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import List, Any, Dict, Callable, Mapping

from boto3.dynamodb.conditions import ConditionBase, Key, And, Equals
from aws_lambda_powertools import Tracer, Logger

logger = Logger()
tracer = Tracer()


class DynamoDbKey:
    """DynamoDb Key"""

    def __init__(self) -> None:
        self.index_name: str | None = None
        self.pk_name: str | None = None
        self.pk_value: Any = None
        self.sk_name: str | None = None
        self.sk_value: Any = None


class DynamoDbHelpers:
    """Dynamo DB Helper Functions"""

    def __init__(self) -> None:
        pass

    def get_filter_expressions(
        self, key: ConditionBase | And | Equals
    ) -> Dict[str, Any] | None:
        """Get the filter expression"""
        value = None
        try:
            keys: List[Dict[str, Any]] = []
            expression = {
                "expression_format": key.expression_format,
                "expression_operator": key.expression_operator,
                "keys": keys,  # Initialize 'keys' as an empty list helps with mypy linting
            }

            exp = key.get_expression()
            key_values = exp["values"]
            for v in key_values:
                kv = self._get_key_info(v)
                k: dict[str, dict[str, Any]] = {"key": kv}

                if k:
                    try:
                        keys.append(k)
                    except Exception as e:  # pylint: disable=w0718
                        logger.error({"exception": str(e)})

            if isinstance(keys, list):
                expression["keys"] = keys
            else:
                expression["keys"] = []

            expression["sort"] = self.get_key_sort(key)

            value = expression
        except Exception as e:  # pylint: disable=w0718
            logger.error(str(e))

        return value

    def _get_key_info(self, value: ConditionBase | And | Key) -> dict[str, Any]:
        """
        Get Key Information.  This is helpful for logging and
        visualizing what the key looks like
        """
        key_value: Any = None
        key_name: Any = None
        values = {}
        if isinstance(value, Key):
            key_name = value.name
        elif isinstance(value, str):
            key_value = value
        else:
            key_values = value.get_expression()["values"]
            key: Key = key_values[0]
            key_name = key.name
            key_value = key_values[1]

            try:
                index = 0
                sub_values = value.get_expression()["values"]
                if sub_values:
                    for (
                        v
                    ) in sub_values:  # value._values:  # pylint: disable=w0212,w0012,
                        if index > 0:
                            values[f"value_{index}"] = v
                        index += 1
            except:  # noqa e722, pylint: disable=w0702
                pass

        key_info: Dict[str, Any] = {
            "name": key_name,
            "key": key_value,
            "expression_format": None
            if not isinstance(value, And)
            else value.expression_format,
            "expression_operator": None
            if not isinstance(value, And)
            else value.expression_operator,
            "has_grouped_values": None
            if not isinstance(value, And)
            else value.has_grouped_values,
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

    @staticmethod
    def get_key_value(
        key_configs: dict, index_name: str, key_name: str | None
    ) -> str | None:
        """
        Get the partition key for a given index
        Args:
            key_configs (dict): _description_
            index_name (str): _description_
            key_name (str | None): _description_

        Returns:
            str | None: _description_
        """
        keys = key_configs

        # should be in a list format
        if isinstance(keys, list) and len(keys) > 0:
            pass
        else:
            raise ValueError(
                f"Could not find key_configurations for DynamoDB index {key_name} key {key_name}"
            )
        # get the correct key
        value: str | Callable[[], str] | None = None
        k: dict
        found: bool = False
        for k in keys:
            if isinstance(k, dict):
                for index, index_value in k.items():
                    if index == index_name:
                        if isinstance(index_value, dict):
                            block: dict = index_value.get(key_name, None)
                            if isinstance(block, dict):
                                value = block.get("value", None)

                        found = True
                        break
            if found:
                break

        if not value:
            return None

        if callable(value):
            return value()
        return value

    def populate_key(
        self, key_configs: List[Dict[str, Any]], key: DynamoDbKey
    ) -> DynamoDbKey:
        """
        Populate a key with it's given value

        Args:
            sefl (_type_): _description_
            key_configs (dict): _description_
            key (DynamoDbKey): _description_

        Raises:
            ValueError: _description_

        Returns:
            DynamoDbKey: _description_
        """

        # should be in a list format
        if isinstance(key_configs, list) and len(key_configs) > 0:
            pass
        else:
            raise ValueError(
                f"Could not find key_configurations for DynamoDB index {key.index_name}"
            )
        # get the correct key

        k: dict
        found: bool = False
        for k in key_configs:
            if isinstance(k, dict):
                found, key = self._build_key(k, key)
                if found:
                    break

        return key

    def _build_key(
        self, key_config: dict, key: DynamoDbKey
    ) -> tuple[bool, DynamoDbKey]:
        value: str | Callable[[], str] | None = None
        for index, index_value in key_config.items():
            if index == key.index_name:
                if isinstance(index_value, dict):
                    pk_index_key: dict = index_value.get("pk", {})
                    if isinstance(pk_index_key, dict) and len(pk_index_key) > 0:
                        value = pk_index_key.get("value", None)

                        if callable(value):
                            value = value()
                        key.pk_value = value
                        key.pk_name = pk_index_key.get("attribute", None)

                    sk_index_key: dict = index_value.get("sk", {})
                    if isinstance(sk_index_key, dict) and len(sk_index_key) > 0:
                        value = sk_index_key.get("value", None)

                        if callable(value):
                            value = value()
                        key.sk_value = value
                        key.sk_name = sk_index_key.get("attribute", None)

                return True, key
        return False, key

    def build_key(
        self,
        pk_name: str,
        pk_value: str,
        sk_name: str | None = None,
        sk_value: str | None = None,
        sk_value2: str | None = None,
        condition: str = "begins_with",
    ) -> And | Equals:
        """Get the GSI index name and key"""

        key: Equals | And = Key(f"{pk_name}").eq(pk_value)

        if sk_name and sk_value:
            if sk_value2:
                match condition:
                    case "between":
                        key = key & Key(f"{sk_name}").between(sk_value, sk_value2)

            else:
                match condition:
                    case "begins_with":
                        key = key & Key(f"{sk_name}").begins_with(sk_value)
                    case "eq":
                        key = key & Key(f"{sk_name}").eq(sk_value)
                    case "gt":
                        key = key & Key(f"{sk_name}").gt(sk_value)
                    case "gte":
                        key = key & Key(f"{sk_name}").gte(sk_value)
                    case "lt":
                        key = key & Key(f"{sk_name}").lt(sk_value)

        return key

    def get_keys(
        self, key_configs: List[Dict], exclude_pk: bool = False
    ) -> List[DynamoDbKey]:
        """_summary_

        Args:
            key_configs (List[Dict]): _description_
            index_name (str): _description_

        Returns:
            List[Dict]: _description_
        """
        keys: List[DynamoDbKey] = []
        for k in key_configs:
            if isinstance(k, dict):
                for index, _ in k.items():
                    # print(index, index_value)
                    if index == "primary_key" and exclude_pk:
                        continue
                    key: DynamoDbKey = DynamoDbKey()
                    key.index_name = index
                    key = self.populate_key(key_configs, key)
                    keys.append(key)

        return keys

    def keys_to_dictionary(self, keys: List[DynamoDbKey]) -> dict:
        """_summary_

        Args:
            keys (List[DynamoDbKey]): _description_

        Returns:
            dict: _description_
        """
        key_dict: dict = {}
        for key in keys:
            if key.pk_name and key.pk_value:
                key_dict[key.pk_name] = key.pk_value
            if key.sk_name and key.sk_value:
                key_dict[key.sk_name] = key.sk_value

        return key_dict
