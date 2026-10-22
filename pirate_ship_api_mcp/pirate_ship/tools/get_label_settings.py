"""Get label settings: Settings, General."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.tools._labels import EXAMPLE, raw_settings, settings_out

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


@tool(
    name="get_label_settings",
    title="Get label settings",
    access="read",
    confirm=False,
    description="Label size and file format, packing list, logo, QR codes, address correction, export format.",
    details=(
        "The account's Settings, General: the size and file format new labels are made in, whether a packing "
        "list prints with them, the logo on the label, USPS label-free QR codes, what happens when Pirate Ship "
        "finds a better address, and the spreadsheet format of report exports."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /label-settings",
    example_response=EXAMPLE,
)
async def get_label_settings(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return settings_out(await raw_settings(ctx))
