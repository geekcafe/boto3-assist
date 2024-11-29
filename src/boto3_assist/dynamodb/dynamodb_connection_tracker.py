"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from boto3_assist.connection_tracker import ConnectionTracker


class DynamoDBConnectionTracker(ConnectionTracker):
    """
    Tracks DynamoDB Connection Requests.
    Useful in for performance tuning and debugging.
    """

    def __init__(self) -> None:
        super().__init__("DynamoDB")
