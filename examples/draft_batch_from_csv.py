#!/usr/bin/env python3
"""Turn a CSV of recipients into an unpaid draft batch and print the rates of each rate group.

    python draft_batch_from_csv.py orders.csv --title "Wholesale 19 Oct" --package "Small box"
    python draft_batch_from_csv.py orders.csv --title "Etsy run" --weight-oz 12 --size 9x6x2

CSV columns: full_name, address1, city, zip, and optionally company, address2, state, country,
email, phone, order_id, weight_oz. Rows without a name, street, city or ZIP are skipped and listed.
Nothing is bought: review the batch in Pirate Ship and buy it there.
"""

import argparse
import csv
import sys

from pirate_ship_api_mcp.scripting import call, run

FIELDS = (
    "full_name",
    "company",
    "address1",
    "address2",
    "city",
    "state",
    "zip",
    "country",
    "email",
    "phone",
    "order_id",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", help="File with one recipient per row")
    parser.add_argument("--title", required=True, help="Batch name")
    parser.add_argument("--package", help="Title of one of your Saved Packages")
    parser.add_argument("--weight-oz", type=float, help="Weight in ounces, without --package")
    parser.add_argument("--size", help="Length x width x height in inches, without --package")
    args = parser.parse_args()

    shipments, skipped = [], []
    with open(args.csv, newline="", encoding="utf-8-sig") as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):
            item = {k: row[k].strip() for k in FIELDS if (row.get(k) or "").strip()}
            if row.get("weight_oz"):
                item["weight_oz"] = float(row["weight_oz"])
            if all(item.get(k) for k in ("full_name", "address1", "city", "zip")):
                shipments.append(item)
            else:
                skipped.append(n)
    if skipped:
        print(f"Skipped rows without name, street, city or ZIP: {skipped}", file=sys.stderr)
    if not shipments:
        sys.exit("No complete rows.")

    params: dict = {"title": args.title, "shipments": shipments[:500]}
    if args.package:
        saved = call("list_saved_packages")["packages"]
        match = next((p for p in saved if p["title"].lower() == args.package.lower()), None)
        if not match:
            sys.exit(f"No Saved Package named {args.package!r}. You have: {[p['title'] for p in saved]}")
        params["package_preset_id"] = match["id"]
    else:
        if not args.weight_oz:
            sys.exit("Pass --package, or --weight-oz (and --size for a box).")
        params["weight_oz"] = args.weight_oz
        if args.size:
            length, width, height = (float(x) for x in args.size.lower().split("x"))
            params.update(length_in=length, width_in=width, height_in=height)

    batch = call("create_batch", params)
    print(f"Draft batch {batch['batch_id']}: {batch['shipment_count']} shipments, {batch['errors']} not rated")
    for rate in batch.get("rates", []):
        mark = " (cheapest)" if rate.get("cheapest") else ""
        print(f"  {rate['group']}: {rate['carrier']} {rate['service']} ${rate['price_usd']} x{rate['shipments']}{mark}")


if __name__ == "__main__":
    run(main)
