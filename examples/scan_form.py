#!/usr/bin/env python3
"""Make the USPS SCAN Form for today's labels and print its PDF link.

    python scan_form.py
    python scan_form.py --date 2026-10-19
    python scan_form.py --batch 632576079

The carrier scans the one form instead of every package. A form cannot be edited: labels bought
later go on a second form. Free.
"""

import argparse

from pirate_ship_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", help="Ship Date, YYYY-MM-DD. Default today")
    parser.add_argument("--batch", help="Only the labels of this batch id")
    parser.add_argument("--from-address", help="Ship From Address id, when you ship from more than one")
    args = parser.parse_args()

    form = call(
        "create_scan_form", {"ship_date": args.date, "batch_id": args.batch, "from_address_id": args.from_address}
    )
    print(f"SCAN Form {form['id']} for {form['labels']} labels, {form['ship_date']}: {form['url']}")


if __name__ == "__main__":
    run(main)
