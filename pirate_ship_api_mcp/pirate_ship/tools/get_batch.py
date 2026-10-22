"""Get batch: one batch (a single label is a batch of one) with its shipments, rates and label state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import batch_details

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "batch_id": {"type": "string", "minLength": 1, "description": "From create_shipment or list_batches."}
    },
    "required": ["batch_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "batch_id": "632575376",
    "title": "Linda Morales",
    "step": "Rated",
    "process": "IDLE",
    "ship_date": "2026-10-19",
    "shipment_count": 1,
    "ship_from": {"full_name": "Jane Doe", "city": "Charlotte", "state": "NC", "zip": "28203-4239"},
    "package": {"type": "Box or Rigid Packaging", "dimensions": '10x8x4"', "weight_oz": 20},
    "label_format": {"size": "SIZE_4x6", "file": "PDF"},
    "shipments": [
        {
            "shipment_id": "799699258",
            "recipient": {"full_name": "Linda Morales", "city": "New York", "state": "NY", "zip": "10118"},
            "status": "Rated",
            "tracking_number": None,
            "tracking_url": None,
            "can_print": False,
            "can_refund": False,
        }
    ],
    "rates": [{"rate_id": "domestic_big_or_heavy_business:3-1-0", "carrier": "USPS", "price_usd": 7.12}],
    "refundable": False,
    "price_summary": [{"service": "Ground Advantage", "shipments": 1, "total_usd": 7.12}],
}


@tool(
    name="get_batch",
    title="Get batch",
    access="read",
    confirm=False,
    description="A draft or bought batch: shipments, tracking, rates to buy, what can be refunded.",
    details=(
        "One Pirate Ship batch: a single label from create_shipment is a batch of one. A draft (step Rated) "
        "lists every rate the packages qualify for, with rate_id for buy_label. A bought batch (Billed) shows "
        "each shipment's status, tracking number and link, whether its label can be printed or refunded, "
        "and what was paid per service."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /batches/{batch_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_batch(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await batch_details(ctx, args["batch_id"])
