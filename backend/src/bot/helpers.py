import os
import shutil
from pathlib import Path

DIR = Path(__file__).parent.resolve()


def initialize_workspace(path: Path):
    if os.path.isfile(path):
        raise FileExistsError("Specified path is a file")

    if not os.path.isdir(path):
        shutil.copytree(DIR / "templates", path)
