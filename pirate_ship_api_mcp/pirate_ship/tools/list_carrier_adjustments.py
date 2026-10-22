"""List carrier adjustments: Pirate Ship's Reports, Carrier Adjustments table (CarrierAdjustmentReportGridRowsQuery)."""

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
    "id": "adjustment_id",
    "shipment_id": "shipment_id",
    "batch_id": "batch_id",
    "reconciliation_adjustment_created_at": "created_at",
    "adjustment_status": "status",
    "disputed_at": "disputed_at",
    "dispute_processed_at": "dispute_processed_at",
    "postmark_date": "ship_date",
    "tracking_nr": "tracking_number",
    "batch_title": "batch",
    "full_name": "recipient",
    "reason": "reason",
    "carrier_title": "carrier",
    "zone": "old_zone",
    "new_zone": "new_zone",
    "old_to_zip": "old_to_zip",
    "actual_to_zip": "actual_to_zip",
    "old_from_zip": "old_from_zip",
    "actual_from_zip": "actual_from_zip",
    "old_dimension_x": "old_length_in",
    "old_dimension_y": "old_width_in",
    "old_dimension_z": "old_height_in",
    "actual_dimension_x": "actual_length_in",
    "actual_dimension_y": "actual_width_in",
    "actual_dimension_z": "actual_height_in",
    "old_package_type": "old_package_type",
    "actual_package": "actual_package_type",
    "old_weight": "old_weight_oz",
    "actual_weight": "actual_weight_oz",
    "old_service_key": "old_service",
    "actual_service": "actual_service",
    "client_price_original": "old_cost_usd",
    "client_price": "actual_cost_usd",
    "carrier_adjustment": "adjustment_usd",
}
LISTS = {"status": "adjustment_status", "carrier": "carrier_title"}
DATE_FIELD = "reconciliation_adjustment_created_at"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **PAGING_SCHEMA,
        **DATE_SCHEMA,
        "status": {
            "type": "array",
            "items": {"type": "string", "maxLength": 100},
            "maxItems": 20,
            "description": "Adjustment status as the table shows it.",
        },
        "carrier": {
            "type": "array",
            "items": {"type": "string", "maxLength": 100},
            "maxItems": 20,
            "description": "USPS or UPS.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total": 1,
    "adjustments": [
        {
            "adjustment_id": "5512",
            "shipment_id": "1234567890",
            "batch_id": "632500000",
            "created_at": "2026-10-17T10:00:00-04:00",
            "status": "Charged",
            "disputed_at": None,
            "dispute_processed_at": None,
            "ship_date": "2026-10-12",
            "tracking_number": "9400100000000000000000",
            "batch": "Single Label",
            "recipient": "Linda Morales",
            "reason": "Weight",
            "carrier": "USPS",
            "old_zone": "4",
            "new_zone": "4",
            "old_to_zip": "10118",
            "actual_to_zip": "10118",
            "old_from_zip": "28203",
            "actual_from_zip": "28203",
            "old_length_in": 10,
            "old_width_in": 8,
            "old_height_in": 4,
            "actual_length_in": 10,
            "actual_width_in": 8,
            "actual_height_in": 4,
            "old_package_type": "Parcel",
            "actual_package_type": "Parcel",
            "old_weight_oz": 20,
            "actual_weight_oz": 36,
            "old_service": "GroundAdvantage",
            "actual_service": "Ground Advantage",
            "old_cost_usd": 6.86,
            "actual_cost_usd": 8.12,
            "adjustment_usd": 1.26,
        }
    ],
}


@tool(
    name="list_carrier_adjustments",
    title="List carrier adjustments",
    access="read",
    confirm=False,
    description="Extra charges or credits the carrier made after a label was used, with old and actual package.",
    details=(
        "The Reports, Carrier Adjustments table: when USPS or UPS measured a package differently from the "
        "label (weight, size, package type, zone, ZIP), the old and actual values, the old and new cost and "
        "the adjustment in US dollars, and whether it was disputed. dispute_adjustment disputes one by "
        "shipment_id."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /carrier-adjustments",
    example_response=EXAMPLE_RESPONSE,
)
async def list_carrier_adjustments(ctx: ToolContext, args: dict[str, Any]) -> Any:
    result = await grid_rows(
        ctx,
        "CarrierAdjustmentReportGridRowsQuery",
        "carrierAdjustmentReport",
        args,
        filters=report_filters(ctx, args, DATE_FIELD, LISTS),
        sorting=report_sorting(args, DATE_FIELD),
    )
    return {"total": result["total"], "adjustments": renamed(result["rows"], FIELDS)}
