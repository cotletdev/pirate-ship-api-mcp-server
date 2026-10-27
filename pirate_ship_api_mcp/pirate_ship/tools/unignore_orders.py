"""Unignore orders: the Import grid's Unignore action."""

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
    name="unignore_orders",
    title="Unignore orders",
    access="write",
    confirm=False,
    description="Put ignored store orders back on the Import list.",
    details=(
        "Reverses ignore_orders: the orders show in list_import_orders again and create_batch_from_orders can "
        "ship them. Up to 500 order ids per call; ids that are not ignored are skipped. Returns how many orders "
        "came back and their ids."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /import-orders/ignore",
    example_response={"count": 1, "order_ids": ["8812004"]},
)
async def unignore_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    answer = (await graphql(ctx, "UnignoreOrdersMutation", {"ids": args["order_ids"]}))["data"]["unignoreOrders"]
    return {"count": answer.get("count", 0), "order_ids": answer.get("ids") or []}
