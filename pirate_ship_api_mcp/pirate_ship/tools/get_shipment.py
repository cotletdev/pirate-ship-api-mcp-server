"""Get shipment: one label's page in Pirate Ship: recipient, service, cost, tracking, adjustments."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import address
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "shipment_id": {"type": "string", "minLength": 1, "description": "From get_batch or list_shipments."},
        "batch_id": {"type": "string", "description": "Saves one request when known."},
    },
    "required": ["shipment_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "shipment_id": "799699258",
    "batch_id": "632575376",
    "status": "PRINTABLE",
    "created_at": "2026-10-18T15:48:19+00:00",
    "carrier": "USPS",
    "service": "Ground Advantage",
    "zone": "4",
    "tracking_number": "9400100000000000000000",
    "tracking_url": "https://www.pirateship.com/track/9400100000000000000000",
    "recipient": {"full_name": "Linda Morales", "address1": "350 5th Ave", "city": "New York", "zip": "10118-0110"},
    "package": {"type": "Box or Rigid Packaging", "weight_oz": 20, "dimensions_in": [10, 8, 4]},
    "cost": {"base_usd": 7.12, "total_usd": 7.12, "surcharges": [], "insured_usd": 0},
    "estimated_delivery": "2026-10-22T18:00:00",
    "can_print": True,
    "can_refund": True,
    "order": None,
    "adjustments": [],
    "error": None,
}


@tool(
    name="get_shipment",
    title="Get shipment",
    access="read",
    confirm=False,
    description="One shipment with tracking, service, cost, recipient and carrier adjustments.",
    details=(
        "The shipment page of a Pirate Ship label: status, carrier and service, zone, tracking number and "
        "link, recipient, package, base and total cost with surcharges and insurance in US dollars, estimated "
        "delivery, the store order it came from, whether it can be printed or refunded, and carrier "
        "adjustments (weight or size the carrier corrected, with the price change and dispute state)."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /shipments/{shipment_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_shipment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    shipment_id = str(args["shipment_id"])
    batch_id = args.get("batch_id")
    if not batch_id:
        found = (await graphql(ctx, "BatchIdFromShipmentQuery", {"shipmentId": shipment_id}))["data"].get("shipment")
        batch_id = ((found or {}).get("batch") or {}).get("id")
    if not batch_id:
        raise ToolError("No such shipment in this Pirate Ship account.", ErrorCode.INVALID_INPUT)
    variables = {"batchId": str(batch_id), "shipmentId": shipment_id}
    batch = (await graphql(ctx, "ShipmentDetailsPageQuery", variables))["data"].get("batch") or {}
    item = next(iter(batch.get("shipments") or []), None)
    if item is None:
        raise ToolError("No such shipment in this Pirate Ship account.", ErrorCode.INVALID_INPUT)
    insurance = item.get("insuranceDetails") or {}
    order = item.get("order")
    return {
        "shipment_id": item.get("id"),
        "batch_id": batch.get("id"),
        "status": item.get("status"),
        "created_at": item.get("createdAt"),
        "carrier": item.get("carrierTitle") or None,
        "service": (item.get("mailClass") or {}).get("title"),
        "zone": item.get("zone"),
        "tracking_number": item.get("trackingNr"),
        "tracking_url": item.get("trackingLink") or None,
        "recipient": address(item.get("recipientAddress")),
        "package": {
            "type": (item.get("packageType") or {}).get("title"),
            "weight_oz": item.get("weight"),
            "dimensions_in": [item.get("dimensionX"), item.get("dimensionY"), item.get("dimensionZ")],
        },
        "cost": {
            "base_usd": item.get("baseClientPrice"),
            "total_usd": item.get("totalClientPrice"),
            "surcharges": [
                {"title": extra.get("title"), "price_usd": extra.get("clientPrice")}
                for extra in item.get("surcharges") or []
                if not extra.get("isIgnored")
            ],
            "insured_usd": insurance.get("insuredValue"),
        },
        "estimated_delivery": (item.get("deliveryEstimation") or {}).get("arrivalLocalDateTime"),
        "can_print": bool(item.get("canPrint")),
        "can_refund": bool(item.get("isShipmentRefundable")),
        "order": {
            "order_id": order.get("foreignOrderId"),
            "store": (order.get("platform") or {}).get("title"),
            "url": (order.get("orderLink") or {}).get("url"),
            "items": [
                {"title": line.get("title"), "sku": line.get("sku"), "quantity": line.get("quantity")}
                for line in order.get("orderItems") or []
            ],
        }
        if order
        else None,
        "adjustments": [
            {
                "created_at": extra.get("createdAt"),
                "weight_oz": extra.get("weight"),
                "dimensions_in": [extra.get("dimensionX"), extra.get("dimensionY"), extra.get("dimensionZ")],
                "price_change_usd": extra.get("clientPriceChange"),
                "dispute_status": extra.get("disputeStatus"),
                "disputable": bool(extra.get("isDisputable")),
                "notes": extra.get("notes"),
            }
            for extra in item.get("adjustments") or []
        ],
        "error": item.get("errorMessage") or None,
    }
