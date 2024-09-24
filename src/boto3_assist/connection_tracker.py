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
        self.__stack_trace_env_var: str = "ISSUE_STACK_TRACE"
        self.__connection_couter: int = 0
        self.__service_name: str = service_name
        self.__issue_stack_trace: bool = (
            os.getenv(f"{self.__stack_trace_env_var}", "false") == "true"
        )

    def increment_connection(self) -> None:
        """Increments the connection counter"""
        self.__connection_couter += 1

        if self.connection_count > 1:
            service_message = ""
            stack_trace_message = ""
            if self.__service_name:
                service_message = f"Your {self.__service_name} service has more than one connection.\n"

            if not self.__issue_stack_trace:
                stack_trace_message = (
                    f"\nTo add addtional information to the log and determine where additional connections are being created"
                    f", set the environment variable {self.__stack_trace_env_var} to true.\n"
                )
            self.__log_warning(
                f"{service_message}"
                f"Your dynamodb connection count is {self.connection_count}. "
                "Under most circumstances you should be able to use the same connection "
                "vs. creating a new one.  Connections are expensive in terms of time / latency. "
                "If you are seeing perforance issues, check how and where you are creating your "
                "connections.  You should be able to pass the .db connection to your other objects "
                "and reuse your dynamodb boto connections."
                f"{stack_trace_message}"
            )

            # do a stack trace
            if self.__issue_stack_trace:
                print("Stack Trace")
                traceback.print_stack()
                print("")

    def decrement_connection(self) -> None:
        """Decrements the connection counter"""
        self.__connection_couter -= 1

    @property
    def connection_count(self) -> int:
        """Returns the current connection count"""
        return self.__connection_couter

    def reset(self) -> None:
        """Resets the connection counter"""
        self.__connection_couter = 0

    def __log_warning(self, message: str) -> None:
        """Logs a warning message"""
        print(f"Warning: {message}")
