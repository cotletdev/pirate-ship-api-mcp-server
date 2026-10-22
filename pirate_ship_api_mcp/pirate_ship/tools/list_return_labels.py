"""List return labels: Pirate Ship's Reports, Return Labels table (ReturnLabelsReportGridRowsQuery)."""

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
    "created_at": "created_at",
    "status": "status",
    "full_name": "recipient",
    "company": "company",
    "email": "email",
    "address1": "address1",
    "address2": "address2",
    "city": "city",
    "region_id": "state",
    "postcode": "zip",
    "country_id": "country",
    "client_price": "amount_usd",
}
LISTS = {"status": "status"}
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
            "description": "Return label status as the table shows it.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total": 1,
    "return_labels": [
        {
            "shipment_id": "1234567891",
            "created_at": "2026-10-16T14:05:00-04:00",
            "status": "Unused",
            "recipient": "Karen Smith",
            "company": "",
            "email": "",
            "address1": "100 Main St",
            "address2": "",
            "city": "Charlotte",
            "state": "NC",
            "zip": "28203",
            "country": "US",
            "amount_usd": 0,
        }
    ],
}


@tool(
    name="list_return_labels",
    title="List return labels",
    access="read",
    confirm=False,
    description="Pay-on-use return labels and whether a customer used them.",
    details=(
        "The Reports, Return Labels table: every return label made with a shipment, its status (unused labels"
        " cost nothing), the address it goes back to and what was charged in US dollars when it was used."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /return-labels",
    example_response=EXAMPLE_RESPONSE,
)
async def list_return_labels(ctx: ToolContext, args: dict[str, Any]) -> Any:
    result = await grid_rows(
        ctx,
        "ReturnLabelsReportGridRowsQuery",
        "returnLabelsReport",
        args,
        filters=report_filters(ctx, args, DATE_FIELD, LISTS),
        sorting=report_sorting(args, DATE_FIELD),
    )
    return {"total": result["total"], "return_labels": renamed(result["rows"], FIELDS)}
