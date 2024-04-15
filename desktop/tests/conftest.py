from typing import Generator

import pytest

from app.consts import BASE_DIR

TEST_ARC = str(BASE_DIR / "tests/data/test.zip")


@pytest.fixture
def no_archive() -> Generator[str, None, None]:
    import os

    if os.path.exists(TEST_ARC):
        os.remove(TEST_ARC)
    yield TEST_ARC
    if os.path.exists(TEST_ARC):
        os.remove(TEST_ARC)
