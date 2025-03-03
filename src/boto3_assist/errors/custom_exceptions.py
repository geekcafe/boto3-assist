class Error(Exception):
    """Base class for exceptions in this module."""


class DbFailures(Error):
    """DB Failure Error"""


class InvalidHttpMethod(Exception):
    """Invalid Http Method"""

    def __init__(
        self,
        code=422,
        message="Invalid Http Method",
    ):
        """The user account is not valid"""
        self.message = {
            "status_code": code,
            "message": message,
        }
        super().__init__(self.message)


class InvalidRoutePath(Exception):
    """Invalid Http Route"""

    def __init__(self, message="Invalid Route"):
        """Invalid Route"""
        self.message = {
            "status_code": 404,
            "message": message,
        }
        super().__init__(self.message)


class FileNotFound(Exception):
    """File Not Found Error"""

    def __init__(self, message="File Not Found"):
        """Invalid Route"""
        self.message = {
            "status_code": 404,
            "message": message,
        }
        super().__init__(self.message)
