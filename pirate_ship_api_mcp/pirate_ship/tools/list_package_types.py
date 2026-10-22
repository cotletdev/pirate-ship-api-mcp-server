"""List package types: the packaging choices and size limits of the shipment form."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


@tool(
    name="list_package_types",
    title="List package types",
    access="read",
    confirm=False,
    description="Packaging types per carrier (box, envelope, flat rate) and the size and weight limits.",
    details=(
        "The packaging keys get_rates and saved packages take, per carrier, with which measurements each "
        "needs, plus Pirate Ship's limits: maximum weight in ounces and side lengths in inches."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /package-types",
    example_response={
        "carriers": [
            {
                "carrier": "usps",
                "package_types": [
                    {
                        "key": "Parcel",
                        "title": "Box or Rigid Packaging",
                        "needs_dimensions": True,
                        "needs_height": True,
                        "needs_weight": True,
                    }
                ],
            }
        ],
        "limits": {"max_weight_oz": 2400, "max_long_side_in": 130, "max_length_plus_girth_in": 165},
    },
)
async def list_package_types(ctx: ToolContext, args: dict[str, Any]) -> Any:
    data = (await graphql(ctx, "PackageTypesQuery"))["data"]
    bounds = (await graphql(ctx, "ShipmentBoundariesQuery"))["data"].get("shipmentBoundaries") or {}
    return {
        "carriers": [
            {
                "carrier": carrier.get("carrierKey"),
                "package_types": [
                    {
                        "key": item.get("packageTypeKey"),
                        "title": item.get("title"),
                        "needs_dimensions": bool(item.get("dimensionsRequired")),
                        "needs_height": bool(item.get("heightRequired")),
                        "needs_weight": bool(item.get("weightRequired")),
                    }
                    for item in carrier.get("packageTypes") or []
                ],
            }
            for carrier in data.get("carriers") or []
        ],
        "limits": {
            "max_weight_oz": bounds.get("maxWeight"),
            "max_long_side_in": bounds.get("maxLongSide"),
            "max_length_plus_girth_in": bounds.get("maxLengthPlusGirth"),
        },
    }
