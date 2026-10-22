#!/usr/bin/env python3
"""List your Ship From Addresses and Saved Packages: the ids that batches, rates and SCAN Forms take.

python ship_from_addresses.py
"""

import argparse

from pirate_ship_api_mcp.scripting import call, run


def main() -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    for a in call("list_ship_from_addresses")["addresses"]:
        o = a.get("origin") or {}
        star = " (default)" if a.get("default") else ""
        print(
            f"address {a['id']}{star}: {o.get('full_name')}, {o.get('address1')}, {o.get('city')} {o.get('state')} {o.get('zip')}"
        )
    for p in call("list_saved_packages")["packages"]:
        star = " (default)" if p.get("default") else ""
        size = (
            f"{p.get('length_in')}x{p.get('width_in')}x{p.get('height_in')} in"
            if p.get("length_in")
            else p.get("packaging")
        )
        print(f"package {p['id']}{star}: {p['title']}, {size}, {p.get('weight_oz')} oz")


if __name__ == "__main__":
    run(main)
