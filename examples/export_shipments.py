#!/usr/bin/env python3
"""Export bought labels to CSV or JSON: recipient, tracking number, carrier, service, cost, status.

    python export_shipments.py --since 2026-10-01 --out october.csv
    python export_shipments.py --carrier UPS --status Printed
    python export_shipments.py --search "Linda Morales"

Every page is followed. For Pirate Ship's own spreadsheet with every column, call export_shipments.
"""

import argparse

from pirate_ship_api_mcp.scripting import paginate_offset, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", help="First day, YYYY-MM-DD")
    parser.add_argument("--until", help="Last day, YYYY-MM-DD, included")
    parser.add_argument("--carrier", action="append", help="USPS or UPS (repeatable)")
    parser.add_argument("--status", action="append", help="Label status, e.g. Printed, Refunded (repeatable)")
    parser.add_argument("--search", help="Free text: name, tracking number, order ID")
    parser.add_argument("--max", type=int, help="Stop after this many labels")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    params = {
        "from_date": args.since,
        "to_date": args.until,
        "carrier": args.carrier,
        "status": args.status,
        "search": args.search,
    }
    rows = list(paginate_offset("list_shipments", params, "shipments", args.max))
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
