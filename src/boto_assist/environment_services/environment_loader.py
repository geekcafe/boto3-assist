import os
from typing import IO, Optional, Union
from dotenv import load_dotenv

StrPath = Union[str, "os.PathLike[str]"]


class EnvironmentLoader:
    def __init__(self) -> None:
        pass

    def load_environment_file(
        self,
        path: Optional[StrPath] = None,
        stream: Optional[IO[str]] = None,
        verbose: bool = False,
        override: bool = True,
        interpolate: bool = True,
        encoding: Optional[str] = "utf-8",
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
        return load_dotenv(
            dotenv_path=path,
            stream=stream,
            verbose=verbose,
            override=override,
            interpolate=interpolate,
            encoding=encoding,
        )
