import os
from pathlib import Path


def get_version() -> str:
    if os.getenv("DOCKER_ENV"):
        version_path = Path("/app/VERSION")
    elif os.getcwd().endswith("backend"):
        version_path = Path("../VERSION")
    elif os.getcwd().endswith("commongraph"):
        version_path = Path("VERSION")
    else:
        raise FileNotFoundError("VERSION file not found")
    return version_path.read_text().strip()


__version__ = get_version()
