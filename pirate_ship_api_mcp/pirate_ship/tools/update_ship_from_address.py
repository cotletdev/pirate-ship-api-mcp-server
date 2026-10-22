"""Update ship-from address: Settings, Ship From Addresses, Edit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
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
        "address_id": {"type": "string", "minLength": 1, "description": "id from list_ship_from_addresses."},
        "title": {"type": "string", "minLength": 1, "maxLength": 100},
        "origin": ADDRESS_SCHEMA,
        "return_address": {**ADDRESS_SCHEMA, "description": "A separate return address."},
        "origin_is_return": {"type": "boolean", "description": "true sends returns to the origin."},
    },
    "required": ["address_id"],
    "additionalProperties": False,
}


_KEYS = ("fullName", "company", "address1", "address2", "city", "regionCode", "postcode", "phone")


def _as_input(address: dict[str, Any]) -> dict[str, Any]:
    """A saved address sent back unchanged."""
    return {key: address.get(key) or "" for key in _KEYS} | {"countryCode": "US"}


@tool(
    name="update_ship_from_address",
    title="Update ship-from address",
    access="write",
    confirm=False,
    description="Changes a Ship From Address: its name, origin or return address.",
    details=(
        "Edits one saved Ship From Address; fields you leave out keep their values. origin_is_return true "
        "sends returns to the origin, return_address sets a separate one. Pirate Ship saves an edit as a new "
        "version: the answer carries the new id, use it from then on. Labels already bought keep their address."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /ship-from-addresses/{address_id}",
    example_response=EXAMPLE_SHIP_FROM,
)
async def update_ship_from_address(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "WarehousesQuery"))["data"].get("company") or {}
    default_id = (company.get("settings") or {}).get("defaultWarehouseId")
    current = next((item for item in company.get("warehouses") or [] if item["id"] == args["address_id"]), None)
    if current is None:
        raise ToolError("No ship-from address with this id.", ErrorCode.INVALID_INPUT)
    returns = args.get("return_address")
    same = args.get("origin_is_return", False if returns else bool(current.get("useOriginAsReturnAddress")))
    origin = address_input(args["origin"]) if "origin" in args else _as_input(current["originAddress"])
    if same:
        return_input = None
    elif returns:
        return_input = address_input(returns)
    else:
        return_input = _as_input(current.get("returnAddress") or current["originAddress"])
    variables = {
        "id": current["id"],
        "title": args.get("title", current.get("title")),
        "useOriginAsReturnAddress": same,
        "originAddress": origin,
        "returnAddress": return_input,
    }
    updated = (await graphql(ctx, "UpdateWarehouseMutation", variables))["data"]["updateWarehouse"]
    return ship_from_out(updated, default_id)
