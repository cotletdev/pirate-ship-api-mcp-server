"""Create SCAN form: End of Day, Create SCAN Form, for a Ship Date or for one batch."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ship_date": {"type": "string", "format": "date", "description": "Labels of this Ship Date. Default: today."},
        "batch_id": {"type": "string", "description": "Only the labels of this batch (ignores ship_date)."},
        "from_address_id": {
            "type": "string",
            "description": "Ship From Address, when you ship from more than one. Default: the default one.",
        },
    },
    "required": [],
    "additionalProperties": False,
}


@tool(
    name="create_scan_form",
    title="Create SCAN Form",
    access="write",
    confirm=False,
    description="USPS End of Day SCAN Form for the labels of one Ship Date, as a PDF link.",
    details=(
        "Puts the USPS labels of one Ship Date and Ship From Address (or of one batch) that have no SCAN Form "
        "yet on a new SCAN Form and returns its PDF link. The carrier scans that one sheet instead of every "
        "package. No labels without a form: Pirate Ship answers with an error."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /scan-forms",
    example_response={
        "id": "77120",
        "ship_date": "2026-10-19",
        "labels": 5,
        "url": "https://ship.pirateship.com/scanform/77120.pdf",
    },
)
async def create_scan_form(ctx: ToolContext, args: dict[str, Any]) -> Any:
    if batch := args.get("batch_id"):
        form = (await graphql(ctx, "CreateScanFormByBatchMutation", {"batchId": batch}))["data"]
        made = form.get("createScanFormByBatch") or {}
        if not made.get("scanFormUrl"):
            raise ToolError("This batch has no labels for a SCAN Form.", ErrorCode.TARGET_ERROR)
        return {"id": made.get("id"), "ship_date": None, "labels": None, "url": made.get("scanFormUrl")}
    company = (await graphql(ctx, "ScanFormsQuery"))["data"].get("company") or {}
    warehouse = args.get("from_address_id") or (company.get("settings") or {}).get("defaultWarehouseId")
    ready = {item["id"]: item.get("totalAvailableLabelsForScanForm", 0) for item in company.get("warehouses") or []}
    if not ready.get(warehouse):
        raise ToolError("No USPS labels without a SCAN Form at this ship-from address.", ErrorCode.TARGET_ERROR)
    day = args.get("ship_date") or datetime.now(ZoneInfo(ctx.profile.timezone)).date().isoformat()
    made = (await graphql(ctx, "CreateScanFormMutation", {"warehouseId": warehouse, "shipDate": day}))["data"]
    form = made.get("createScanForm") or {}
    return {
        "id": form.get("id"),
        "ship_date": form.get("shipDate"),
        "labels": form.get("shipmentCount", 0),
        "url": form.get("url"),
    }
