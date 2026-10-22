"""List import orders: the Import page's grid of unshipped store orders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.grids import PAGING_SCHEMA, grid_rows

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **PAGING_SCHEMA,
        "ignored": {"type": "boolean", "default": False, "description": "Show the ignored orders instead."},
    },
    "required": [],
    "additionalProperties": False,
}


@tool(
    name="list_import_orders",
    title="List import orders",
    access="read",
    confirm=False,
    description="Unshipped orders from your connected store integrations, as in the Import grid.",
    details=(
        "Orders imported from connected stores that still need a label: one row per order with the grid's "
        "columns (order number, recipient, items, store). ignored true lists the orders you hid with "
        "ignore_orders. Run sync_store_orders first for the newest. Use order ids in create_batch_from_orders."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /import-orders",
    example_response={
        "total": 1,
        "rows": [{"id": "8812004", "order_number": "1042", "full_name": "Linda Morales", "platform": "Etsy"}],
    },
)
async def list_import_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    mode = "IGNORED" if args.get("ignored") else "DEFAULT"
    return await grid_rows(ctx, "ImportedOrdersGridRowsQuery", "importedOrders", args, extra={"gridMode": mode})
