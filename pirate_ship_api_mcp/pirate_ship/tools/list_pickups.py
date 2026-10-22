"""List pickups: the Pickups page."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._pickups import EXAMPLE_PICKUP, pickup_out

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


@tool(
    name="list_pickups",
    title="List pickups",
    access="read",
    confirm=False,
    description="Your scheduled and past USPS and UPS pickups with confirmation numbers.",
    details=(
        "Every carrier pickup on the account: carrier, day and time window, status, confirmation number, "
        "package count and weight in ounces, where the driver finds them, the price (USPS is free) and "
        "whether it can still be cancelled with cancel_pickup."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /pickups",
    example_response={"pickups": [EXAMPLE_PICKUP]},
)
async def list_pickups(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "PickupsQuery"))["data"].get("company") or {}
    return {"pickups": [pickup_out(item) for item in company.get("pickups") or []]}
