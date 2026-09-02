import os
from pathlib import Path
from queue import Queue
from typing import Annotated, Literal

from pydantic import Field

from core.tools import registry
from core.utils import standardize_path


@registry.register("filesystem")
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


@registry.register("filesystem")
def read_file(
    path: Annotated[
        str,
        Field(description="Path to the file to read (absolute / relative)."),
    ],
    start_line: Annotated[
        int,
        Field(description="Line number to start reading from (1-indexed)"),
    ] = 1,
    limit: Annotated[
        int,
        Field(description="Maximum number of lines to read"),
    ] = 100,
) -> str:
    """Read file content from the specified path. Values are returned as <lineno>| <content>. Long contents are automatically truncated, call tool again with `start_line` offset specified to continue reading."""

    max_length = 1_000_000
    curr_length = 0
    contents: list[str] = []
    path_ = standardize_path(path)
    end_line = start_line + limit

    if not path_.is_file():
        raise FileNotFoundError(f"File not found: {path_}")

    with open(path_, "r") as fp:
        for i, line in enumerate(fp, start=1):
            if i < start_line:
                continue

            if i >= end_line:
                break

            if curr_length + len(line) > max_length:
                contents.append(f"{i}| {line[:max_length - curr_length]}...")
                break

            contents.append(f"{i}| {line}")
            curr_length += len(line)

    return "".join(contents)


@registry.register("filesystem")
def create_file(path: str = "s"):
    """Create a file on the specified path."""

    path_ = standardize_path(path)

    if path_.is_file():
        raise FileExistsError(f"File {path_} already exists.")

    with open(path_, "w") as fp:
        pass

    return {"message": f"Created {path_}."}


@registry.register("filesystem")
def update_file(
    path: Annotated[
        str,
        Field(description="Path to the file to modify (absolute / relative)."),
    ],
    content: Annotated[str, Field(description="text to insert or replace in the file")],
    mode: Annotated[
        Literal["append", "replace_line", "overwrite"],
        Field(
            description="'append' adds content from `start_line`, 'replace_line' updates existing lines, 'overwrite' deletes the file content then writes the new content"
        ),
    ],
    start_line: Annotated[
        int,
        Field(
            description="Line number where append or replace_line begins (1-indexed)"
        ),
    ] = 1,
    end_line: Annotated[
        int | None,
        Field(
            description="Line number where replacement ends (1-indexed); if not specified, it will automatically infer from the length of 'content'"
        ),
    ] = None,
):
    """Update or insert content in a file at a specific line range."""

    path_ = standardize_path(path)
    new_content = content.split("\n")
    file_content = open(path_, "r").read().splitlines()
    start_line = max(0, start_line - 1)
    end_line = end_line or start_line + len(new_content)

    if mode == "append":
        file_content = (
            file_content[:start_line] + new_content + file_content[start_line:]
        )

    elif mode == "replace_line":
        i = start_line
        j = start_line + len(new_content)

        while len(file_content) < j:
            file_content.append("")

        for line in new_content:
            file_content[i] = line
            i += 1

        if i < end_line:
            file_content = file_content[:i] + file_content[end_line:]

    else:
        open(path_, "w").close()
        file_content = new_content

    with open(f"{path_}", "w") as fp:
        fp.write("\n".join(line for line in file_content))

    return {"message": f"Updated '{path_}'."}


@registry.register("filesystem")
def create_directory(path: str):
    """Create a new directory in the specified path relative to the current directory."""

    path_ = standardize_path(path)

    if path_.exists():
        raise FileExistsError(f"Directory {path_} exists.")

    os.makedirs(path_)

    return {"message": f"Created directory {path_}."}
