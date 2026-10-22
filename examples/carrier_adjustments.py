#!/usr/bin/env python3
"""List carrier adjustments: extra charges after the carrier measured a package, with the difference.

    python carrier_adjustments.py --since 2026-10-01
    python carrier_adjustments.py --carrier UPS --out adjustments.csv

Shows the weight and size you entered next to what the carrier measured. Disputes go through Pirate Ship.
"""

import argparse

from pirate_ship_api_mcp.scripting import paginate_offset, run, write_rows

KEYS = (
    "created_at",
    "status",
    "tracking_number",
    "recipient",
    "reason",
    "carrier",
    "old_weight_oz",
    "actual_weight_oz",
    "old_length_in",
    "actual_length_in",
    "old_width_in",
    "actual_width_in",
    "old_height_in",
    "actual_height_in",
    "old_cost_usd",
    "actual_cost_usd",
    "adjustment_usd",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", help="First day, YYYY-MM-DD")
    parser.add_argument("--until", help="Last day, YYYY-MM-DD, included")
    parser.add_argument("--carrier", action="append", help="USPS or UPS (repeatable)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    params = {"from_date": args.since, "to_date": args.until, "carrier": args.carrier}
    rows = [{k: a.get(k) for k in KEYS} for a in paginate_offset("list_carrier_adjustments", params, "adjustments")]
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
