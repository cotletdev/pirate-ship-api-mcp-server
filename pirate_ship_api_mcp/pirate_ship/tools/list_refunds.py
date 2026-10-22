"""List refunds: Pirate Ship's Reports, Refunds table (RefundReportGridRowsQuery)."""

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
    "id": "shipment_id",
    "refund_requested_at": "requested_at",
    "refund_approved_at": "approved_at",
    "refund_declined_at": "declined_at",
    "refund_reversed_at": "reversed_at",
    "status": "status",
    "tracking_nr": "tracking_number",
    "full_name": "recipient",
    "company": "company",
    "email": "email",
    "city": "city",
    "region_id": "state",
    "postcode": "zip",
    "country_id": "country",
    "client_price": "amount_usd",
    "was_auto_refunded": "auto_refund",
}
LISTS = {"status": "status"}
DATE_FIELD = "refund_requested_at"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **PAGING_SCHEMA,
        **DATE_SCHEMA,
        "status": {
            "type": "array",
            "items": {"type": "string", "maxLength": 100},
            "maxItems": 20,
            "description": "Refund status as the table shows it, e.g. Pending, Approved, Declined.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total": 1,
    "refunds": [
        {
            "shipment_id": "1234567890",
            "requested_at": "2026-10-16T15:00:00-04:00",
            "approved_at": None,
            "declined_at": None,
            "reversed_at": None,
            "status": "Pending",
            "tracking_number": "9400100000000000000000",
            "recipient": "Linda Morales",
            "company": "",
            "email": "linda@example.com",
            "city": "New York",
            "state": "NY",
            "zip": "10118",
            "country": "US",
            "amount_usd": 6.86,
            "auto_refund": False,
        }
    ],
}


@tool(
    name="list_refunds",
    title="List refunds",
    access="read",
    confirm=False,
    description="Label refunds with their status and amount, newest request first.",
    details=(
        "The Reports, Refunds table: every label refund the account asked for (or Pirate Ship made "
        "automatically for an unused label), when it was requested, approved, declined or reversed, the "
        "tracking number, recipient and amount in US dollars. from_date and to_date narrow by the request "
        "day."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /refunds",
    example_response=EXAMPLE_RESPONSE,
)
async def list_refunds(ctx: ToolContext, args: dict[str, Any]) -> Any:
    result = await grid_rows(
        ctx,
        "RefundReportGridRowsQuery",
        "refundReport",
        args,
        filters=report_filters(ctx, args, DATE_FIELD, LISTS),
        sorting=report_sorting(args, DATE_FIELD),
    )
    return {"total": result["total"], "refunds": renamed(result["rows"], FIELDS)}
