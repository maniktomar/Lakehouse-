"""Shared pytest fixtures for the iceberg-lakehouse-platform test suite."""
from __future__ import annotations

import pytest

from src.generate_orders import build_order
from datetime import datetime, timezone


@pytest.fixture()
def sample_orders() -> list[dict]:
    """Return a small list of well-formed order records."""
    start = datetime.now(timezone.utc)
    return [build_order(i, start) for i in range(20)]


@pytest.fixture()
def single_order(sample_orders: list[dict]) -> dict:
    """Return a single well-formed order record."""
    return sample_orders[0]
