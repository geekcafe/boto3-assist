"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import json
from typing import List, Union, Optional, IO
from pathlib import Path
from dotenv import load_dotenv
from aws_lambda_powertools import Logger


logger = Logger(__name__)

DEBUGGING = os.getenv("DEBUGGING", "false").lower() == "true"

StrPath = Union[str, "os.PathLike[str]"]


class EnvironmentLoader:
    """Environment Loader"""

    def __init__(self) -> None:
        pass

    def load_environment_file(
        self,
        *,
        starting_path: Optional[str] = None,
        file_name: Optional[str] = None,
        path: Optional[StrPath] = None,
        stream: Optional[IO[str]] = None,
        verbose: bool = False,
        override: bool = True,
        interpolate: bool = True,
        encoding: Optional[str] = "utf-8",
        raise_error_if_not_found: bool = False,
    ) -> bool:
        """
        Loads an environment file into memory. This simply passes off to load_dotenv in dotenv.
        However one small change is that I'm defaulting override to True instead of False.


        Args:
            path: Absolute or relative path to .env file.
            stream: Text stream (such as `io.StringIO`) with .env content, used if
                `dotenv_path` is `None`.
            verbose: Whether to output a warning the .env file is missing.
            override: Whether to override the system environment variables with the variables
                from the `.env` file.
            encoding: Encoding to be used to read the file.
        Returns:
            Bool: True if at least one environment variable is set else False

        If both `dotenv_path` and `stream` are `None`, `find_dotenv()` is used to find the
        .env file.
        """

        if not starting_path:
            starting_path = __file__

        if file_name is None:
            file_name = ".env"

        new_path: str | StrPath | None = path or self.find_file(
            starting_path=starting_path,
            file_name=file_name,
            raise_error_if_not_found=raise_error_if_not_found,
        )

        loaded = load_dotenv(
            dotenv_path=new_path,
            stream=stream,
            verbose=verbose,
            override=override,
            interpolate=interpolate,
            encoding=encoding,
        )

        if DEBUGGING:
            env_vars = os.environ
            logger.debug(f"Loaded environment file: {path}")
            print(env_vars)

        return loaded

    def find_file(
        self, starting_path: str, file_name: str, raise_error_if_not_found: bool = True
    ) -> str | None:
        """Searches the project directory structor for a file"""
        parents = 10
        starting_path = starting_path or __file__

        paths: List[str] = []
        for parent in range(parents):
            path = Path(starting_path).parents[parent].absolute()
            logger.debug(f"searching for {file_name} in: {path}")
            tmp = os.path.join(path, file_name)
            paths.append(tmp)
            if os.path.exists(tmp):
                return tmp

        if raise_error_if_not_found:
            searched_paths = "\n".join(paths)
            raise RuntimeError(
                f"Failed to locate environment file: {file_name} in: \n {searched_paths}"
            )

        return None

    def load_event_file(self, full_path: str) -> dict:
        """Loads an AWS event file"""
        if not os.path.exists(full_path):
            raise RuntimeError(f"Failed to locate event file: {full_path}")

        event = {}
        with open(full_path, mode="r", encoding="utf-8") as json_file:
            event = json.load(json_file)

        if isinstance(event, dict) and "message" in event:
            event = event.get("message", {})

        if isinstance(event, dict) and "event" in event:
            event = event.get("event", {})

        return event
