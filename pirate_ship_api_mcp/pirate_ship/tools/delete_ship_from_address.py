"""Delete ship-from address: Settings, Ship From Addresses, Delete."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
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
    name="delete_ship_from_address",
    title="Delete ship-from address",
    access="write",
    confirm=True,
    description="Removes a saved Ship From Address. The default address cannot be removed.",
    details=(
        "Deletes one Ship From Address from Settings. Labels already bought are not affected. Pirate Ship "
        "keeps at least one address and never deletes the default: make another one the default first."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /ship-from-addresses/{address_id}",
    example_response={"deleted": "18968840"},
)
async def delete_ship_from_address(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "WarehousesQuery"))["data"].get("company") or {}
    if (company.get("settings") or {}).get("defaultWarehouseId") == args["address_id"]:
        raise ToolError(
            "This is the default ship-from address; set another one as default first.", ErrorCode.INVALID_INPUT
        )
    deleted = (await graphql(ctx, "DeleteWarehouseMutation", {"warehouseId": args["address_id"]}))["data"]
    return {"deleted": (deleted.get("deleteWarehouse") or {}).get("id", args["address_id"])}
