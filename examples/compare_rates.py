#!/usr/bin/env python3
"""Compare USPS and UPS rates for one package, cheapest first. Nothing is saved or bought.

    python compare_rates.py --to-zip 10001 --weight-oz 16 --size 10x8x4
    python compare_rates.py --to-zip M5V2T6 --country CA --weight-oz 32 --size 12x10x6
    python compare_rates.py --to-zip 94103 --weight-oz 8 --packaging SoftEnvelope --business

Rates start from your default Ship From Address.
"""

import argparse

from pirate_ship_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--to-zip", required=True, help="Destination ZIP or postcode")
    parser.add_argument("--country", default="US", help="Destination country code, e.g. US, CA, GB")
    parser.add_argument("--weight-oz", type=float, required=True, help="Weight in ounces")
    parser.add_argument("--size", help="Length x width x height in inches, e.g. 10x8x4")
    parser.add_argument("--packaging", default="Parcel", help="Parcel, SoftEnvelope, SmallFlatRateBox ...")
    parser.add_argument("--business", action="store_true", help="The destination is a business, not a home")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    params = {
        "to_zip": args.to_zip,
        "to_country": args.country,
        "weight_oz": args.weight_oz,
        "packaging": args.packaging,
        "residential": not args.business,
    }
    if args.size:
        length, width, height = (float(x) for x in args.size.lower().split("x"))
        params.update(length_in=length, width_in=width, height_in=height)
    answer = call("get_rates", params)
    rows = sorted(answer.get("rates", []), key=lambda r: r.get("price_usd") or 0)
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
