"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os

import shutil
import tempfile


from aws_lambda_powertools import Logger

logger = Logger()


class FileOperations:
    """
    General File Operations
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def makedirs(path):
        """Create a directory and all sub directories."""
        abs_path = os.path.abspath(path)
        os.makedirs(abs_path, exist_ok=True)

    @staticmethod
    def clean_directory(path: str):
        """Clean / Delete all files and directories and sub directories"""
        if path is None:
            return
        if path == "/":
            raise ValueError("Cannot delete root directory")

        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            items = os.listdir(abs_path)
            for item in items:
                path = os.path.join(abs_path, item)
                if os.path.exists(path):
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        elif os.path.isfile(path):
                            os.remove(path)

                    except Exception as e:  # pylint: disable=W0718
                        logger.exception(f"clean up error {str(e)}")

    @staticmethod
    def get_directory_name(path: str):
        """
        Get the directory path from a path that is either a directory
        or a path to a file.
        """
        dirname = os.path.dirname(path)
        return dirname

    @staticmethod
    def read_file(path: str, encoding: str = "utf-8") -> str:
        """
        Read a file
        """
        logger.debug(f"reading file {path}")
        with open(path, "r", encoding=encoding) as file:
            data = file.read()
        return data

    @staticmethod
    def write_to_file(path: str, data: str, append: bool = False) -> str:
        """
        Write to a file

        """
        return FileOperations.write_file(path=path, output=data, append=append)

    @staticmethod
    def write_file(path: str, output: str, append: bool = False) -> str:
        """
        Writes to a file
        Args:
            path (str): path
            output (str): text to write to the file
            append (bool): if true this operation will append to the file
                otherwise it will overwrite. the default is to overwrite
        Returns:
            str: path to the file
        """
        dirname = FileOperations.get_directory_name(path)
        FileOperations.makedirs(dirname)
        mode = "a" if append else "w"

        if output is None:
            output = ""
        with open(path, mode=mode, encoding="utf-8") as file:
            file.write(output)

        return path

    @staticmethod
    def get_file_extension(file_name: str, include_dot: bool = False):
        """Get the extension of a file"""
        logger.debug(f"getting extension for {file_name}")
        # get the last part of a string after a period .
        extention = os.path.splitext(file_name)[1]
        logger.debug(f"extention is {extention}")

        if not include_dot:
            if str(extention).startswith("."):
                extention = str(extention).removeprefix(".")
                logger.debug(f"extension after prefix removal: {extention}")

        return extention

    @staticmethod
    def get_tmp_directory() -> str:
        """
        Get the temp directory
        """
        # are we in an aws lambda function?
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            # we are in a lambda function /tmp is the only place
            # we can write to
            if not os.path.exists("/tmp"):
                raise ValueError("Temp directory does not exist.")

            tmp_dir = "/tmp"
            return tmp_dir

        return tempfile.gettempdir()
