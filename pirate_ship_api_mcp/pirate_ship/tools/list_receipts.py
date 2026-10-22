"""List receipts: Pirate Ship's Reports, Receipts table (ReceiptsReportGridRowsQuery)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.grids import (
    DATE_SCHEMA,
    PAGING_SCHEMA,
    grid_rows,
    renamed,
    report_filters,
    report_sorting,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

FIELDS = {
    "id": "receipt_id",
    "created_at": "created_at",
    "payment_status": "status",
    "title": "description",
    "payment_total": "total_usd",
}
LISTS = {"status": "payment_status"}
DATE_FIELD = "created_at"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **PAGING_SCHEMA,
        **DATE_SCHEMA,
        "status": {
            "type": "array",
            "items": {"type": "string", "maxLength": 100},
            "maxItems": 20,
            "description": "Payment status as the table shows it.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total": 1,
    "receipts": [
        {
            "receipt_id": "7712345",
            "created_at": "2026-10-16T14:02:00-04:00",
            "status": "Paid",
            "description": "Visa ending in 4242",
            "total_usd": 20.0,
        }
    ],
}


@tool(
    name="list_receipts",
    title="List receipts",
    access="read",
    confirm=False,
    description="Payments made to Pirate Ship, newest first; get_receipt shows one.",
    details=(
        "The Reports, Receipts table: each payment the account made (card, PayPal, bank) with its status, "
        "description and total in US dollars. Pass receipt_id to get_receipt for the labels it paid for."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /receipts",
    example_response=EXAMPLE_RESPONSE,
)
async def list_receipts(ctx: ToolContext, args: dict[str, Any]) -> Any:
    result = await grid_rows(
        ctx,
        "ReceiptsReportGridRowsQuery",
        "receiptsReport",
        args,
        filters=report_filters(ctx, args, DATE_FIELD, LISTS),
        sorting=report_sorting(args, DATE_FIELD),
    )
    return {"total": result["total"], "receipts": renamed(result["rows"], FIELDS)}
