from pathlib import Path
import sys

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pytest_sessionstart(session) -> None:
    src_path = Path(__file__).resolve().parents[1] / "src"
    src_str = str(src_path)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
