"""List shipments: Pirate Ship's Reports, Shipments table (ShipmentReportGridRowsQuery)."""

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
    values_schema,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

FIELDS = {
    "id": "shipment_id",
    "batch_id": "batch_id",
    "label_transaction_date_time": "created_at",
    "full_name": "recipient",
    "company": "company",
    "email": "email",
    "phone": "phone",
    "address1": "address1",
    "address2": "address2",
    "city": "city",
    "region_id": "state",
    "postcode": "zip",
    "country_id": "country",
    "tracking_nr": "tracking_number",
    "client_price": "cost_usd",
    "status": "status",
    "tracking_status": "tracking_status",
    "tracking_info": "tracking_info",
    "tracking_date": "tracking_date",
    "estimated_delivery_time": "estimated_delivery",
    "carrier_title": "carrier",
    "mailclass_title": "service",
    "package_type_title": "package_type",
    "preset_title": "saved_package",
    "weight": "weight_oz",
    "dimension_x": "length_in",
    "dimension_y": "width_in",
    "dimension_z": "height_in",
    "zone": "zone",
    "insured_value": "insured_value_usd",
    "insured_value_type": "insurance_type",
    "labeling_artifact_type": "type",
    "label_size": "label_size",
    "batch_title": "batch",
    "warehouse_title": "ship_from",
    "postmark_date": "ship_date",
    "foreign_order_id": "order_id",
    "order_value": "order_value_usd",
    "rubber_stamp1": "rubber_stamp1",
    "rubber_stamp2": "rubber_stamp2",
    "rubber_stamp3": "rubber_stamp3",
}
LISTS = {"status": "status", "tracking_status": "tracking_status", "carrier": "carrier_title", "batch": "batch_title"}
DATE_FIELD = "label_transaction_date_time"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **PAGING_SCHEMA,
        **DATE_SCHEMA,
        "status": values_schema("Label status as the report shows it, e.g. Printed, Refunded."),
        "tracking_status": values_schema("Tracking status as the report shows it, e.g. Delivered, In Transit."),
        "carrier": values_schema("USPS or UPS."),
        "batch": values_schema("Batch titles."),
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total": 1,
    "shipments": [
        {
            "shipment_id": "1234567890",
            "batch_id": "632500000",
            "created_at": "2026-10-16T14:02:11-04:00",
            "recipient": "Linda Morales",
            "company": "",
            "email": "linda@example.com",
            "phone": "",
            "address1": "350 5th Ave",
            "address2": "",
            "city": "New York",
            "state": "NY",
            "zip": "10118",
            "country": "US",
            "tracking_number": "9400100000000000000000",
            "cost_usd": 6.86,
            "status": "Printed",
            "tracking_status": "In Transit",
            "tracking_info": "Arrived at USPS Regional Facility",
            "tracking_date": "2026-10-17T08:15:00-04:00",
            "estimated_delivery": "Tuesday 10/20",
            "carrier": "USPS",
            "service": "Ground Advantage",
            "package_type": "Box or Rigid Packaging",
            "saved_package": "Small box",
            "weight_oz": 20,
            "length_in": 10,
            "width_in": 8,
            "height_in": 4,
            "zone": "4",
            "insured_value_usd": 0,
            "insurance_type": None,
            "type": "Label",
            "label_size": "4x6",
            "batch": "Single Label",
            "ship_from": "Main warehouse",
            "ship_date": "2026-10-16",
            "order_id": None,
            "order_value_usd": None,
            "rubber_stamp1": "",
            "rubber_stamp2": "",
            "rubber_stamp3": "",
        }
    ],
}


@tool(
    name="list_shipments",
    title="List shipments",
    access="read",
    confirm=False,
    description="Labels bought in Pirate Ship with recipient, tracking, cost and status, newest first.",
    details=(
        "The Reports, Shipments table: every label the account bought, with the recipient's address, carrier "
        "and service, tracking number and status, cost in US dollars, package size and weight, batch and "
        "ship-from address. search works like the table's search box (name, email, tracking number, order "
        "id). from_date and to_date narrow by the day the label was created; status, tracking_status, "
        "carrier and batch take the values the table shows. total counts every match, limit and offset page "
        "through them."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /shipments",
    example_response=EXAMPLE_RESPONSE,
)
async def list_shipments(ctx: ToolContext, args: dict[str, Any]) -> Any:
    result = await grid_rows(
        ctx,
        "ShipmentReportGridRowsQuery",
        "shipmentReport",
        args,
        filters=report_filters(ctx, args, DATE_FIELD, LISTS),
        sorting=report_sorting(args, DATE_FIELD),
    )
    return {"total": result["total"], "shipments": renamed(result["rows"], FIELDS)}
