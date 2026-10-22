"""Set default ship-from address: Settings, Ship From Addresses, Make Default."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "address_id": {"type": "string", "minLength": 1, "description": "id from list_ship_from_addresses."}
    },
    "required": ["address_id"],
    "additionalProperties": False,
}


@tool(
    name="set_default_ship_from_address",
    title="Set default ship-from address",
    access="write",
    confirm=False,
    description="Makes one Ship From Address the default for new shipments and rate quotes.",
    details="New shipments, get_rates and pickups start from the default Ship From Address.",
    input_schema=INPUT_SCHEMA,
    route="PUT /ship-from-addresses/{address_id}/default",
    example_response={"default": "1000001"},
)
async def set_default_ship_from_address(ctx: ToolContext, args: dict[str, Any]) -> Any:
    await graphql(ctx, "SetDefaultWarehouseMutation", {"id": args["address_id"]})
    return {"default": args["address_id"]}
