import os
from typing import Annotated

from pydantic import Field


def list_directory(path: str = "."):
    """List the path files and directories in the specified path."""

    out: list[str] = []
    path = os.path.expanduser(path)

    for file_or_dir in os.listdir(path):
        relative_path = os.path.join(path, file_or_dir)

        if os.path.isdir(relative_path):
            out.append(f"{file_or_dir}/")
        else:
            out.append(file_or_dir)

    return {"dir": os.path.abspath(path), "contents": out}


def read_file(path: str):
    """Read the file content from path. Absolute path is preferred, but relative path will work."""

    path = os.path.expanduser(path)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Cannot find a file in {path}")

    with open(path, "r") as fp:
        return fp.read()


def write_file(path: str, content: str):
    """Replace the content of the specified path. Absolute path is preferred, but relative path will work."""

    path = os.path.expanduser(path)

    with open(path, "w") as fp:
        fp.write(content)

    return {"message": f"{path} updated."}
