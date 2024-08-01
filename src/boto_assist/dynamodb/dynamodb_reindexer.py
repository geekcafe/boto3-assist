"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import json
from typing import Any, Callable, Dict, Optional

from boto_assist.dynamodb.dynamodb import DynamoDb
from boto_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase
from boto_assist.utilities.serialization_utility import Serialization


class DynamoDbReindexer(DynamoDb):
    def __init__(
        self,
        table_name: str,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        self.table_name = table_name

        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def reindex_item(
        self,
        original_pk: dict,
        key_configs: Dict[str, Dict[str, Callable[[], str]]],
        dry_run: bool = False,
    ):
        """_summary_

        Args:
            original_pk (dict): _description_
            db_item (dict): _description_
            db_model (DynamoDbModelBase): _description_
            dry_run (bool, optional): _description_. Defaults to False.
        """

        # Generate new keys based on the key_configs
        updated_keys = self.update_keys(key_configs)

        # Update the item in DynamoDB with new keys
        self.update_item_in_dynamodb(
            original_pk=original_pk, updated_keys=updated_keys, dry_run=dry_run
        )

    def load_model(
        self, db_item: dict, db_model: DynamoDbModelBase
    ) -> DynamoDbModelBase:
        """load the model which will serialze the dynamodb dictionary to an instance of an object"""
        # Assume UserDbModel is your model class, replace with actual model
        base_model = Serialization.map(db_item, db_model)
        return base_model

    def update_keys(
        self, key_configs: Dict[str, Dict[str, Callable[[], str]]]
    ) -> Dict[str, Any]:
        """Update key values"""
        updated_keys = {}
        for index_name, index_config in key_configs.items():
            updated_keys[index_name] = {}
            for key_type, key_value_lambda in index_config.items():
                updated_keys[index_name][key_type] = key_value_lambda()

        return updated_keys

    def update_item_in_dynamodb(
        self, original_pk: dict, updated_keys: Dict[str, Any], dry_run: bool = False
    ):
        """Update the dynamodb item"""
        update_expression = self.build_update_expression(updated_keys)
        expression_attribute_values = self.build_expression_attribute_values(
            updated_keys
        )

        if not dry_run:
            self.update_item(
                table_name=self.table_name,
                key=original_pk,
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )
        else:
            print("Dry run: Skipping Update item")
            print(f"{json.dumps(original_pk, indent=4)}")
            print(f"{update_expression}")
            print(f"{json.dumps(expression_attribute_values, indent=4)}")

    def build_update_expression(self, updated_keys: Dict[str, Any]) -> str:
        """
        Build the expression for updating the item

        Args:
            updated_keys (Dict[str, Any]): _description_

        Returns:
            str: _description_
        """
        update_expression = "SET " + ", ".join(
            f"{k} = :{k}" for k in updated_keys.keys()
        )
        return update_expression

    def build_expression_attribute_values(
        self, updated_keys: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the expression attribute values for the update expression

        Args:
            updated_keys (Dict[str, Any]): _description_

        Returns:
            Dict[str, Any]: _description_
        """
        expression_attribute_values = {f":{k}": v for k, v in updated_keys.items()}
        return expression_attribute_values


def main():
    # Assume the following key_configs is correct and the lambda functions can access model attributes
    key_configs = {
        "pk_sk": {
            "pk": lambda model: f"user#{model.id}",
            "sk": lambda model: f"user#{model.id}",
        },
        "gsi0": {
            "pk": lambda model: "users#",
            "sk": lambda model: f"email#{model.email}",
        },
        "gsi1": {
            "pk": lambda model: "users#",
            "sk": lambda model: f"lastname#{model.last_name}",
        },
        "gsi2": {
            "pk": lambda model: "users#",
            "sk": lambda model: f"firstname#{model.first_name}",
        },
    }

    # reindexer = DynamoDbReindexer(table_name="UserTable", key_configs=key_configs)
    # reindexer.reindex()
