"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""


class DynamoDBConnectionTracker:
    """
    Tracks DynamoDB Connection Requests.
    Useful in for performance tuning and debugging.
    """

    def __init__(self) -> None:
        self.__connection_couter: int = 0

    def increment_connection(self) -> None:
        """Increments the connection counter"""
        self.__connection_couter += 1

        if self.connection_count > 1:
            self.__log_warning(
                f"Your dynamodb connection count is {self.connection_count}. "
                "Under most circumstances you should be able to use the same connection "
                "vs. creating a new one.  Connections are expensive in terms of time / latency. "
                "If you are seeing perforance issues, check how and where you are creating your "
                "connections.  You should be able to pass the .db connection to your other objects "
                "and reuse your dynamodb boto connections."
            )

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
