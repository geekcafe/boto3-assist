import datetime
from boto3.dynamodb.conditions import Key
from boto_assist.dynamodb.dynamodb_model_base import DynamoDbModelBase
from boto_assist.utilities.string_utility import StringUtility


class UserPostDbModel(DynamoDbModelBase):
    """Database Model for the User Posts Entity"""

    PK_PREFIX: str = "post#"
    POSTS_PREFIX: str = "posts#"
    TIME_STAMP_PREFIX: str = "ts#"
    USER_ID_PREFIX: str = "user_id#"
    TITLE_PREFIX: str = "title#"

    def __init__(
        self,
        id: str | None = None,  # pylint: disable=w0622
        title: str | None = None,
        user_id: str | None = None,
    ) -> None:
        self.__id: str | None = id
        self.user_id: str | None = user_id
        self.title: str | None = title
        self.data: str | None = None
        self.status: str | None = None
        self.type: str | None = None
        self.timestamp: str = str(datetime.datetime.now(datetime.UTC).timestamp())
        self.modified_datetime_utc: str = str(datetime.datetime.now(datetime.UTC))

    @property
    def id(self) -> str:
        """User Post Id"""
        if self.__id is None:
            self.__id = StringUtility.generate_uuid()

        return self.__id

    @id.setter
    def id(self, value: str):
        self.__id = value

    @property
    def pk(self) -> str:
        """The user's primary key"""
        return f"{UserPostDbModel.PK_PREFIX}{self.id}"

    @property
    def sk(self) -> str:
        """The user's sort key"""
        return f"{UserPostDbModel.PK_PREFIX}{self.id}"

    @staticmethod
    def pk_sk_key(user_id: str) -> dict:
        """Gets the key for the primay pk and sk key pair"""
        pk = f"{UserPostDbModel.PK_PREFIX}{user_id}"
        # pk and sk are the same
        key = {
            "pk": pk,
            "sk": pk,
        }

        return key

    @property
    def gsi0_pk(self) -> str:
        """
        Global Secondary Index PK "posts#"
        this a bit of a HOT key, depending on the size of your user
        base you may want to rethink this
        """
        return UserPostDbModel.POSTS_PREFIX

    @property
    def gsi0_sk(self) -> str:
        """
        Global Secondary Index Sort Key
        In the form of: "title#{self.email}"
        """
        return f"{UserPostDbModel.TITLE_PREFIX}{self.title}"

    @staticmethod
    def gsi0() -> tuple[str, Key]:
        """
        Get the GSI0 index name and key.  This matches the pattern
        for gsi0 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        index_name = "gsi0"
        key = Key(f"{index_name}_pk").eq(UserPostDbModel.POSTS_PREFIX) & Key(
            f"{index_name}_sk"
        ).begins_with(UserPostDbModel.TITLE_PREFIX)

        return index_name, key

    @property
    def gsi1_pk(self) -> str:
        """
        Global Secondary Index PK "posts#"
        this a bit of a HOT key, depending on the size of your user
        base you may want to rethink this
        """
        return UserPostDbModel.POSTS_PREFIX

    @property
    def gsi1_sk(self) -> str:
        """
        Global Secondary Index Sort Key
        In the form of: "lastname#{self.last_name}"
        """
        return f"{UserPostDbModel.TIME_STAMP_PREFIX}{self.timestamp}"

    @staticmethod
    def gsi1(
        start_date_time_utc: datetime.datetime | None = None,
        end_date_time_utc: datetime.datetime | None = None,
    ) -> tuple[str, Key]:
        """
        Get the GSI1 index name and key.  This matches the pattern
        for gsi1 pk & sk for searching (query function), which needs the
        index name and the key
        Returns:
            tuple[Key, str]: The Index Name and the Key
        """
        index_name = "gsi1"
        pk = Key(f"{index_name}_pk").eq(UserPostDbModel.POSTS_PREFIX)
        sk: Key = None
        if start_date_time_utc:
            low_range = start_date_time_utc.timestamp()
            if not end_date_time_utc:
                end_date_time_utc = datetime.datetime.now(datetime.UTC)
            high_range = end_date_time_utc.timestamp()

            sk = Key(f"{index_name}_sk").between(
                f"{UserPostDbModel.TIME_STAMP_PREFIX}{low_range}",
                f"{UserPostDbModel.TIME_STAMP_PREFIX}{high_range}",
            )
        else:
            sk = Key(f"{index_name}_sk").begins_with(UserPostDbModel.TIME_STAMP_PREFIX)

        key = pk & sk
        return index_name, key

    @staticmethod
    def get_projection_expressions() -> tuple[str, dict]:
        """Gets the current projection expressions"""
        projection_expression = (
            "id,user_id,title,data,timestamp,modified_datetime_utc" "#status,#type"
        )
        # status and type are reserved words so once we project them we
        # need alias them, otherwise we'll get an error
        expression_attribute_names = {"#status": "status", "#type": "type"}

        return projection_expression, expression_attribute_names
