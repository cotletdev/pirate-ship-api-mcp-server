"""Create batch from orders: the Import grid's Create Batch with selected orders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
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
        },
        "package_id": {"type": "string", "minLength": 1, "description": "Saved package id from list_saved_packages."},
        "ship_from_id": {"type": "string", "description": "From list_ship_from_addresses. Default: the default one."},
        "title": {"type": "string", "maxLength": 100, "description": "Batch name. Default: today's date."},
        "override_multiple": {
            "type": "boolean",
            "default": False,
            "description": "Use the saved package also for orders with several items.",
        },
    },
    "required": ["order_ids", "package_id"],
    "additionalProperties": False,
}


@tool(
    name="create_batch_from_orders",
    title="Create batch from orders",
    access="write",
    confirm=False,
    description="Turns store orders into a batch of shipments with one saved package; nothing is bought.",
    details=(
        "Creates a Pirate Ship batch from imported orders: recipients come from the orders, size and weight "
        "from the saved package. The batch is rated, not paid: no label is bought. Large batches are built in "
        "the background (progress in the answer)."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /batches/from-orders",
    example_response={
        "batch_id": "632575376",
        "title": "Etsy orders",
        "step": "RATED",
        "status": "IDLE",
        "progress": 100,
    },
)
async def create_batch_from_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    warehouse = args.get("ship_from_id")
    if not warehouse:
        company = (await graphql(ctx, "WarehousesQuery"))["data"].get("company") or {}
        warehouse = (company.get("settings") or {}).get("defaultWarehouseId")
        if not warehouse:
            raise ToolError("Add a ship-from address in Pirate Ship first.", ErrorCode.TARGET_ERROR)
    variables = {
        "orderIds": args["order_ids"],
        "warehouseId": warehouse,
        "shipmentPresetId": args["package_id"],
        "title": args.get("title") or "",
        "overrideMultiple": args.get("override_multiple", False),
    }
    batch = (await graphql(ctx, "CreateBatchFromImportMutation", variables))["data"]["createBatchFromImport"]
    process = batch.get("runningProcess") or {}
    return {
        "batch_id": batch["id"],
        "title": batch.get("title"),
        "step": batch.get("step"),
        "status": batch.get("status"),
        "progress": process.get("progressPercentage", 100),
    }
