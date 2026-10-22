"""Create email template: Settings, Tracking Emails, Add Email Template."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import EXAMPLE_TEMPLATE, TEMPLATE_PROPERTIES, template_out

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": TEMPLATE_PROPERTIES,
    "required": ["name", "subject", "html", "sender_name", "sender_email"],
    "additionalProperties": False,
}


@tool(
    name="create_email_template",
    title="Create email template",
    access="write",
    confirm=False,
    description="Adds a tracking email template for the emails recipients get with their tracking link.",
    details=(
        "Saves a new tracking email template. Nothing is sent now: Pirate Ship uses the template when a label "
        "is bought with tracking emails on. html takes the placeholders [Recipient First Name], [Ship Date], "
        "[Shipping Service], [Recipient Address] and [Tracking #]."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /email-templates",
    example_response={**EXAMPLE_TEMPLATE, "default": False},
)
async def create_email_template(ctx: ToolContext, args: dict[str, Any]) -> Any:
    variables = {
        "title": args["name"].strip(),
        "asDefault": args.get("default", False),
        "senderEmail": args["sender_email"].strip(),
        "senderName": args["sender_name"].strip(),
        "subject": args["subject"],
        "templateHtml": args["html"],
        "bccEmail": args.get("bcc_email", ""),
    }
    return template_out((await graphql(ctx, "CreateMailTemplateMutation", variables))["data"]["createMailTemplate"])
