#!/usr/bin/env python3
"""Find labels worth refunding: duplicates to the same recipient and order, and labels never scanned.

    python refund_candidates.py
    python refund_candidates.py --unscanned-after 5 --out refunds.csv

Looks at the last 28 days, the window in which Pirate Ship takes refund requests. It only lists the
labels; refunds are final, so request them in Pirate Ship yourself (Ship > the batch > Refund).
"""

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta

from pirate_ship_api_mcp.scripting import paginate_offset, run, write_rows

NOT_SCANNED = {"", "New", "Pre-Transit", None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--unscanned-after", type=int, default=7, help="Days without a carrier scan")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    since = (date.today() - timedelta(days=28)).isoformat()
    labels = [
        s
        for s in paginate_offset("list_shipments", {"from_date": since}, "shipments")
        if s.get("status") != "Refunded" and s.get("type") == "Label"
    ]
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for s in labels:
        groups[(s.get("recipient"), s.get("address1"), s.get("zip"), s.get("order_id") or "")].append(s)

    now = datetime.now().astimezone()
    rows = []
    for same in groups.values():
        for extra in sorted(same, key=lambda s: s.get("created_at") or "")[1:]:
            rows.append({**pick(extra), "reason": f"duplicate of {same[0].get('tracking_number')}"})
    for s in labels:
        age = (now - datetime.fromisoformat(s["created_at"])).days if s.get("created_at") else 0
        if s.get("tracking_status") in NOT_SCANNED and age >= args.unscanned_after:
            rows.append({**pick(s), "reason": f"no carrier scan in {age} days"})
    write_rows(rows, args.out)


def pick(s: dict) -> dict:
    keys = ("shipment_id", "created_at", "recipient", "order_id", "tracking_number", "carrier", "cost_usd")
    return {k: s.get(k) for k in keys}


if __name__ == "__main__":
    run(main)
