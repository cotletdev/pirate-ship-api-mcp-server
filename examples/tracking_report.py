#!/usr/bin/env python3
"""Shipments of the last N days that are not delivered yet, with their latest tracking event.

    python tracking_report.py --days 7
    python tracking_report.py --days 14 --stuck 4 --out late.csv

--stuck flags labels whose last tracking event is older than that many days.
"""

import argparse
from datetime import date, datetime, timedelta

from pirate_ship_api_mcp.scripting import paginate_offset, run, write_rows


def days_since(stamp: str | None) -> int | None:
    if not stamp:
        return None
    return (datetime.now().astimezone() - datetime.fromisoformat(stamp)).days


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=7, help="Labels bought in the last N days")
    parser.add_argument("--stuck", type=int, default=3, help="Days without a tracking event that count as stuck")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    since = (date.today() - timedelta(days=args.days)).isoformat()
    rows = []
    for s in paginate_offset("list_shipments", {"from_date": since}, "shipments"):
        if s.get("status") == "Refunded" or s.get("tracking_status") == "Delivered":
            continue
        quiet = days_since(s.get("tracking_date") or s.get("created_at"))
        rows.append(
            {
                "recipient": s.get("recipient"),
                "tracking_number": s.get("tracking_number"),
                "carrier": s.get("carrier"),
                "tracking_status": s.get("tracking_status"),
                "last_event": s.get("tracking_info"),
                "estimated_delivery": s.get("estimated_delivery"),
                "days_quiet": quiet,
                "stuck": quiet is not None and quiet >= args.stuck,
            }
        )
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
