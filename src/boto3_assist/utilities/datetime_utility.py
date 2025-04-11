"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any
import pytz  # type: ignore
from aws_lambda_powertools import Logger
from dateutil.relativedelta import relativedelta



logger = Logger()

_last_timestamp = None


class DatetimeUtility:
    @staticmethod
    def get_elapsed_time(start: datetime, end=None) -> str:
        end = end or DatetimeUtility.get_utc_now()
        delta: timedelta = end - start

        total_seconds = delta.total_seconds()
        days = int(total_seconds // (3600 * 24))
        total_seconds %= 3600 * 24
        hours = int(total_seconds // 3600)
        total_seconds %= 3600
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(delta.microseconds / 1000)
        timespan = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds, {milliseconds} milliseconds"

        return timespan

    @staticmethod
    def get_start_time() -> datetime:
        return DatetimeUtility.get_utc_now()

    @staticmethod
    def get_utc_now() -> datetime:
        # datetime.utcnow()
        # below is the prefered over datetime.utcnow()
        return datetime.now(timezone.utc)

    @staticmethod
    
    def string_to_date(string_date: str | datetime) -> datetime | None:
        """
        Description: takes a string value and returns it as a datetime.
        If the value is already a datetime type, it will return it as is, otherwise
        the returned value is None
        string_date: str must be in format of %Y-%m-%dT%H:%M:%S.%f
        """

        if not string_date or str(string_date) == "None":
            return None

        if isinstance(string_date, datetime):
            return string_date

        if "Z" in str(string_date):
            string_date = str(string_date).replace("Z", "+00:00")
        string_date = str(string_date)
        string_date = string_date.replace(" ", "T")
        string_date = string_date.replace("Z", "")
        string_date = string_date.replace("+00:00", "")
        # todo determine the format
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%m-%d-%Y",
            "%m-%d-%y",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%m/%d/%y",
        ]

        result: datetime | None = None
        try:
            if isinstance(string_date, str):
                for date_format in date_formats:
                    try:
                        result = datetime.strptime(string_date, date_format)
                        break
                    except ValueError:
                        pass
                # if nothing the we need to raise an error
                if result is None:
                    raise ValueError(f"Unable to parse date: {string_date}")

            elif isinstance(string_date, datetime):
                result = string_date
            else:
                logger.warning(
                    {
                        "metric_filter": "string_to_date_warning",
                        "datetime": string_date,
                        "action": "returning none",
                    }
                )
        except Exception as e:  # noqa: E722, pylint: disable=W0718
            msg = {
                "metric_filter": "string_to_date_error",
                "datetime": string_date,
                "error": str(e),
                "action": "returning none",
                "type": type(string_date).__name__,
                "accepted_formats": date_formats,
            }
            logger.error(msg=msg)

            raise RuntimeError(msg) from e

        return result

    @staticmethod
    def to_datetime(
        value, default: datetime | None = None, tzinfo=UTC
    ) -> datetime | None:
        """
        Description: takes a value and attempts to turn it into a datetime object
        Returns: datetime or None
        """

        result = DatetimeUtility.string_to_date(value)

        if result is None and default is not None:
            if not isinstance(default, datetime):
                default = DatetimeUtility.string_to_date(value)
            result = default

        if result and isinstance(result, datetime):
            result = result.replace(tzinfo=tzinfo)

        return result

    @staticmethod
    def to_datetime_utc(value, default: datetime | None = None) -> datetime | None:
        """
        Description: takes a value and attempts to turn it into a datetime object
        Returns: datetime or None
        """

        result = DatetimeUtility.to_datetime(value, default, tzinfo=UTC)
        return result

    @staticmethod
    def to_date_string(value: Any, default: datetime | None | str = None) -> str | None:
        """
        Description: takes a value and attempts to turn it into a datetime object
        Returns: datetime or None
        """
        value = DatetimeUtility.to_datetime(value=value)
        result = DatetimeUtility.to_string(value, date_format="%Y-%m-%d")
        if result is None and default is not None:
            if isinstance(default, datetime):
                result = DatetimeUtility.to_string(default, date_format="%Y-%m-%d")

        return result

    @staticmethod
    def to_time_string(value, default: datetime | None = None) -> str | None:
        """
        Description: takes a value and attempts to turn it into a datetime object
        Returns: datetime or None
        """
        value = DatetimeUtility.to_datetime(value=value)
        result = f"{DatetimeUtility.to_string(value, date_format='%H:%M:%S')}+00:00"
        if result is None and default is not None:
            result = default

        return result

    @staticmethod
    def to_string(
        value: datetime, date_format: str = "%Y-%m-%d-%H-%M-%S-%f"
    ) -> str | None:
        """
        Description: takes a string value and returns it as a datetime.
        If the value is already a datetime type, it will return it as is, otherwise
        the returned value is None
        """
        # todo determine the format
        if not value:
            return None

        result = value.strftime(date_format)

        return result

    @staticmethod
    def datetime_from_uuid1(uuid1: uuid.UUID) -> datetime:
        """
        Converts a uuid1 to a datetime
        """
        ns = 0x01B21DD213814000
        timestamp = datetime.fromtimestamp(
            (uuid1.time - ns) * 100 / 1e9, tz=timezone.utc
        )
        return timestamp

    @staticmethod
    def fromtimestamp(value: float, default=None) -> datetime:
        result = default
        try:
            if "-" in str(value):
                value = float(str(value).replace("-", "."))
            result = datetime.fromtimestamp(float(value))
        except Exception as e:
            logger.error(str(e))
            pass

        return result

    @staticmethod
    def uuid1_utc(node=0, clock_seq=0, timestamp=None):
        global _last_timestamp  # pylint: disable=w0603

        if not timestamp:
            timestamp = float(DatetimeUtility.get_utc_now().timestamp())
        if isinstance(timestamp, datetime):
            timestamp = timestamp.timestamp()

        nanoseconds = int(timestamp * 1e9)
        # import time
        # t = time.time_ns()
        # ns = int(t * 1e9)

        # 0x01b21dd213814000 is the number of 100-ns intervals between the
        # UUID epoch 1582-10-15 00:00:00 and the Unix epoch 1970-01-01 00:00:00.
        timestamp = nanoseconds // 100 + 0x01B21DD213814000
        if _last_timestamp is not None and timestamp <= _last_timestamp:
            timestamp = _last_timestamp + 1
        _last_timestamp = timestamp
        if clock_seq is None:
            import random

            clock_seq = random.getrandbits(14)  # instead of stable storage
        time_low = timestamp & 0xFFFFFFFF
        time_mid = (timestamp >> 32) & 0xFFFF
        time_hi_version = (timestamp >> 48) & 0x0FFF
        clock_seq_low = clock_seq & 0xFF
        clock_seq_hi_variant = (clock_seq >> 8) & 0x3F
        if node is None:
            node = uuid.getnode()
        return uuid.UUID(
            fields=(
                time_low,
                time_mid,
                time_hi_version,
                clock_seq_hi_variant,
                clock_seq_low,
                node,
            ),
            version=1,
        )

    @staticmethod
    def add_month(dt: datetime, months: int = 1) -> datetime:
        """Add a month to the current date

        Args:
            dt (datetime): datetime
            months (int): the number of months

        Returns:
            datetime: One Month added to the input dt
        """
        new_date = dt + relativedelta(months=+months)
        new_date = new_date + relativedelta(microseconds=-1)

        return new_date

    @staticmethod
    def add_days(dt: datetime, days: int = 1) -> datetime:
        """Add a month to the current date

        Args:
            dt (datetime): datetime
            months (int): the number of months

        Returns:
            datetime: One Month added to the input dt
        """
        new_date = dt + relativedelta(days=+days)
        new_date = new_date + relativedelta(microseconds=-1)

        return new_date

    @staticmethod
    def add_minutes(dt: datetime, minutes: int = 1) -> datetime:
        """Add a month to the current date

        Args:
            dt (datetime): datetime
            months (int): the number of months

        Returns:
            datetime: One Month added to the input dt
        """
        new_date = dt + relativedelta(minutes=+minutes)
        new_date = new_date + relativedelta(microseconds=-1)

        return new_date

    @staticmethod
    def to_timezone(utc_datetime: datetime, timezone_name: str) -> datetime:
        """_summary_

        Args:
            utc_datetime (datetime): datetime in utc
            timezone (str): 'US/Eastern', 'US/Moutain', etc

        Returns:
            datetime: in the correct timezone
        """

        tz = pytz.timezone(timezone_name)
        result = utc_datetime.astimezone(tz)
        return result

    @staticmethod
    def get_timestamp(value: datetime | None | str) -> float:
        """Get a timestampe from a date or 0.0"""
        if value is None:
            return 0.0
        if not isinstance(value, datetime):
            value = DatetimeUtility.to_datetime_utc(value=value)

        if not isinstance(value, datetime):
            return 0.0
        ts = value.timestamp()
        return ts

    @staticmethod
    def get_timestamp_or_none(value: datetime | None | str) -> float | None:
        """Get a timestampe from a date or None"""
        if value is None:
            return None
        if not isinstance(value, datetime):
            value = DatetimeUtility.to_datetime_utc(value=value)

        if not isinstance(value, datetime):
            return None
        ts = value.timestamp()
        return ts
