"""Get rates: Pirate Ship's Quick Rate Quote for one package from the account's ship-from address."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

# USPS package types from RatesConfigQuery; UPS shares Parcel and SoftEnvelope.
PACKAGING = [
    "Parcel",
    "SoftEnvelope",
    "Irregular",
    "SmallFlatRateBox",
    "MediumFlatRateBox",
    "LargeFlatRateBox",
    "FlatRateEnvelope",
    "FlatRateLegalEnvelope",
    "FlatRatePaddedEnvelope",
]
_MARKUP = re.compile(r"\[/?(b|i|link[^\]]*)\]")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "to_zip": {"type": "string", "minLength": 3, "maxLength": 12, "description": "Destination ZIP or postcode."},
        "to_country": {
            "type": "string",
            "pattern": "^[A-Z]{2}$",
            "default": "US",
            "description": "Destination country, ISO 3166-1 alpha-2.",
        },
        "weight_oz": {"type": "number", "exclusiveMinimum": 0, "maximum": 2400, "description": "Weight in ounces."},
        "length_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
        "width_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
        "height_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
        "packaging": {"type": "string", "enum": PACKAGING, "default": "Parcel"},
        "residential": {"type": "boolean", "default": True, "description": "The destination is a home."},
    },
    "required": ["to_zip", "weight_oz"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "from": {"city": "Charlotte", "state": "NC", "zip": "28203"},
    "rates": [
        {
            "carrier": "UPS",
            "service": "UPS Ground Saver®",
            "price_usd": 6.83,
            "retail_usd": 31.43,
            "zone": "4",
            "delivery": "Estimated delivery Thursday 10/22 by 11:00 PM if shipped on 10/19",
            "cheapest": True,
            "fastest": False,
            "best": False,
        },
        {
            "carrier": "USPS",
            "service": "Ground Advantage",
            "price_usd": 6.86,
            "retail_usd": 13.5,
            "zone": "4",
            "delivery": "Estimated delivery Thursday 10/22 by 6:00 PM if shipped on 10/19",
            "cheapest": False,
            "fastest": False,
            "best": False,
        },
    ],
}


def _origin(company: dict[str, Any]) -> dict[str, Any]:
    warehouses = company.get("warehouses") or []
    default = (company.get("settings") or {}).get("defaultWarehouseId")
    found = next((item for item in warehouses if item.get("id") == default), warehouses[0] if warehouses else None)
    if found is None:
        raise ToolError("Add a ship-from address in Pirate Ship first.", ErrorCode.TARGET_ERROR)
    return found["originAddress"]


@tool(
    name="get_rates",
    title="Get rates",
    access="read",
    confirm=False,
    description="USPS and UPS services with price for one package, cheapest first.",
    details=(
        "Pirate Ship's Quick Rate Quote: every USPS and UPS service that can carry one package from your "
        "default ship-from address to to_zip, with your price and the retail price, the zone and the "
        "estimated delivery. Weight in ounces (2 lb = 32). Parcel, SoftEnvelope and Irregular need length_in "
        "and width_in, a box also height_in: size changes the price (cubic and dimensional pricing). Flat "
        "rate envelopes and boxes need only the weight. Services that cannot carry the package are left out. "
        "Nothing is bought."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /rates",
    example_response=EXAMPLE_RESPONSE,
)
async def get_rates(ctx: ToolContext, args: dict[str, Any]) -> Any:
    packaging = args.get("packaging", "Parcel")
    dims = [args.get("length_in"), args.get("width_in"), args.get("height_in")]
    if packaging in ("Parcel", "SoftEnvelope", "Irregular") and not all(dims[:2]):
        raise ToolError(f"{packaging} needs length_in and width_in (and height_in for a box).", ErrorCode.INVALID_INPUT)
    config = (await graphql(ctx, "RatesConfigQuery"))["data"]
    origin = _origin(config.get("company") or {})
    mail_classes = [item["mailClassKey"] for carrier in config.get("carriers") or [] for item in carrier["mailClasses"]]
    variables = {
        "originZip": origin["postcode"],
        "originCity": origin["city"],
        "originRegionCode": origin["regionCode"],
        "isResidential": args.get("residential", True),
        "destinationZip": args["to_zip"].strip(),
        "destinationCountryCode": args.get("to_country", "US"),
        "mailClassKeys": mail_classes,
        "packageTypeKeys": [packaging],
        "weight": args["weight_oz"],
        "dimensionX": dims[0] or 0,
        "dimensionY": dims[1] or 0,
        "dimensionZ": dims[2] or 0,
        "showUpsRatesWhen2x7Selected": True,
    }
    answer = await graphql(ctx, "RatesQuery", variables)
    rates = [
        {
            "carrier": (item.get("carrier") or {}).get("title"),
            "service": item.get("title"),
            "price_usd": item.get("totalPrice"),
            "retail_usd": item.get("crossedTotalPrice"),
            "zone": item.get("zone"),
            "delivery": _MARKUP.sub("", item.get("deliveryDescription") or ""),
            "cheapest": bool(item.get("cheapest")),
            "fastest": bool(item.get("fastest")),
            "best": bool(item.get("best")),
        }
        for item in answer["data"].get("rates") or []
    ]
    rates.sort(key=lambda item: item["price_usd"] if item["price_usd"] is not None else float("inf"))
    return {"from": {"city": origin["city"], "state": origin["regionCode"], "zip": origin["postcode"]}, "rates": rates}
