"""Update email template: Settings, Tracking Emails, Edit Email Template."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools._settings import EXAMPLE_TEMPLATE, TEMPLATE_PROPERTIES, template_out
from pirate_ship_api_mcp.pirate_ship.tools.list_email_templates import templates

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "template_id": {"type": "string", "minLength": 1, "description": "id from list_email_templates."},
        **TEMPLATE_PROPERTIES,
    },
    "required": ["template_id"],
    "additionalProperties": False,
}


@tool(
    name="update_email_template",
    title="Update email template",
    access="write",
    confirm=False,
    description="Changes a tracking email template; fields you leave out keep their values.",
    details="Edits the name, subject, sender, BCC address, HTML body or default flag of one template.",
    input_schema=INPUT_SCHEMA,
    route="PATCH /email-templates/{template_id}",
    example_response=EXAMPLE_TEMPLATE,
)
async def update_email_template(ctx: ToolContext, args: dict[str, Any]) -> Any:
    current = next((item for item in await templates(ctx) if item["id"] == args["template_id"]), None)
    if current is None:
        raise ToolError("No email template with this id.", ErrorCode.INVALID_INPUT)
    variables = {
        "id": current["id"],
        "title": args.get("name", current.get("name")),
        "asDefault": args.get("default", bool(current.get("asDefault"))),
        "senderEmail": args.get("sender_email", current.get("senderEmail")),
        "senderName": args.get("sender_name", current.get("senderName")),
        "subject": args.get("subject", current.get("subject")),
        "templateHtml": args.get("html", current.get("templateHtml")),
        "bccEmail": args.get("bcc_email", current.get("bccEmail") or ""),
        "sendTemplatePreview": False,
    }
    return template_out((await graphql(ctx, "UpdateMailTemplateMutation", variables))["data"]["updateMailTemplate"])
