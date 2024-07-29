import datetime
from boto3.dynamodb.conditions import Key, And
from boto_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase


class UserDbModel(DynamoDbModelBase):
    """Database Model for the User Entity"""

    PK_PREFIX: str = "user#"
    USERS_PREFIX: str = "users#"
    EMAIL_SK_PREFIX: str = "email#"
    LAST_NAME_SK_PREFIX: str = "lastname#"
    FIRST_NAME_SK_PREFIX: str = "firstname#"

    def __init__(
        self,
        id: str | None = None,  # pylint: disable=w0622
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> None:
        self.id: str | None = id
        self.first_name: str | None = first_name
        self.last_name: str | None = last_name
        self.email: str | None = email
        self.modified_datetime_utc: str = str(datetime.datetime.now(datetime.UTC))

    @property
    def pk(self) -> str:
        """The user's primary key"""
        return f"{UserDbModel.PK_PREFIX}{self.id}"

    @property
    def sk(self) -> str:
        """The user's sort key"""
        return f"{UserDbModel.PK_PREFIX}{self.id}"

    @staticmethod
    def pk_sk_key(user_id: str) -> dict:
        """Gets the key for the primay pk and sk key pair"""
        pk = f"{UserDbModel.PK_PREFIX}{user_id}"
        # pk and sk are the same
        key = {
            "pk": pk,
            "sk": pk,
        }

        return key

    @property
    def gsi0_pk(self) -> str:
        """
        Global Secondary Index PK "users#"
        this a bit of a HOT key, depending on the size of your user
        base you may want to rethink this
        """
        return UserDbModel.USERS_PREFIX

    @property
    def gsi0_sk(self) -> str:
        """
        Global Secondary Index Sort Key
        In the form of: "email#{self.email}"
        """
        return f"{UserDbModel.EMAIL_SK_PREFIX}{self.email}"

    @staticmethod
    def gsi0() -> tuple[str, And]:
        """
        Get the GSI0 index name and key.  This matches the pattern
        for gsi0 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        index_name = "gsi0"
        key = Key(f"{index_name}_pk").eq(UserDbModel.USERS_PREFIX) & Key(
            f"{index_name}_sk"
        ).begins_with(UserDbModel.EMAIL_SK_PREFIX)

        return index_name, key

    @property
    def gsi1_pk(self) -> str:
        """
        Global Secondary Index PK "users#"
        this a bit of a HOT key, depending on the size of your user
        base you may want to rethink this
        """
        return UserDbModel.EMAIL_SK_PREFIX

    @property
    def gsi1_sk(self) -> str:
        """
        Global Secondary Index Sort Key
        In the form of: "lastname#{self.last_name}"
        """
        return f"{UserDbModel.LAST_NAME_SK_PREFIX}{self.last_name}"

    @staticmethod
    def gsi1() -> tuple[str, And]:
        """
        Get the GSI1 index name and key.  This matches the pattern
        for gsi1 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        index_name = "gsi1"
        key = Key(f"{index_name}_pk").eq(UserDbModel.USERS_PREFIX) & Key(
            f"{index_name}_sk"
        ).begins_with(UserDbModel.LAST_NAME_SK_PREFIX)

        return index_name, key

    @staticmethod
    def get_projection_expressions() -> tuple[str, dict | None]:
        """Gets the current projection expressions"""
        projection_expression = "id,first_name,last_name,email,modified_datetime_utc"

        expression_attribute_names = None

        return projection_expression, expression_attribute_names
