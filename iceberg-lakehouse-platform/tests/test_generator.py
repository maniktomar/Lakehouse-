"""Extended tests for order and change generation."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.generate_changes import build_changes
from src.generate_orders import build_order

_UTC = timezone.utc


# ── build_order tests ────────────────────────────────────────────────────────

def test_build_order_is_consistent():
    event = build_order(1, datetime.now(_UTC))
    assert event["quantity"] > 0
    assert event["unit_price"] > 0
    assert event["order_amount"] == round(event["quantity"] * event["unit_price"], 2)
    assert event["status"] in {"completed", "cancelled", "refunded"}


def test_build_order_has_all_required_fields():
    required = {
        "event_id", "event_time", "order_id", "customer_id", "customer_email",
        "product_id", "category", "quantity", "unit_price", "order_amount",
        "currency", "sales_channel", "country", "status",
    }
    event = build_order(0, datetime.now(_UTC))
    assert required.issubset(event.keys()), f"Missing fields: {required - event.keys()}"


def test_build_order_known_categories():
    """Category must be one of the five defined product categories."""
    known = {"electronics", "home", "sports", "fashion", "beauty"}
    for i in range(50):
        event = build_order(i, datetime.now(_UTC))
        assert event["category"] in known


def test_build_order_known_currencies():
    known = {"USD", "GBP", "EUR"}
    for i in range(50):
        event = build_order(i, datetime.now(_UTC))
        assert event["currency"] in known


def test_build_order_known_channels():
    known = {"web", "mobile", "store", "partner"}
    for i in range(50):
        event = build_order(i, datetime.now(_UTC))
        assert event["sales_channel"] in known


# ── build_changes tests ──────────────────────────────────────────────────────

def test_build_changes_contains_supported_operations():
    orders = [build_order(i, datetime.now(_UTC)) for i in range(20)]
    changes = build_changes(orders, 12)
    operations = {row["operation"] for row in changes}

    assert len(changes) == 12
    assert operations <= {"insert", "update", "delete"}
    assert "insert" in operations


def test_build_changes_exact_count(sample_orders):
    for count in [5, 10, 20, 50]:
        changes = build_changes(sample_orders, count)
        assert len(changes) == count, f"Expected {count} changes, got {len(changes)}"


def test_build_changes_updates_are_subset_of_existing(sample_orders):
    """Updated orders must come from the existing order pool."""
    existing_ids = {o["order_id"] for o in sample_orders}
    changes = build_changes(sample_orders, 20)
    for change in changes:
        if change["operation"] == "update":
            assert change["order_id"] in existing_ids


def test_build_changes_deletes_are_subset_of_existing(sample_orders):
    """Deleted orders must come from the existing order pool."""
    existing_ids = {o["order_id"] for o in sample_orders}
    changes = build_changes(sample_orders, 20)
    for change in changes:
        if change["operation"] == "delete":
            assert change["order_id"] in existing_ids


def test_build_changes_inserts_have_new_ids(sample_orders):
    """Inserted orders should be newly generated, not from the existing pool."""
    changes = build_changes(sample_orders, 30)
    for change in changes:
        if change["operation"] == "insert":
            assert "order_id" in change


def test_build_changes_raises_on_empty_orders():
    with pytest.raises(ValueError, match="At least one existing order is required"):
        build_changes([], 10)


def test_build_changes_updates_change_status(sample_orders):
    """Updated records must have a valid status value."""
    valid_statuses = {"completed", "refunded"}
    changes = build_changes(sample_orders, 20)
    for change in changes:
        if change["operation"] == "update":
            assert change["status"] in valid_statuses, (
                f"Unexpected status '{change['status']}' for update operation"
            )
