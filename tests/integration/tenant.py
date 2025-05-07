"""
Tenant Model
"""

import datetime
from typing import Optional, Literal
from boto3_assist.dynamodb.dynamodb_index import (
    DynamoDBIndex,
    DynamoDBKey,
)
from boto3_assist.dynamodb.dynamodb_model_base import (
    DynamoDBModelBase,
    exclude_from_serialization,
)

from boto3_assist.utilities.datetime_utility import DatetimeUtility


class Tenant(DynamoDBModelBase):
    """Database Model for the Tenant Entity"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=w0622
    ) -> None:
        super().__init__()
        self.id: Optional[str] = id
        self.name: Optional[str] = None
        self.email: Optional[str] = None
        self.subscription_id: Optional[str] = None
        self.type: Optional[str] = None
        self.__status: Optional[str] = None
        self.status_message: str = ""
        self.company_name: Optional[str] = None
        self.created_utc: datetime.datetime = DatetimeUtility.get_utc_now()
        self.modified_utc: datetime.datetime = DatetimeUtility.get_utc_now()
        self.reindexed_utc: Optional[datetime.datetime] = None
        self.__onboard_utc: Optional[datetime.datetime] = None
        self.__setup_indexes()

    def __setup_indexes(self):
        self.indexes.add_primary(
            DynamoDBIndex(
                index_name="primary",
                partition_key=DynamoDBKey(
                    attribute_name="pk",
                    value=lambda: f"tenant#{self.id if self.id else ''}",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="sk",
                    value=lambda: f"tenant#{self.id if self.id else ''}",
                ),
            )
        )

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi0",
                partition_key=DynamoDBKey(
                    attribute_name="gsi0_pk",
                    value="tenants#",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi0_sk",
                    value=lambda: f"name#{self.__sort_name if self.__sort_name else ''}",
                ),
            )
        )

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi1",
                partition_key=DynamoDBKey(
                    attribute_name="gsi1_pk",
                    value="tenants#",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi1_sk",
                    value=lambda: (
                        f"status#{self.status if self.status else ''}"
                        f"name#{self.__sort_name if self.__sort_name else ''}"
                    ),
                ),
            )
        )

        self.indexes.add_secondary(
            DynamoDBIndex(
                index_name="gsi2",
                partition_key=DynamoDBKey(
                    attribute_name="gsi2_pk",
                    value="tenants#",
                ),
                sort_key=DynamoDBKey(
                    attribute_name="gsi2_sk",
                    value=lambda: f"onboard-ts#{self.onboard_utc.timestamp() if self.onboard_utc else ''}",
                ),
            )
        )

    @property
    @exclude_from_serialization
    def modifed_date(self) -> Optional[str]:
        """Backward compatibale db model for modified date"""
        return str(self.modified_utc)

    @modifed_date.setter
    def modifed_date(self, value: Optional[str]) -> None:
        v = DatetimeUtility.to_datetime_utc(value=value)

        self.modified_utc = v or DatetimeUtility.get_utc_now()

    @property
    @exclude_from_serialization
    def onboarding_date(self) -> Optional[str]:
        """Backward compatibale db model for modified date"""
        return str(self.onboard_utc)

    @onboarding_date.setter
    def onboarding_date(self, value: Optional[str]) -> None:
        self.onboard_utc = DatetimeUtility.to_datetime_utc(value=value)

    @property
    @exclude_from_serialization
    def email_address(self) -> Optional[str]:
        """Backward compatibale db model for email address"""
        return self.email

    @email_address.setter
    def email_address(self, value: Optional[str]) -> None:
        self.email = value

    @property
    def onboard_utc(self) -> Optional[datetime.datetime]:
        """The UTC date and time the user was onboarded"""
        return DatetimeUtility.to_datetime_utc(self.__onboard_utc)

    @onboard_utc.setter
    def onboard_utc(self, value: Optional[datetime.datetime]) -> None:
        self.__onboard_utc = DatetimeUtility.to_datetime_utc(
            value=value, default=DatetimeUtility.get_utc_now()
        )

    @property
    def status(self) -> Optional[Literal["enabled", "disabled", "locked"]]:
        """The status of the tenant"""

        return self.__status

    @status.setter
    def status(self, value: Optional[Literal["enabled", "disabled", "locked"]]) -> None:
        if value is not None:
            value = str(value).lower()

        self.__status = value

    @property
    def __sort_name(self) -> Optional[str]:
        if self.name is None:
            return None
        else:
            return self.name.lower()

    @property
    def record_type(self) -> str:
        """
        The type of record we are storing to help load the
        correct object at runtime if needed.
        """
        name = __name__.rsplit(".", maxsplit=1)[-1]
        return name

    @record_type.setter
    def record_type(self, value: str) -> None:
        pass

    @property
    def subscription(self) -> dict | None:
        """The tenants current subscription - if bound to one"""
        return self.__subscription

    @subscription.setter
    def subscription(self, value: dict) -> None:

        self.__subscription = value
