"""Create saved package: Settings, Saved Packages, Add."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import (
    EXAMPLE_PACKAGE,
    PACKAGE_PROPERTIES,
    package_input,
    package_out,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": PACKAGE_PROPERTIES,
    "required": ["title", "packaging"],
    "additionalProperties": False,
}


@tool(
    name="create_saved_package",
    title="Create saved package",
    access="write",
    confirm=False,
    description="Saves a package (type, size, weight, extra services) for reuse on labels.",
    details=(
        "Adds a Saved Package in Settings. Parcel, SoftEnvelope and Irregular need length_in and width_in, a "
        "box also height_in; flat rate packaging needs none. weight_oz 0 leaves the weight to each label. "
        "default true preselects it on new shipments."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /saved-packages",
    example_response=EXAMPLE_PACKAGE,
)
async def create_saved_package(ctx: ToolContext, args: dict[str, Any]) -> Any:
    variables = {"default": args.get("default", False), "shipmentPreset": package_input(args)}
    created = (await graphql(ctx, "CreateShipmentPresetMutation", variables))["data"]["createShipmentPreset"]
    preset = created["shipmentPreset"]
    return package_out(preset, preset["id"] if created.get("default") else None)
