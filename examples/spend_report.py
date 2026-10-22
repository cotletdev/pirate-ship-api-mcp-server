#!/usr/bin/env python3
"""Shipping spend for a date range: labels, cost, savings, carrier split, top states and the balance.

    python spend_report.py
    python spend_report.py --since 2026-10-01 --until 2026-10-31
    python spend_report.py --since 2026-10-01 --transactions transactions.csv

The numbers are those of Pirate Ship's Reports page. --transactions also saves every charge,
payment and refund of the range.
"""

import argparse

from pirate_ship_api_mcp.scripting import call, paginate_offset, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", help="First day, YYYY-MM-DD. Default 30 days ago")
    parser.add_argument("--until", help="Last day, YYYY-MM-DD. Default today")
    parser.add_argument("--transactions", help="Also save the transactions to this .csv or .json")
    args = parser.parse_args()

    stats = call("get_shipping_stats", {"from_date": args.since, "to_date": args.until})
    balance = call("get_account_balance")
    labels = stats["labels"]
    print(f"{stats['from_date']} to {stats['to_date']}")
    print(f"  labels      {labels['count']}, ${labels['total_usd']:.2f}, average ${labels['average_usd']:.2f}")
    print(f"  saved       ${stats.get('savings_usd') or 0:.2f} against retail")
    print(f"  adjustments ${stats.get('carrier_adjustments_usd') or 0:.2f}")
    print(
        f"  balance     ${balance.get('balance_usd') or 0:.2f}, pending refunds ${balance['pending_refunds']['amount_usd']:.2f}"
    )
    for item in stats.get("by_carrier", []):
        print(f"  {item['label']:<11} {item['percent']}%")
    for item in stats.get("by_state", [])[:5]:
        print(f"  {item['state']:<11} {item['labels']} labels, ${item['total_usd']:.2f}")

    if args.transactions:
        params = {"from_date": stats["from_date"], "to_date": stats["to_date"]}
        write_rows(list(paginate_offset("list_transactions", params, "transactions")), args.transactions)


if __name__ == "__main__":
    run(main)
