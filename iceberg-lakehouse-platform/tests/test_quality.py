"""Unit tests for quality validation rules.

Tests the quality logic in pure Python without requiring a local JVM / PySpark.
The rules mirror exactly what enrich_quality_columns() enforces in Spark:

  1. event_id must not be None
  2. order_id must not be None
  3. quantity > 0
  4. unit_price > 0
  5. abs(order_amount - round(quantity * unit_price, 2)) <= 0.05
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from src.generate_orders import build_order

_UTC = timezone.utc


# ---------------------------------------------------------------------------
# Pure-Python mirror of the quality rules (no Spark / JVM needed)
# ---------------------------------------------------------------------------

def quality_status(row: dict) -> str:
    """Return 'valid' or 'invalid' applying the same rules as quality.py."""
    if row.get("event_id") is None:
        return "invalid"
    if row.get("order_id") is None:
        return "invalid"
    qty = row.get("quantity", 0)
    price = row.get("unit_price", 0)
    amount = row.get("order_amount", 0)
    if qty is None or qty <= 0:
        return "invalid"
    if price is None or price <= 0:
        return "invalid"
    computed = round(qty * price, 2)
    if abs(amount - computed) > 0.05:
        return "invalid"
    return "valid"


# ---------------------------------------------------------------------------
# Quality rule unit tests
# ---------------------------------------------------------------------------

def _valid_row(**overrides) -> dict:
    base = {
        "event_id":     "evt-001",
        "order_id":     "ORD-ABC",
        "quantity":     2,
        "unit_price":   50.0,
        "order_amount": 100.0,
    }
    base.update(overrides)
    return base


def test_valid_row_passes():
    assert quality_status(_valid_row()) == "valid"


def test_null_event_id_is_invalid():
    assert quality_status(_valid_row(event_id=None)) == "invalid"


def test_null_order_id_is_invalid():
    assert quality_status(_valid_row(order_id=None)) == "invalid"


def test_zero_quantity_is_invalid():
    assert quality_status(_valid_row(quantity=0, order_amount=0.0)) == "invalid"


def test_negative_quantity_is_invalid():
    assert quality_status(_valid_row(quantity=-1, order_amount=-50.0)) == "invalid"


def test_zero_unit_price_is_invalid():
    assert quality_status(_valid_row(unit_price=0.0, order_amount=0.0)) == "invalid"


def test_amount_mismatch_beyond_tolerance_is_invalid():
    """order_amount differs from quantity * unit_price by more than $0.05."""
    assert quality_status(_valid_row(order_amount=200.0)) == "invalid"


def test_amount_within_rounding_tolerance_is_valid():
    """Tiny floating-point difference within $0.05 must still pass."""
    assert quality_status(_valid_row(order_amount=100.03)) == "valid"


def test_amount_exactly_at_tolerance_boundary_is_valid():
    assert quality_status(_valid_row(order_amount=100.05)) == "valid"


def test_amount_just_over_tolerance_is_invalid():
    assert quality_status(_valid_row(order_amount=100.06)) == "invalid"


def test_single_item_valid():
    assert quality_status(_valid_row(quantity=1, unit_price=9.99, order_amount=9.99)) == "valid"


# ---------------------------------------------------------------------------
# Cross-check: generated orders must all pass quality rules
# ---------------------------------------------------------------------------

def test_generated_orders_all_pass_quality():
    """Every order from generate_orders.build_order() must be quality-valid."""
    start = datetime.now(_UTC)
    failures = []
    for i in range(100):
        order = build_order(i, start)
        status = quality_status(order)
        if status != "valid":
            failures.append((i, order))
    assert not failures, f"{len(failures)} generated orders failed quality: {failures[:3]}"


def test_generated_order_amount_matches_quantity_times_price():
    """order_amount must equal round(quantity * unit_price, 2) for every order."""
    start = datetime.now(_UTC)
    for i in range(100):
        order = build_order(i, start)
        expected = round(order["quantity"] * order["unit_price"], 2)
        assert math.isclose(order["order_amount"], expected, abs_tol=0.01), (
            f"Order {i}: amount={order['order_amount']}, expected={expected}"
        )


def test_multiple_rows_mixed_validity():
    """Quality function correctly labels a mixed batch."""
    rows = [
        _valid_row(),                                          # valid
        _valid_row(quantity=0, order_amount=0.0),             # invalid — zero qty
        _valid_row(event_id=None),                            # invalid — no event_id
        _valid_row(unit_price=0.0, order_amount=0.0),         # invalid — zero price
        _valid_row(order_amount=999.0),                       # invalid — amount mismatch
        _valid_row(quantity=3, unit_price=9.99, order_amount=29.97),  # valid
    ]
    statuses = [quality_status(r) for r in rows]
    assert statuses.count("valid") == 2
    assert statuses.count("invalid") == 4
