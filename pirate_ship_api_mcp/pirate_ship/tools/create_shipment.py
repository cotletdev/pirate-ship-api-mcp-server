"""Create shipment: the Single Shipment form up to "Get Rates", an unpaid draft batch with its rates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import (
    ADDRESS_SCHEMA,
    PACKAGE_SCHEMA,
    address,
    mutate,
    package_for,
    refusal,
    settled_batch,
    summary,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "to": ADDRESS_SCHEMA,
        **PACKAGE_SCHEMA,
        "rubber_stamp_1": {"type": "string", "maxLength": 50, "description": "Extra text printed on the label."},
        "rubber_stamp_2": {"type": "string", "maxLength": 50},
        "address_correction": {
            "type": "string",
            "enum": ["ask", "accept", "skip"],
            "default": "ask",
            "description": (
                "When Pirate Ship suggests a corrected address: ask returns the suggestion without a draft, "
                "accept ships to the suggestion, skip keeps the address as given."
            ),
        },
    },
    "required": ["to"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "status": "rated",
    "batch_id": "632575376",
    "title": "Linda Morales",
    "step": "Rated",
    "ship_date": "2026-10-19",
    "shipment_count": 1,
    "ship_from": {"full_name": "Jane Doe", "city": "Charlotte", "state": "NC", "zip": "28203-4239", "country": "US"},
    "package": {"type": "Box or Rigid Packaging", "dimensions": '10x8x4"', "weight_oz": 20, "insured_usd": 0},
    "shipments": [{"shipment_id": "799699258", "recipient": {"full_name": "Linda Morales", "city": "New York"}}],
    "rates": [
        {
            "rate_id": "domestic_big_or_heavy_business:3-1-0",
            "group": "domestic_big_or_heavy_business",
            "carrier": "USPS",
            "service": "Ground Advantage",
            "price_usd": 7.12,
            "retail_usd": 13.5,
            "delivery": "Estimated delivery Thursday 10/22 by 6:00 PM if shipped on 10/19",
            "ship_dates": ["2026-10-19", "2026-10-20"],
            "cheapest": True,
        }
    ],
}


@tool(
    name="create_shipment",
    title="Create shipment",
    access="write",
    confirm=False,
    description="Unpaid draft label for one package with every rate; buy it with buy_label.",
    details=(
        "Pirate Ship's Single Shipment form up to Get Rates: makes a draft batch for one package from your "
        "ship-from address to the recipient and returns its rates (USPS and UPS services with your price, "
        "retail price, estimated delivery, possible ship dates). Nothing is charged; buy_label buys one of "
        "the rates, delete_batch drops the draft. Give the package as packaging, weight_oz and size, or "
        "package_preset_id of a saved package. When Pirate Ship suggests a corrected address and "
        "address_correction is ask, the answer is status address_correction with the suggestion and no draft: "
        "call again with accept or skip."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /shipments",
    example_response=EXAMPLE_RESPONSE,
)
async def create_shipment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    warehouse, preset_ref = await package_for(ctx, args)
    to = args["to"]
    variables = {
        "warehouseId": warehouse["id"],
        "shipmentPresetId": preset_ref,
        "shipToAddress": {
            "email": to.get("email", ""),
            "phone": to.get("phone", ""),
            "fullName": to["full_name"],
            "company": to.get("company", ""),
            "address1": to["address1"],
            "address2": to.get("address2", ""),
            "city": to["city"],
            "regionCode": to.get("state", ""),
            "postcode": to["zip"],
            "countryCode": to.get("country", "US"),
        },
        "rubberStamps": {
            "rubberStamp1": args.get("rubber_stamp_1", ""),
            "rubberStamp2": args.get("rubber_stamp_2", ""),
        },
        "skipCorrection": args.get("address_correction") == "skip",
        "validatedAddressId": None,
    }
    answer = await mutate(ctx, "CreateBatchFromSingleShipmentMutation", variables)
    created = answer["data"].get("createBatchFromSingleShipment")
    if not created:
        correction = next(
            (
                (item.get("extensions") or {}).get("addressCorrection")
                for item in answer["errors"]
                if (item.get("extensions") or {}).get("failureReason") == "address_correction_available"
            ),
            None,
        )
        if correction is None:
            raise refusal(answer["errors"], "Pirate Ship did not create the shipment.")
        if args.get("address_correction", "ask") == "ask":
            return {
                "status": "address_correction",
                "suggested_address": address(correction.get("address")),
                "reasons": correction.get("correctionReasons") or [],
                "missing_information": bool(correction.get("hasMissingInformation")),
            }
        variables["validatedAddressId"] = (correction.get("address") or {}).get("id")
        answer = await mutate(ctx, "CreateBatchFromSingleShipmentMutation", variables)
        created = answer["data"].get("createBatchFromSingleShipment")
        if not created:
            raise refusal(answer["errors"], "Pirate Ship did not create the shipment.")
    batch = (await settled_batch(ctx, created["id"]))["batch"]
    return {"status": "rated", **summary(batch)}
