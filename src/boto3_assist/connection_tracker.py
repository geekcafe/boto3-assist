"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import traceback
import os


class ConnectionTracker:
    """
    Tracks Connection Requests.
    Useful in for performance tuning and debugging.
    """

    def __init__(self, service_name: str) -> None:
        self.__stack_trace_env_var: str = "BOTO3_ASSIST_CONNECTION_STACK_TRACE"
        self.__connection_counter: int = 0
        self.__service_name: str = service_name
        self.__issue_stack_trace: bool | None = None

    @property
    def issue_stack_trace(self) -> bool:
        """Returns True if the stack trace should be issued"""
        if self.__issue_stack_trace is None:
            self.__issue_stack_trace = (
                os.getenv(self.__stack_trace_env_var, "").lower() == "true"
            )
        return self.__issue_stack_trace

    def increment_connection(self) -> None:
        """Increments the connection counter"""
        self.__connection_counter += 1

        if self.connection_count > 1:
            service_message = ""
            stack_trace_message = ""
            if self.__service_name:
                service_message = f"Your {self.__service_name} service has more than one connection.\n"

            if not self.issue_stack_trace:
                stack_trace_message = (
                    f"\nTo add addtional information to the log and determine where additional connections are being created"
                    f", set the environment variable {self.__stack_trace_env_var} to true.\n"
                )
            else:
                stack = "\n".join(traceback.format_stack())
                stack_trace_message = (
                    f"\nStack Trace Enabeld with {self.__stack_trace_env_var}"
                    f"\n{stack}"
                )

            self.__log_warning(
                f"{service_message}"
                f"Your boto3 connection count is {self.connection_count}. "
                "Under most circumstances you should be able to use the same connection "
                "vs. creating a new one.  Connections are expensive in terms of time / latency. "
                "If you are seeing perforance issues, check how and where you are creating your "
                "connections.  You should be able to pass the connection to your other objects "
                "and reuse your boto3 connections."
                f"{stack_trace_message}"
            )

    def decrement_connection(self) -> None:
        """Decrements the connection counter"""
        self.__connection_counter -= 1

    @property
    def connection_count(self) -> int:
        """Returns the current connection count"""
        return self.__connection_counter

    def reset(self) -> None:
        """Resets the connection counter"""
        self.__connection_counter = 0

    def __log_warning(self, message: str) -> None:
        """Logs a warning message"""
        print(f"Warning: {message}")
