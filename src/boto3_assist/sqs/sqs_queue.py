"""
SQS Queue operations module.

Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

import json
from typing import Any, Dict, List, Optional

from aws_lambda_powertools import Logger

from boto3_assist.sqs.sqs_connection import SQSConnection

logger = Logger(child=True)


class SQSQueue(SQSConnection):
    """SQS Queue operations wrapper."""

    def __init__(
        self,
        *,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_end_point_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        """
        Initialize SQS Queue.

        Args:
            aws_profile: AWS profile name
            aws_region: AWS region
            aws_end_point_url: Custom endpoint URL (for LocalStack, etc.)
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
        """
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            aws_end_point_url=aws_end_point_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def send_message(
        self,
        queue_url: str,
        message_body: str,
        delay_seconds: int = 0,
        message_attributes: Optional[Dict[str, Any]] = None,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None,
    ) -> str:
        """
        Send a message to an SQS queue.

        Args:
            queue_url: The URL of the SQS queue
            message_body: The message body (string)
            delay_seconds: Delay before message becomes visible (0-900 seconds)
            message_attributes: Optional message attributes
            message_group_id: Required for FIFO queues
            message_deduplication_id: Required for FIFO queues without content-based deduplication

        Returns:
            The message ID of the sent message
        """
        params: Dict[str, Any] = {
            "QueueUrl": queue_url,
            "MessageBody": message_body,
        }

        if delay_seconds > 0:
            params["DelaySeconds"] = min(delay_seconds, 900)  # SQS max is 900 seconds

        if message_attributes:
            params["MessageAttributes"] = message_attributes

        if message_group_id:
            params["MessageGroupId"] = message_group_id

        if message_deduplication_id:
            params["MessageDeduplicationId"] = message_deduplication_id

        response = self.client.send_message(**params)
        message_id = response.get("MessageId", "")

        logger.debug(f"Sent message to {queue_url}: {message_id}")
        return message_id

    def send_message_batch(
        self,
        queue_url: str,
        entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Send multiple messages to an SQS queue in a batch.

        Args:
            queue_url: The URL of the SQS queue
            entries: List of message entries, each with 'Id' and 'MessageBody'

        Returns:
            Response containing 'Successful' and 'Failed' lists
        """
        response = self.client.send_message_batch(
            QueueUrl=queue_url,
            Entries=entries,
        )

        successful = response.get("Successful", [])
        failed = response.get("Failed", [])

        if failed:
            logger.warning(f"Failed to send {len(failed)} messages to {queue_url}")

        logger.debug(f"Sent batch of {len(successful)} messages to {queue_url}")
        return response

    def receive_messages(
        self,
        queue_url: str,
        max_number_of_messages: int = 1,
        wait_time_seconds: int = 0,
        visibility_timeout: Optional[int] = None,
        message_attribute_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from an SQS queue.

        Args:
            queue_url: The URL of the SQS queue
            max_number_of_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Long polling wait time (0-20 seconds)
            visibility_timeout: Override the queue's default visibility timeout
            message_attribute_names: List of message attribute names to retrieve

        Returns:
            List of messages
        """
        params: Dict[str, Any] = {
            "QueueUrl": queue_url,
            "MaxNumberOfMessages": min(max_number_of_messages, 10),
            "WaitTimeSeconds": min(wait_time_seconds, 20),
        }

        if visibility_timeout is not None:
            params["VisibilityTimeout"] = visibility_timeout

        if message_attribute_names:
            params["MessageAttributeNames"] = message_attribute_names

        response = self.client.receive_message(**params)
        messages = response.get("Messages", [])

        logger.debug(f"Received {len(messages)} messages from {queue_url}")
        return messages

    def delete_message(
        self,
        queue_url: str,
        receipt_handle: str,
    ) -> None:
        """
        Delete a message from an SQS queue.

        Args:
            queue_url: The URL of the SQS queue
            receipt_handle: The receipt handle of the message to delete
        """
        self.client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle,
        )
        logger.debug(f"Deleted message from {queue_url}")

    def delete_message_batch(
        self,
        queue_url: str,
        entries: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Delete multiple messages from an SQS queue in a batch.

        Args:
            queue_url: The URL of the SQS queue
            entries: List of entries with 'Id' and 'ReceiptHandle'

        Returns:
            Response containing 'Successful' and 'Failed' lists
        """
        response = self.client.delete_message_batch(
            QueueUrl=queue_url,
            Entries=entries,
        )

        logger.debug(f"Deleted batch of messages from {queue_url}")
        return response

    def get_queue_url(self, queue_name: str) -> str:
        """
        Get the URL of an SQS queue by name.

        Args:
            queue_name: The name of the queue

        Returns:
            The queue URL
        """
        response = self.client.get_queue_url(QueueName=queue_name)
        return response["QueueUrl"]

    def get_queue_attributes(
        self,
        queue_url: str,
        attribute_names: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Get attributes of an SQS queue.

        Args:
            queue_url: The URL of the SQS queue
            attribute_names: List of attribute names to retrieve (default: All)

        Returns:
            Dictionary of queue attributes
        """
        params: Dict[str, Any] = {"QueueUrl": queue_url}

        if attribute_names:
            params["AttributeNames"] = attribute_names
        else:
            params["AttributeNames"] = ["All"]

        response = self.client.get_queue_attributes(**params)
        return response.get("Attributes", {})

    def purge_queue(self, queue_url: str) -> None:
        """
        Purge all messages from an SQS queue.

        Args:
            queue_url: The URL of the SQS queue

        Note: This action can only be performed once every 60 seconds.
        """
        self.client.purge_queue(QueueUrl=queue_url)
        logger.info(f"Purged queue: {queue_url}")

    def change_message_visibility(
        self,
        queue_url: str,
        receipt_handle: str,
        visibility_timeout: int,
    ) -> None:
        """
        Change the visibility timeout of a message.

        Args:
            queue_url: The URL of the SQS queue
            receipt_handle: The receipt handle of the message
            visibility_timeout: New visibility timeout in seconds (0-43200)
        """
        self.client.change_message_visibility(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=visibility_timeout,
        )
        logger.debug(f"Changed visibility timeout for message in {queue_url}")

    def send_json_message(
        self,
        queue_url: str,
        message: Dict[str, Any],
        delay_seconds: int = 0,
        message_attributes: Optional[Dict[str, Any]] = None,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None,
    ) -> str:
        """
        Send a JSON message to an SQS queue.

        Convenience method that serializes a dict to JSON.

        Args:
            queue_url: The URL of the SQS queue
            message: Dictionary to serialize and send
            delay_seconds: Delay before message becomes visible
            message_attributes: Optional message attributes
            message_group_id: Required for FIFO queues
            message_deduplication_id: Required for FIFO queues

        Returns:
            The message ID of the sent message
        """
        return self.send_message(
            queue_url=queue_url,
            message_body=json.dumps(message),
            delay_seconds=delay_seconds,
            message_attributes=message_attributes,
            message_group_id=message_group_id,
            message_deduplication_id=message_deduplication_id,
        )
