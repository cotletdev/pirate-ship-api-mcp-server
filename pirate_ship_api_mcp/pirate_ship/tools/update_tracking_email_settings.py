"""Update tracking email settings: Settings, Tracking Emails, the default switch and Default Email Delay."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools.get_tracking_email_settings import (
    DELAYS,
    EXAMPLE_RESPONSE,
    tracking_settings,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "enabled": {"type": "boolean", "description": "Send tracking emails on new labels by default."},
        "delay": {
            "type": "string",
            "enum": list(DELAYS),
            "description": "When the email goes out after purchase; +24 hours is next day 9:00 AM.",
        },
    },
    "required": [],
    "additionalProperties": False,
}


@tool(
    name="update_tracking_email_settings",
    title="Update tracking email settings",
    access="write",
    confirm=False,
    description="Turns default tracking emails on or off and sets their delay after purchase.",
    details="Changes only what you pass and returns the settings as get_tracking_email_settings does.",
    input_schema=INPUT_SCHEMA,
    route="PATCH /tracking-email-settings",
    example_response=EXAMPLE_RESPONSE,
)
async def update_tracking_email_settings(ctx: ToolContext, args: dict[str, Any]) -> Any:
    if "enabled" not in args and "delay" not in args:
        raise ToolError("Pass enabled, delay or both.", ErrorCode.INVALID_INPUT)
    if "enabled" in args:
        await graphql(ctx, "UpdateDefaultTrackingEmailsEnabled", {"enabled": args["enabled"]})
    if "delay" in args:
        await graphql(ctx, "UpdateDefaultTrackingEmailsDelay", {"inAdvance": args["delay"]})
    return await tracking_settings(ctx)
