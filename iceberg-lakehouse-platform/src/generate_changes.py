from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from src.generate_orders import build_order


def load_orders(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def build_changes(orders: list[dict], count: int) -> list[dict]:
    if not orders:
        raise ValueError("At least one existing order is required")

    update_count = min(count // 2, len(orders))
    delete_count = min(count // 4, len(orders) - update_count)
    selected = random.sample(orders, update_count + delete_count)
    changes: list[dict] = []

    for order in selected[:update_count]:
        updated = dict(order)
        updated["operation"] = "update"
        updated["status"] = random.choice(["completed", "refunded"])
        changes.append(updated)

    for order in selected[update_count:]:
        deleted = dict(order)
        deleted["operation"] = "delete"
        changes.append(deleted)

    for index in range(count - len(changes)):
        inserted = build_order(index, datetime.now(timezone.utc))
        inserted["operation"] = "insert"
        changes.append(inserted)

    return changes


def generate(source: Path, output: Path, count: int) -> None:
    changes = build_changes(load_orders(source), count)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for change in changes:
            file.write(json.dumps(change) + "\n")
    print(f"Generated {len(changes)} CDC records at {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("data/generated/orders.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/generated/order_changes.jsonl")
    )
    parser.add_argument("--count", type=int, default=250)
    args = parser.parse_args()
    generate(args.source, args.output, args.count)
