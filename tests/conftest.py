"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def data_root() -> Path:
    """Return path to data directory for canonical entity loading."""
    return Path(__file__).parent.parent / "data"
