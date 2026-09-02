import os
from pathlib import Path


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
