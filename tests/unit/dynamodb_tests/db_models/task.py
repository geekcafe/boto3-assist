from typing import Optional
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility


class Task(DynamoDBModelBase):
    """
    A Generic Task Model

    Using the same task.id, you can chain child elements via task.step_id

    """

    def __init__(self, id: Optional[str] = None):
        super().__init__()
        self.id: str = id or StringUtility.generate_uuid()
        self._name: Optional[str] = None
        self._step: Optional[str] = None
        self._step_id: Optional[str] = None
        self.metadata: dict = {}
        self._setup_pk()

    @property
    def name(self) -> Optional[str]:
        """
        Returns the name for this task
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """
        Sets the name for this task
        """
        self._name = value

    @property
    def step(self) -> Optional[str]:
        """
        Returns the step for this task
        """
        return self._step

    @step.setter
    def step(self, value: str):
        """
        Sets the step for this task
        """
        self._step = value

    @property
    def step_id(self) -> str | None:

        return self._step_id

    @step_id.setter
    def step_id(self, value: str):
        """
        Sets the step_id for this task
        """

        self._step_id = value

    def _setup_pk(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            (self.__class__.__name__, self.id)
        )

        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("step", self.step_id))
        self.indexes.add_primary(primary)
