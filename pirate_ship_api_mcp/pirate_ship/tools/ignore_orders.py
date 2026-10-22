"""Ignore orders: the Import grid's Ignore action."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "order_ids": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
            "maxItems": 500,
            "description": "Order ids from list_import_orders.",
        }
    },
    "required": ["order_ids"],
    "additionalProperties": False,
}


@tool(
    name="ignore_orders",
    title="Ignore orders",
    access="write",
    confirm=False,
    description="Hides store orders from the Import list without shipping them.",
    details="They move to the ignored list (list_import_orders with ignored true); unignore_orders brings them back.",
    input_schema=INPUT_SCHEMA,
    route="POST /import-orders/ignore",
    example_response={"count": 1, "order_ids": ["8812004"]},
)
async def ignore_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    answer = (await graphql(ctx, "IgnoreOrdersMutation", {"ids": args["order_ids"]}))["data"]["ignoreOrders"]
    return {"count": answer.get("count", 0), "order_ids": answer.get("ids") or []}
