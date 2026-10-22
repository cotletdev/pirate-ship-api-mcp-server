"""Create ship-from address: Settings, Ship From Addresses, Add."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import (
    ADDRESS_SCHEMA,
    EXAMPLE_SHIP_FROM,
    address_input,
    ship_from_out,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 100, "description": "Name in the address list."},
        "origin": ADDRESS_SCHEMA,
        "return_address": {**ADDRESS_SCHEMA, "description": "Where returns go. Default: the origin."},
    },
    "required": ["title", "origin"],
    "additionalProperties": False,
}


@tool(
    name="create_ship_from_address",
    title="Create ship-from address",
    access="write",
    confirm=False,
    description="Adds a US Ship From Address, optionally with a separate return address.",
    details=(
        "Saves a new Ship From Address in Pirate Ship. Without return_address, returns go to the origin. "
        "Pirate Ship completes the ZIP+4. It does not become the default: call set_default_ship_from_address "
        "for that."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /ship-from-addresses",
    example_response={**EXAMPLE_SHIP_FROM, "default": False},
)
async def create_ship_from_address(ctx: ToolContext, args: dict[str, Any]) -> Any:
    returns = args.get("return_address")
    variables = {
        "title": args["title"].strip(),
        "saveAddressForReuse": True,
        "useOriginAsReturnAddress": returns is None,
        "originAddress": address_input(args["origin"]),
        "returnAddress": address_input(returns) if returns else None,
    }
    created = (await graphql(ctx, "CreateWarehouseMutation", variables))["data"]["createWarehouse"]
    return ship_from_out(created, None)
