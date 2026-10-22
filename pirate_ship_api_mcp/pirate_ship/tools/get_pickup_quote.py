"""Get pickup quote: the price UPS charges for a pickup, before Schedule a Pickup."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._pickups import PICKUP_PROPERTIES, pickup_request

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": PICKUP_PROPERTIES,
    "required": ["carrier", "package_count", "total_weight_oz"],
    "additionalProperties": False,
}


@tool(
    name="get_pickup_quote",
    title="Get pickup quote",
    access="read",
    confirm=False,
    description="What a USPS or UPS pickup would cost; USPS pickups are free. Nothing is booked.",
    details=(
        "Prices one pickup without booking it. USPS collects for free on the next delivery day. UPS charges "
        "per pickup and needs a date and a ready and close time; surcharges are listed apart."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /pickups/quote",
    example_response={
        "carrier": "ups",
        "price_usd": 4.75,
        "base_price_usd": 4.75,
        "retail_usd": None,
        "surcharges": [],
    },
)
async def get_pickup_quote(ctx: ToolContext, args: dict[str, Any]) -> Any:
    if args["carrier"] == "usps":
        return {"carrier": "usps", "price_usd": 0, "base_price_usd": 0, "retail_usd": None, "surcharges": []}
    request = await pickup_request(ctx, args)
    rate = (await graphql(ctx, "RatePickupMutation", {"pickupRequest": request}))["data"]["ratePickup"]
    return {
        "carrier": "ups",
        "price_usd": rate.get("totalPrice"),
        "base_price_usd": rate.get("basePrice"),
        "retail_usd": rate.get("crossedOutTotalPrice"),
        "surcharges": [
            {"name": item.get("name"), "price_usd": item.get("price")} for item in rate.get("surcharges") or []
        ],
    }
