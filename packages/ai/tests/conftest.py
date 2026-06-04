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
    # Pin the seed fixtures: the suite asserts against the known fixture
    # distribution, so it must not depend on whether the real `data/marts`
    # happen to be present (they are, once Sondeig's pipeline runs).
    wh = Warehouse(catalog, use_fixtures=True)
    yield wh
    wh.close()


@pytest.fixture()
def agent() -> Agent:
    """Offline agent (no key) — the default test subject.

    Forces the seed fixtures so the deterministic gate proves the router logic
    and stays stable regardless of the real marts on disk.
    """
    a = Agent(mode="offline", use_fixtures=True)
    yield a
    a.close()
