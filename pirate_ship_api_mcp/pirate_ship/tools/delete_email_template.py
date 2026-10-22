"""Delete email template: Settings, Tracking Emails, Delete."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"template_id": {"type": "string", "minLength": 1, "description": "id from list_email_templates."}},
    "required": ["template_id"],
    "additionalProperties": False,
}


@tool(
    name="delete_email_template",
    title="Delete email template",
    access="write",
    confirm=False,
    description="Removes a tracking email template.",
    input_schema=INPUT_SCHEMA,
    route="DELETE /email-templates/{template_id}",
    example_response={"deleted": "6800990"},
)
async def delete_email_template(ctx: ToolContext, args: dict[str, Any]) -> Any:
    deleted = (await graphql(ctx, "DeleteMailTemplateMutation", {"id": args["template_id"]}))["data"]
    return {"deleted": (deleted.get("deleteMailTemplate") or {}).get("id", args["template_id"])}
