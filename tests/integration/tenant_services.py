from typing import Optional
from .tenant import Tenant
from boto3_assist.dynamodb.dynamodb import DynamoDB


class TenantServices:

    def __init__(self, db: DynamoDB, table_name: str) -> None:
        self.db: DynamoDB = db or DynamoDB()
        self.table_name: str = table_name

    def list(
        self,
        *,
        status: Optional[str] = None,
        ascending: bool = True,
        do_projections: bool = False,
        strongly_consistent: bool = False,
        start_key: Optional[dict] = None,
    ) -> dict:
        """
        List all Tenants within an optional status (enabled or )

        Args:
            start_key (Optional[str]): A start key for paged results.
            do_projections (bool, optional): Determines if we do projections or not. Defaults to False.

        Returns:
            dict: DynamoDB response dictionary
        """
        model: Tenant = Tenant()
        index_name: str = "gsi0"
        if status:
            model.status = status
            index_name = "gsi1"
        key = model.get_key(index_name).key()
        response = self.db.query_by_criteria(
            model=model,
            index_name=index_name,
            key=key,
            start_key=start_key,
            do_projections=do_projections,
            table_name=self.table_name,
            strongly_consistent=strongly_consistent,
            ascending=ascending,
        )

        return response
