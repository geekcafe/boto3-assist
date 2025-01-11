"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

import traceback
import os
from typing import Dict


class ConnectionTracker:
    """
    Tracks Boto3 connection requests for performance tuning and debugging.

    Attributes:
        __stack_trace_env_var (str): Environment variable name to enable stack trace logging.
        __issue_stack_trace (bool | None): Caches the result of whether stack trace logging is enabled.
        __connection_counter (Dict[str, int]): Tracks the number of connections per service.
    """

    def __init__(self) -> None:
        self.__stack_trace_env_var: str = "BOTO3_ASSIST_CONNECTION_STACK_TRACE"
        self.__issue_stack_trace: bool | None = None
        self.__connection_counter: Dict[str, int] = {}

    def add(self, service_name: str) -> None:
        """
        Increments the connection count for a given service and
        performs a check on the number of connections.

        Args:
            service_name (str): Name of the AWS service.
        """
        self.__connection_counter[service_name] = (
            self.__connection_counter.get(service_name, 0) + 1
        )

        self.check(service_name=service_name)

    @property
    def issue_stack_trace(self) -> bool:
        """
        Checks if stack trace logging is enabled by the environment variable.

        Returns:
            bool: True if stack trace logging is enabled, False otherwise.
        """
        if self.__issue_stack_trace is None:
            self.__issue_stack_trace = (
                os.getenv(self.__stack_trace_env_var, "").lower() == "true"
            )
        return self.__issue_stack_trace

    def check(self, service_name: str) -> None:
        """
        Checks the connection count for a service and logs warnings if needed.

        Args:
            service_name (str): Name of the AWS service.
        """
        connection_count = self.__connection_counter.get(service_name, 0)
        if connection_count > 1:
            service_message = (
                f"Your {service_name} service has more than one connection.\n"
            )

            if not self.issue_stack_trace:
                stack_trace_message = (
                    f"📄 NOTE: To add additional information 👀 to the log and determine where additional connections are being created: "
                    f"set the environment variable 👉{self.__stack_trace_env_var}👈 to true ✅. \n"
                )
            else:
                stack = "\n".join(traceback.format_stack())
                stack_trace_message = (
                    f"\nStack Trace Enabled with {self.__stack_trace_env_var}\n{stack}"
                )

            self.__log_warning(
                f"{service_message}"
                f"Your boto3 connection count is {connection_count}. "
                "Under most circumstances, you should be able to use the same connection "
                "instead of creating a new one. Connections are expensive in terms of time and latency. "
                "If you are seeing performance issues, check how and where you are creating your "
                "connections. You should be able to pass the connection to your other objects "
                "and reuse your boto3 connections. "
                "\n🧪 MOCK Testing may show this message as well, in which case you can dismiss this warning.🧪\n"
                f"{stack_trace_message}"
            )

    def decrement_connection(self, service_name: str) -> None:
        """
        Decrements the connection count for a service.

        Args:
            service_name (str): Name of the AWS service.
        """
        if (
            service_name in self.__connection_counter
            and self.__connection_counter[service_name] > 0
        ):
            self.__connection_counter[service_name] -= 1

    def reset(self, service_name: str) -> None:
        """
        Resets the connection count for a service to zero.

        Args:
            service_name (str): Name of the AWS service.
        """
        self.__connection_counter[service_name] = 0

    def __log_warning(self, message: str) -> None:
        """
        Logs a warning message.

        Args:
            message (str): The warning message to log.
        """
        print(f"Warning: {message}")
