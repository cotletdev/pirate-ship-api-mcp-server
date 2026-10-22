#!/usr/bin/env python3
"""Count today's labels per carrier and quote a pickup for each. Nothing is booked.

    python pickup_quote.py
    python pickup_quote.py --date 2026-10-19 --location SIDE_DOOR

USPS pickups are free and come the next delivery day; UPS charges for them. Book in Pirate Ship.
"""

import argparse
from collections import defaultdict
from datetime import date

from pirate_ship_api_mcp.scripting import call, paginate_offset, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", default=date.today().isoformat(), help="Labels bought on this day, YYYY-MM-DD")
    parser.add_argument("--location", default="FRONT_DOOR", help="FRONT_DOOR, BACK_DOOR, SIDE_DOOR, OFFICE ...")
    args = parser.parse_args()

    params = {"from_date": args.date, "to_date": args.date}
    totals: dict[str, list[float]] = defaultdict(list)
    for s in paginate_offset("list_shipments", params, "shipments"):
        if s.get("status") != "Refunded":
            totals[(s.get("carrier") or "").lower()].append(float(s.get("weight_oz") or 0))
    if not totals:
        print(f"No labels on {args.date}.")
        return
    for carrier, weights in totals.items():
        if carrier not in ("usps", "ups"):
            continue
        quote = call(
            "get_pickup_quote",
            {
                "carrier": carrier,
                "package_count": len(weights),
                "total_weight_oz": sum(weights) or 1,
                "location": args.location,
            },
        )
        print(f"{carrier.upper()}: {len(weights)} packages, {sum(weights):.0f} oz, pickup ${quote['price_usd']}")


if __name__ == "__main__":
    run(main)
