"""List ship-from addresses: Settings, Ship From Addresses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import EXAMPLE_SHIP_FROM, ship_from_out

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


@tool(
    name="list_ship_from_addresses",
    title="List ship-from addresses",
    access="read",
    confirm=False,
    description="Your Ship From Addresses with their return addresses; one is the default.",
    details=(
        "Every saved Ship From Address in Pirate Ship: where labels ship from and the return address printed "
        "on them (origin_is_return when they are the same). default marks the one new shipments and rate "
        "quotes start from. Use an id in update_ship_from_address, delete_ship_from_address or "
        "set_default_ship_from_address."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /ship-from-addresses",
    example_response={"addresses": [EXAMPLE_SHIP_FROM]},
)
async def list_ship_from_addresses(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "WarehousesQuery"))["data"].get("company") or {}
    default_id = (company.get("settings") or {}).get("defaultWarehouseId")
    warehouses = [item for item in company.get("warehouses") or [] if not item.get("shy")]
    return {"addresses": [ship_from_out(item, default_id) for item in warehouses]}
