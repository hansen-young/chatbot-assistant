import os
from pathlib import Path
from queue import Queue
from typing import Annotated, Literal, TypedDict, overload

from pydantic import Field

from bot.helpers import standardize_path


class FileLine(TypedDict):
    lineno: int
    content: str


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


@overload
def read_file(path: str, show_lines: Literal[True]) -> list[FileLine]: ...


@overload
def read_file(path: str, show_lines: Literal[False]) -> str: ...


def read_file(path: str, show_lines: bool = False) -> list[FileLine] | str:
    """Read the file content from path relative to the current directory."""

    path_ = standardize_path(path)

    if not path_.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path_, "r") as fp:
        if show_lines:
            return [
                {"lineno": i + 1, "content": line.strip("\n")}
                for i, line in enumerate(fp)
            ]
        else:
            return fp.read()


def create_file(path: str):
    """Create a file on the specified path."""

    path_ = standardize_path(path)

    if path_.is_file():
        raise FileExistsError(f"File {path_} already exists.")

    with open(path_, "w") as fp:
        pass

    return {"message": f"Created {path_}."}


def update_file(
    path: Annotated[str, Field(description="path to the file to modify")],
    content: Annotated[str, Field(description="text to insert or replace in the file")],
    mode: Annotated[
        Literal["insert", "replace"],
        Field(
            description="operation mode: 'insert' to insert the content at start_line, 'replace' to replace lines from start_line to end_line"
        ),
    ],
    start_line: Annotated[
        int,
        Field(description="1-based line number where insertion or replacement begins"),
    ] = 1,
    end_line: Annotated[
        int | None,
        Field(
            description="1-based line number where replacement ends; if None and mode is 'replace' it will automatically infer from the length of 'content'"
        ),
    ] = None,
):
    """Update or insert content in a file at a specific line range."""

    path_ = standardize_path(path)
    new_content = content.split("\n")
    file_content = read_file(path, show_lines=True)
    start_line = start_line - 1
    end_line = end_line or start_line + len(new_content)

    if mode == "insert":
        new_content_fmt: list[FileLine] = [
            {"lineno": -1, "content": c} for c in new_content
        ]
        file_content = (
            file_content[:start_line] + new_content_fmt + file_content[start_line:]
        )

    else:
        i = start_line
        j = start_line + len(new_content)

        while len(file_content) < j:
            file_content.append({"lineno": -1, "content": ""})

        for line in new_content:
            file_content[i]["content"] = line
            i += 1

        if i < end_line:
            file_content = file_content[:i] + file_content[end_line:]

    for i in range(len(file_content)):
        file_content[i]["lineno"] = i + 1

    with open(f"{path_}", "w") as fp:
        fp.write("\n".join(line["content"] for line in file_content))

    return {"message": f"Updated '{path_}'."}
