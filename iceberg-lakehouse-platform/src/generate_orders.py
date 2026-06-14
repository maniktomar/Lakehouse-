from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

PRODUCTS = [
    ("SKU-1001", "electronics", 799.0),
    ("SKU-1002", "home", 149.0),
    ("SKU-1003", "sports", 99.0),
    ("SKU-1004", "fashion", 69.0),
    ("SKU-1005", "beauty", 39.0),
]
COUNTRY_CODES = ["US", "GB", "DE", "FR", "IN", "CA", "AU"]


def build_order(index: int, start: datetime) -> dict:
    product_id, category, base_price = random.choice(PRODUCTS)
    quantity = random.randint(1, 5)
    unit_price = round(base_price * random.uniform(0.8, 1.2), 2)
    event_time = start + timedelta(seconds=index * random.randint(1, 4))
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": event_time.isoformat(),
        "order_id": f"ORD-{uuid.uuid4().hex[:12].upper()}",
        "customer_id": f"CUST-{random.randint(10000, 99999)}",
        "customer_email": f"customer{random.randint(10000, 99999)}@example.com",
        "product_id": product_id,
        "category": category,
        "quantity": quantity,
        "unit_price": unit_price,
        "order_amount": round(quantity * unit_price, 2),
        "currency": random.choice(["USD", "GBP", "EUR"]),
        "sales_channel": random.choice(["web", "mobile", "store", "partner"]),
        "country": random.choice(COUNTRY_CODES),
        "status": random.choices(["completed", "cancelled", "refunded"], [0.9, 0.06, 0.04])[0],
    }


def generate(output: Path, count: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc) - timedelta(hours=2)
    with output.open("w", encoding="utf-8") as file:
        for index in range(count):
            file.write(json.dumps(build_order(index, start)) + "\n")
    print(f"Generated {count} orders at {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--output", type=Path, default=Path("data/generated/orders.jsonl"))
    args = parser.parse_args()
    generate(args.output, args.count)
