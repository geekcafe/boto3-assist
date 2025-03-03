"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import math
from typing import List, Optional
from aws_lambda_powertools import Logger

logger = Logger()


class NumberUtility:
    """
    Number Utility.
    """

    @staticmethod
    def is_numeric(value: str | None | int | float) -> bool:
        """
        Determines if a value is a number or not.  This will remove any dashes, periods "-", "."
        and then determine if the value is numeric
        Args:
            value (str): string value of a number

        Returns:
            bool: _description_
        """
        if value is None:
            return False

        if value is None:
            return False

        if str(value).isnumeric():
            return True
        try:
            float(value)
            return True
        except:  # noqa: E722, pylint: disable=w0702
            return False

    @staticmethod
    def are_numeric(values: List[int] | List[str] | List[float]) -> bool:
        """determines if a set of values are numeric or not"""
        for value in values:
            if not NumberUtility.is_numeric(value):
                return False

        return True

    @staticmethod
    def to_number_or_none(value: str) -> float | int | None:
        """Converts a string to a number."""
        if value is None:
            return None

        if str(value).lower() == "nan":
            return None

        try:
            numeric_value = float(value)
            # Check if the number is an integer (e.g., 7.0) and return as int
            if numeric_value.is_integer():
                return int(numeric_value)
            return numeric_value
        except (ValueError, TypeError):
            return None

    @staticmethod
    def to_float(
        value: str | float | int, raise_errors: Optional[bool] = False
    ) -> float:
        """_summary_

        Args:
            value (str | float | int): _description_



        Returns:
            float: returns a float of zero.
        """
        try:
            return float(value)
        except:  # noqa: E722, pylint: disable=w0702
            logger.error(f"Unable to convert {value} to float")
            if raise_errors:
                raise
            return 0.0

    @staticmethod
    def get_max_length(items: List[str] | List[int] | List[float]) -> int:
        """Returns the max length of an item in a list."""
        length = 0
        for item in items:
            if len(str(item)) > length:
                length = len(str(item))

        return length

    @staticmethod
    def to_significant_digits_rounded(value, significant_digits=10):
        """
        converts to significant digits
        """
        result = math.floor(value * 10**significant_digits) / 10**significant_digits
        to_the_right = len(f"{int(value)}")
        f_string_number = (
            f"{value:.{significant_digits + to_the_right}g}"  # Using f-string
        )
        result = float(f_string_number)

        return result

    @staticmethod
    def get_number_of_decimal_places(number: float) -> int:
        """
        Gets the number decimal places

        Args:
            number (float): the number to inspect

        Returns:
            int: number of decimal places
        """

        number_str = f"{number}"
        if "." in number_str:
            to_the_right = number_str.split(".")[1]
            return len(to_the_right)

        return 0

    @staticmethod
    def to_significant_digits(number: float, significant_digits: int = 10):
        """To Significat Digits"""
        # make sure we're dealing with a number
        number = float(number)
        if significant_digits < 0:
            raise ValueError("Decimal places must be non-negative")
        else:
            number_str = f"{number}"
            if "." in number_str:
                decimal_point_index = number_str.index(".")
                number_of_decimal_places = NumberUtility.get_number_of_decimal_places(
                    number
                )
                if number_of_decimal_places > significant_digits:
                    return NumberUtility.to_significant_digits_rounded(
                        number, significant_digits
                    )
                else:
                    cutoff_index = decimal_point_index + significant_digits + 1
                    truncated_str = number_str[:cutoff_index]
                    return float(truncated_str)
            else:
                return number

    @staticmethod
    def is_decimal(value):
        is_numeric = NumberUtility.is_numeric(value)
        contains_decimal = "." in str(value)

        return is_numeric and contains_decimal

    @staticmethod
    def percent_difference(number1, number2):
        """
        Calculate the percent difference between two numbers.

        Parameters:
        - number1: The first number.
        - number2: The second number.

        Returns:
        - The percent difference between the two numbers.
        """
        number1 = float(number1)
        number2 = float(number2)
        # Calculate the absolute difference between the two numbers
        difference = abs(number1 - number2)

        # Calculate the average of the two numbers
        average = (number1 + number2) / 2

        if difference > 0:
            # Calculate the percent difference
            percent_diff = (difference / average) * 100

            return percent_diff

        return 0.0

    @staticmethod
    def to_number(
        value: str | float | int,
        raise_errors: Optional[bool] = False,
        error_message: Optional[str] = None,
    ) -> int | float:
        """Converts a string to a number."""
        try:
            numeric_value = float(value)
            # Check if the number is an integer (e.g., 7.0) and return as int
            if numeric_value.is_integer():
                return int(numeric_value)
            return numeric_value
        except Exception as e:  # noqa: E722, pylint: disable=w0718
            logger.error(f"Unable to convert {value} to number")
            if raise_errors:
                if error_message:
                    raise ValueError(
                        f"Unable to convert {value} to number, {error_message}"
                    ) from e
                else:
                    raise ValueError(f"Unable to convert {value} to number") from e
            return 0

    @staticmethod
    def to_significant_figure(
        number: int | float | str, sig_figs: int
    ) -> int | float | str:
        """
        Formats a number to it's significant figures.
        Examples
             12345.6789, 4 = 12350

        Args:
            number (int | float | str): a valid number
            sig_figs (int): the number of signigicant figures

        Returns:
            int | float: the value after applying a significant figure
        """
        # just used for tracking
        original_value = number
        value: int | float | str = 0
        if str(number).lower() == "nan":
            return number

        if NumberUtility.is_numeric(number) and isinstance(number, str):
            number = NumberUtility.to_number(
                number,
                raise_errors=True,
                error_message=(
                    f"Error attempting to set significant figure for value {number}"
                    f", sigfig {sig_figs}"
                ),
            )

        if number == 0:
            if sig_figs > 1:
                value = "0." + "0" * (sig_figs - 1)
            else:
                value = 0

        else:
            scale = int(math.floor(math.log10(abs(float(number)))))
            pre_power = int(scale - sig_figs + 1)

            factor = 10 ** (pre_power)
            rounded = round(number / factor) * factor

            if not isinstance(rounded, int):
                value = f"{rounded:.{sig_figs}g}"
            else:
                value = f"{rounded}"

        if "." in f"{value}" and len(f"{value}") >= (sig_figs):
            value = float(value)
        elif "." in f"{value}" and len(f"{value}") <= (sig_figs + 1):
            # there are more sig figures in the length of the figures
            # adding 1 to account for the decimal place
            value = float(value)
        else:
            # due to the scientific express we need to float it first
            value = float(value)
            value = int(value)

        logger.debug(
            {
                "source": "",
                "sig": sig_figs,
                "value": {"original": original_value, "converted": value},
            }
        )

        return value

    @staticmethod
    def get_significant_figure(value) -> int:
        """
        Calculate the number of significant figures in a number.
        Removes leading and trailing zeros for float numbers.
        """
        if not value:
            return 0
        if isinstance(value, int) or isinstance(value, int):
            return len(str(value).strip("0"))
        elif isinstance(value, float):
            if value == 0:
                return 0
            else:
                length: int = 0
                if value > 1:
                    value_str = f"{value}"
                    digits = value_str
                    number = digits.split(".")
                    left = number[0].lstrip("0")
                    right = ""
                    if len(number) > 1:
                        right = f"{number[1].rstrip('0')}"

                    digits_stripped = f"{left}{right}"
                    # Remove decimal point and trailing zeros
                    length = len(digits_stripped)

                else:
                    value_str = f"{value}"
                    # remove the "." remove all left and right decimals
                    # example: 0.0012 becomes 12 with sig digit of 2
                    digits_stripped = value_str.replace(".", "").rstrip("0").lstrip("0")
                    length = len(digits_stripped)

                return length

        else:
            return 0
