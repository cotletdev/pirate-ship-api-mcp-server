"""Get receipt: one payment from Reports, Receipts, with the transactions it covered (ReceiptQuery)."""

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
        "receipt_id": {"type": "string", "pattern": "^[0-9]+$", "description": "receipt_id from list_receipts."},
    },
    "required": ["receipt_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "receipt_id": "7712345",
    "title": "Visa ending in 4242",
    "status": "Paid",
    "created_at": "2026-10-16T14:02:00-04:00",
    "total_usd": 20.0,
    "refunded_usd": 0,
    "charged": True,
    "successful": True,
    "error": None,
    "start_balance_usd": 0,
    "end_balance_usd": 13.14,
    "billing_address": {
        "name": "Karen Smith",
        "company": "",
        "address1": "100 Main St",
        "address2": "",
        "city": "Charlotte",
        "state": "NC",
        "zip": "28203",
    },
    "transactions": [
        {
            "created_at": "2026-10-16T14:02:11-04:00",
            "type": "Label",
            "title": "USPS Ground Advantage label to Linda Morales",
            "amount_usd": -6.86,
            "balance_usd": 13.14,
            "batch_id": "632500000",
            "shipment_id": "1234567890",
        }
    ],
    "reversals": [],
}


@tool(
    name="get_receipt",
    title="Get receipt",
    access="read",
    confirm=False,
    description="One payment to Pirate Ship with its billing address and the labels it paid for.",
    details=(
        "The receipt page of one payment from list_receipts: title, status, total and refunded amount in US "
        "dollars, the billing address, the balance before and after, every transaction it covered (labels, "
        "refunds, adjustments, with batch_id and shipment_id) and reversals such as chargebacks."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /receipts/{receipt_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_receipt(ctx: ToolContext, args: dict[str, Any]) -> Any:
    try:
        receipt = (await graphql(ctx, "ReceiptQuery", {"id": args["receipt_id"]}))["data"].get("receipt")
    except ToolError as error:
        # An unknown id comes back as data null with PAYMENT_NOT_FOUND and a generic message.
        if "changed its app" in str(error):
            raise
        raise ToolError("Pirate Ship has no receipt with this id.", ErrorCode.INVALID_INPUT) from error
    if not receipt:
        raise ToolError("Pirate Ship has no receipt with this id.", ErrorCode.INVALID_INPUT)
    payment = receipt.get("payment") or {}
    address = receipt.get("billingAddress") or {}
    return {
        "receipt_id": args["receipt_id"],
        "title": payment.get("title"),
        "status": payment.get("status"),
        "created_at": payment.get("createdAt"),
        "total_usd": payment.get("total"),
        "refunded_usd": payment.get("refundTotal"),
        "charged": bool(receipt.get("isCharged")),
        "successful": bool(receipt.get("paymentSuccessful")),
        "error": payment.get("chargeError"),
        "start_balance_usd": receipt.get("startBalance"),
        "end_balance_usd": receipt.get("endBalance"),
        "billing_address": {
            "name": address.get("fullName"),
            "company": address.get("company"),
            "address1": address.get("address1"),
            "address2": address.get("address2"),
            "city": address.get("city"),
            "state": address.get("regionCode"),
            "zip": address.get("postcode"),
        },
        "transactions": [
            {
                "created_at": item.get("createdAt"),
                "type": item.get("transactionType"),
                "title": item.get("title"),
                "amount_usd": item.get("amount"),
                "balance_usd": item.get("balance"),
                "batch_id": item.get("batchId"),
                "shipment_id": item.get("shipmentId"),
            }
            for item in receipt.get("transactions") or []
        ],
        "reversals": [
            {
                "type": (item.get("action") or {}).get("actionType"),
                "new_status": (item.get("action") or {}).get("newPaymentStatus"),
                "created_at": (item.get("action") or {}).get("createdAt"),
                "amount_usd": item.get("amount"),
            }
            for item in receipt.get("reversals") or []
        ],
    }
