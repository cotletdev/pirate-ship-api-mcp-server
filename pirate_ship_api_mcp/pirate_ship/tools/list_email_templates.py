"""List email templates: Settings, Tracking Emails, Email Templates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import EXAMPLE_TEMPLATE, template_out

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


async def templates(ctx: ToolContext) -> list[dict[str, Any]]:
    company = (await graphql(ctx, "MailTemplatesQuery"))["data"].get("company") or {}
    return company.get("mailTemplates") or []


@tool(
    name="list_email_templates",
    title="List email templates",
    access="read",
    confirm=False,
    description="List the templates of the tracking emails sent to label recipients.",
    details=(
        "Returns every template with its id, name, subject, sender name, reply-to email, BCC address and HTML "
        "body with placeholders such as [Tracking #]; default marks the one used for new labels. Use the id in "
        "update_email_template or delete_email_template. Whether emails go out at all and when is in "
        "get_tracking_email_settings."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /email-templates",
    example_response={"templates": [EXAMPLE_TEMPLATE]},
)
async def list_email_templates(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return {"templates": [template_out(item) for item in await templates(ctx)]}
