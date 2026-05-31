import os
from pathlib import Path
from queue import Queue
from typing import Annotated

from pydantic import Field

from bot.helpers import standardize_path


def list_directory(path: str = ".", depth: int = 1):
    """List all files and directories in the specified path relative to the current directory."""

    out: list[str] = []
    path_ = standardize_path(path)

    q: Queue[tuple[int, Path]] = Queue()
    q.put((0, path_))

    while not q.empty():
        tdepth, tpath = q.get()

        if tdepth == depth:
            out.append(f"{tpath.relative_to(path_)}/")
            continue

        for file_or_dir in tpath.iterdir():
            if file_or_dir.is_dir():
                q.put((tdepth + 1, file_or_dir))
            else:
                out.append(f"{file_or_dir.relative_to(path_)}")

    return {"dir": str(path_), "contents": sorted(out)}


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
