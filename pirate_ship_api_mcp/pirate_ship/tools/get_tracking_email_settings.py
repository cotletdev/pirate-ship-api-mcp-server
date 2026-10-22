"""Get tracking email settings: Settings, Tracking Emails, the switches at the top."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

# Pirate Ship's Default Email Delay options, value to label.
DELAYS = {
    "+1 second": "Immediate",
    "+1 hour": "1 hour",
    "+2 hour": "2 hours",
    "+3 hours": "3 hours",
    "+6 hours": "6 hours",
    "+12 hours": "12 hours",
    "+24 hours": "next day, 9:00 AM",
    "+2 days": "+2 days, 9:00 AM",
    "+3 days": "+3 days, 9:00 AM",
    "+4 days": "+4 days, 9:00 AM",
    "+5 days": "+5 days, 9:00 AM",
    "+6 days": "+6 days, 9:00 AM",
    "+7 days": "+7 days, 9:00 AM",
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "enabled": True,
    "delay": "+1 hour",
    "delay_label": "1 hour",
    "branding": True,
    "default_template_id": "6800981",
}


async def tracking_settings(ctx: ToolContext) -> dict[str, Any]:
    switches = (await graphql(ctx, "TrackingEmailsPageSettingsQuery"))["data"]["company"]["settings"]
    templates = (await graphql(ctx, "MailTemplatesQuery"))["data"]["company"]["settings"]
    delay = templates.get("defaultTrackingEmailsDelay")
    return {
        "enabled": bool(switches.get("defaultTrackingEmailsEnabled")),
        "delay": delay,
        "delay_label": DELAYS.get(delay, delay),
        "branding": bool(switches.get("trackingEmailBrandingEnabled")),
        "default_template_id": templates.get("defaultEmailTemplateId"),
    }


@tool(
    name="get_tracking_email_settings",
    title="Get tracking email settings",
    access="read",
    confirm=False,
    description="Whether recipients get tracking emails by default, how long after purchase, and the template.",
    details=(
        "enabled: new labels send a tracking email to the recipient by default. delay: when it goes out after "
        "the label is bought (delay_label as Pirate Ship shows it). branding: Pirate Ship's branding in the "
        "email. default_template_id: the template from list_email_templates used."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /tracking-email-settings",
    example_response=EXAMPLE_RESPONSE,
)
async def get_tracking_email_settings(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await tracking_settings(ctx)
