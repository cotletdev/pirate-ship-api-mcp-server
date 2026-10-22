"""List saved packages: Settings, Saved Packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import EXAMPLE_PACKAGE, package_out

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


async def saved_packages(ctx: ToolContext) -> tuple[list[dict[str, Any]], str | None]:
    """The account's Saved Packages (raw presets) and the default id; one-off presets of single labels are left out."""
    company = (await graphql(ctx, "ShipmentPresetsQuery"))["data"].get("company") or {}
    default_id = (company.get("settings") or {}).get("defaultShipmentPresetId")
    return [item for item in company.get("shipmentPresets") or [] if not item.get("shy")], default_id


@tool(
    name="list_saved_packages",
    title="List saved packages",
    access="read",
    confirm=False,
    description="Your Saved Packages from Settings: size, weight and the extra services stored with each.",
    details=(
        "Every Saved Package: packaging type, size in inches, weight in ounces (0 when each label sets its "
        "own), signature, insured value, return label setting and flags. default marks the one preselected "
        "on new shipments. Use an id in update_saved_package or delete_saved_package."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /saved-packages",
    example_response={"packages": [EXAMPLE_PACKAGE]},
)
async def list_saved_packages(ctx: ToolContext, args: dict[str, Any]) -> Any:
    presets, default_id = await saved_packages(ctx)
    return {"packages": [package_out(item, default_id) for item in presets]}
