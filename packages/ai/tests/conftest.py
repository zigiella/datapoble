"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PKG_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from datapoble_ai import Agent, Catalog, Warehouse  # noqa: E402
from datapoble_ai.catalog import load_catalog  # noqa: E402


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return load_catalog()


@pytest.fixture()
def warehouse(catalog) -> Warehouse:
    wh = Warehouse(catalog)
    yield wh
    wh.close()


@pytest.fixture()
def agent() -> Agent:
    """Offline agent (no key) — the default test subject."""
    a = Agent(mode="offline")
    yield a
    a.close()
