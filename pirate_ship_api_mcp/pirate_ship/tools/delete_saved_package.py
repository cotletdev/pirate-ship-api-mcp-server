"""Delete saved package: Settings, Saved Packages, Delete."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"package_id": {"type": "string", "minLength": 1, "description": "id from list_saved_packages."}},
    "required": ["package_id"],
    "additionalProperties": False,
}


@tool(
    name="delete_saved_package",
    title="Delete saved package",
    access="write",
    confirm=False,
    description="Delete a Saved Package (box size and weight preset) from the account.",
    details=(
        "Removes it for good; labels already made with it are not affected. To change its size or weight "
        "instead, use update_saved_package. Returns the deleted package's id."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /saved-packages/{package_id}",
    example_response={"deleted": "518829001"},
)
async def delete_saved_package(ctx: ToolContext, args: dict[str, Any]) -> Any:
    deleted = (await graphql(ctx, "DeleteShipmentPresetMutation", {"id": args["package_id"]}))["data"]
    return {"deleted": (deleted.get("deleteShipmentPreset") or {}).get("id", args["package_id"])}
