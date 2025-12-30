"""
SQS module for boto3-assist.

Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

from boto3_assist.sqs.sqs_connection import SQSConnection
from boto3_assist.sqs.sqs_queue import SQSQueue

__all__ = ["SQSConnection", "SQSQueue"]
