"""Update saved package: Settings, Saved Packages, Edit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import (
    EXAMPLE_PACKAGE,
    PACKAGE_PROPERTIES,
    package_input,
    package_out,
)
from pirate_ship_api_mcp.pirate_ship.tools.list_saved_packages import saved_packages

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "package_id": {"type": "string", "minLength": 1, "description": "id from list_saved_packages."},
        **PACKAGE_PROPERTIES,
    },
    "required": ["package_id"],
    "additionalProperties": False,
}


@tool(
    name="update_saved_package",
    title="Update saved package",
    access="write",
    confirm=False,
    description="Changes a Saved Package; fields you leave out keep their values.",
    details=(
        "Edits one Saved Package: name, packaging, size, weight, signature, insurance, return label and flags. "
        "Pirate Ship saves an edit as a new version: the answer carries the new id, use it from then on. "
        "default true makes it the preselected package."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /saved-packages/{package_id}",
    example_response=EXAMPLE_PACKAGE,
)
async def update_saved_package(ctx: ToolContext, args: dict[str, Any]) -> Any:
    presets, default_id = await saved_packages(ctx)
    current = next((item for item in presets if item["id"] == args["package_id"]), None)
    if current is None:
        raise ToolError("No saved package with this id.", ErrorCode.INVALID_INPUT)
    fields = {"id": current["id"], **package_input(args, current)}
    variables = {"default": args.get("default", current["id"] == default_id), "shipmentPreset": fields}
    updated = (await graphql(ctx, "UpdateShipmentPresetMutation", variables))["data"]["updateShipmentPreset"]
    preset = updated["shipmentPreset"]
    return package_out(preset, preset["id"] if updated.get("default") else None)
