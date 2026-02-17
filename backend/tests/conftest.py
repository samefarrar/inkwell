"""Shared test fixtures."""

import pytest

from proof_editor.db import create_tables


@pytest.fixture(autouse=True)
def _setup_db() -> None:
    """Ensure database tables exist before each test."""
    create_tables()
