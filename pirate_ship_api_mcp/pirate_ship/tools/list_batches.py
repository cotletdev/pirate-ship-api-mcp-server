"""List batches: the Ship page's latest batches, newest first, a page at a time."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"page": {"type": "integer", "minimum": 0, "default": 0, "description": "0 is the newest page."}},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "page": 0,
    "batches": [
        {
            "batch_id": "632575376",
            "title": "Linda Morales",
            "created_at": "2026-10-18T17:52:10+02:00",
            "shipments": 1,
            "step": "RATED",
            "status": "Rated",
            "progress_percent": None,
            "first_tracking_number": None,
            "first_tracking_url": None,
            "counts": {"delivered": 0, "in_transit": 0, "ready_to_print": 0, "refunded": 0, "errors": 0},
        }
    ],
}


@tool(
    name="list_batches",
    title="List batches",
    access="read",
    confirm=False,
    description="Latest batches and single labels, newest first, with status and tracking counts.",
    details=(
        "The batches on Pirate Ship's Ship page, newest first: drafts (RATED), bought (BILLED) and refunded, "
        "each with its shipment count, status text, the first shipment's tracking number and how many "
        "shipments are delivered, in transit, ready to print, refunded or failed. page 0 is the newest; an "
        "empty list means no more pages. get_batch gives one in full."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /batches",
    example_response=EXAMPLE_RESPONSE,
)
async def list_batches(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page = args.get("page", 0)
    data = (await graphql(ctx, "LatestBatchesQuery", {"pageIndex": page}))["data"]
    batches = []
    for item in (data.get("latestBatches") or {}).get("batches") or []:
        counts = item.get("shipmentStatusSummary") or {}
        first = (item.get("shipments") or [{}])[0] or {}
        batches.append(
            {
                "batch_id": item.get("id"),
                "title": item.get("title"),
                "created_at": item.get("createdAt"),
                "shipments": item.get("numShipments"),
                "step": item.get("step"),
                "status": item.get("statusText"),
                "progress_percent": (item.get("runningProcess") or {}).get("progressPercentage"),
                "first_tracking_number": first.get("trackingNr"),
                "first_tracking_url": first.get("trackingLink"),
                "counts": {
                    "delivered": counts.get("deliveredCount", 0),
                    "in_transit": counts.get("inTransitCount", 0),
                    "ready_to_print": counts.get("readyToPrintCount", 0),
                    "refunded": counts.get("refundedCount", 0),
                    "errors": counts.get("errorCount", 0),
                },
            }
        )
    return {"page": page, "batches": batches}
