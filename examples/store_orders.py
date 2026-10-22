#!/usr/bin/env python3
"""Pull new orders from your connected stores (Shopify, Etsy, eBay ...) and list what waits to ship.

    python store_orders.py
    python store_orders.py --no-sync --out open-orders.csv

The sync is Pirate Ship's Refresh Data. With no store connected, the list is empty.
"""

import argparse

from pirate_ship_api_mcp.scripting import call, paginate_offset, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-sync", action="store_true", help="Only list, do not refresh the stores first")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    if not args.no_sync:
        state = call("sync_store_orders", {"wait_seconds": 30})
        if state.get("running"):
            print("Stores are still syncing; the list may miss the newest orders.")
    rows = list(paginate_offset("list_import_orders", {}, "rows"))
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
