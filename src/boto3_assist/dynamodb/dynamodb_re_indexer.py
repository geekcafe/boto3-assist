"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import json
from typing import Any, Dict, Optional, List, Type
from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.utilities.serialization_utility import Serialization
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_iservice import IDynamoDBService

logger = Logger()


class DynamoDBReIndexer:
    """ReIndexing your database"""

    def __init__(
        self,
        table_name: str,
        *,
        db: Optional[DynamoDB] = None,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        self.table_name = table_name
        self.db: DynamoDB = db or DynamoDB(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def reindex_item(
        self,
        original_primary_key: dict,
        model: DynamoDBModelBase,
        *,
        dry_run: bool = False,
        inplace: bool = True,
        leave_original_record: bool = False,
        service_cls: Type[IDynamoDBService] | None,
    ):
        """
        Reindex the record

        Args:
            original_primary_key (dict): The original primary key of the record to be reindexed.
                This is either the partition_key or a composite key (partition_key, sort_key)
            model (DynamoDBModelBase): A model instance that will be used to serialize the new keys
                into a dictionary. It must inherit from DynamoDBModelBase

            dry_run (bool, optional): Ability to log the actions without executing them. Defaults to False.
            inplace (bool, optional): Ability to just update the indexes only.
                No other fields will be updated, however you can't update the primary_key (partition/sort key)
                with this action since they are immutable.
                Defaults to True.
            leave_original_record (bool, optional): _description_. Defaults to False.
        """

        if inplace:
            keys: List[DynamoDBIndex] = model.list_keys()
            # Update the item in DynamoDB with new keys
            self.update_item_in_dynamodb(
                original_primary_key=original_primary_key, keys=keys, dry_run=dry_run
            )
            # todo: add some additional error handling here and throw a more
            # descriptive error if they try to use a different primary
            # pk or sk, which you can't do.  If that's the case
        else:
            # add the new one first and optionally delete the older one
            # once we are succesfull
            try:
                # save the new one first
                service_instance: Optional[IDynamoDBService] = (
                    service_cls(db=self.db) if callable(service_cls) else None
                )

                if service_instance:
                    service_instance.save(model=model)
                else:
                    self.db.save(
                        item=model, table_name=self.table_name, source="reindex"
                    )

                # then delete the old on
                if not leave_original_record:
                    self.db.delete(
                        table_name=self.table_name, primary_key=original_primary_key
                    )
            except Exception as e:  # pylint: disable=broad-except
                logger.error(str(e))
                raise RuntimeError(str(e)) from e
            # this gets a little more trick as we need to delete the item

    def load_model(
        self, db_item: dict, db_model: DynamoDBModelBase
    ) -> DynamoDBModelBase | None:
        """load the model which will serialze the dynamodb dictionary to an instance of an object"""

        base_model = Serialization.map(db_item, db_model)
        return base_model

    def update_item_in_dynamodb(
        self,
        original_primary_key: dict,
        keys: List[DynamoDBIndex],
        dry_run: bool = False,
    ):
        """Update the dynamodb item"""
        dictionary = self.db.helpers.keys_to_dictionary(keys=keys)

        update_expression = self.build_update_expression(dictionary)
        expression_attribute_values = self.build_expression_attribute_values(dictionary)

        if not dry_run:
            self.db.update_item(
                table_name=self.table_name,
                key=original_primary_key,
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )
        else:
            print("Dry run: Skipping Update item")
            print(f"{json.dumps(original_primary_key, indent=4)}")
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
