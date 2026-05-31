import os
import shutil
from pathlib import Path

DIR = Path(__file__).parent.resolve()


def initialize_workspace(path: Path):
    if os.path.isfile(path):
        raise FileExistsError("Specified path is a file")

    if not os.path.isdir(path):
        shutil.copytree(DIR / "templates", path)


def standardize_path(path: Path | str):
    if isinstance(path, str):
        # nb: trailing & leading space is valid in UNIX. However most of the time
        #     it is not intended, so we remove it for convenience.
        path = path.strip()
        path = os.path.normpath(path)
        path = os.path.expandvars(path)
        path = Path(path)

    path = path.expanduser()
    path = path.resolve()

    return path
