"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

from .connection import Connection
from .connection_pool import ConnectionPool
from .version import __version__

__all__ = ["Connection", "ConnectionPool"]

print(f"✨ Boto3 Assist - Open Source Boto3 Assist Tool v{__version__}")
