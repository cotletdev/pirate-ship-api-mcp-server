"""Pickup requests as the Schedule a Pickup page builds them (PickupRoutes chunk, recorded 18.10.2026).

USPS collects for free on the next delivery day: no date or times, the charge is 0. UPS charges per pickup
(get_pickup_quote) and takes a date with a ready and close time. Weight goes in ounces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

LOCATIONS = ["FRONT_DOOR", "BACK_DOOR", "SIDE_DOOR", "MAIL_ROOM", "OFFICE", "RECEPTION", "OTHER"]

PICKUP_PROPERTIES: dict[str, Any] = {
    "carrier": {"type": "string", "enum": ["usps", "ups"]},
    "date": {"type": "string", "format": "date", "description": "UPS only: pickup day. USPS comes next delivery day."},
    "ready_time": {
        "type": "string",
        "pattern": "^[0-2][0-9]:[0-5][0-9]$",
        "default": "09:00",
        "description": "UPS only.",
    },
    "close_time": {
        "type": "string",
        "pattern": "^[0-2][0-9]:[0-5][0-9]$",
        "default": "17:00",
        "description": "UPS only.",
    },
    "package_count": {"type": "integer", "minimum": 1, "maximum": 500},
    "total_weight_oz": {"type": "number", "exclusiveMinimum": 0, "maximum": 100000},
    "location": {"type": "string", "enum": LOCATIONS, "default": "FRONT_DOOR"},
    "instructions": {"type": "string", "maxLength": 200, "description": "Where to find the packages, with OTHER."},
    "ship_from_id": {"type": "string", "description": "From list_ship_from_addresses. Default: the default one."},
    "overweight": {"type": "boolean", "default": False, "description": "UPS: a package over 70 lb."},
}


async def pickup_request(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    warehouse = args.get("ship_from_id")
    if not warehouse:
        company = (await graphql(ctx, "WarehousesQuery"))["data"].get("company") or {}
        warehouse = (company.get("settings") or {}).get("defaultWarehouseId")
    location = args.get("location", "FRONT_DOOR")
    request = {
        "carrierKey": args["carrier"],
        "warehouseId": warehouse,
        "packageLocation": location,
        "specialInstructions": args.get("instructions", "") if location == "OTHER" else "",
        "frequency": "ONE_TIME",
        "totalPackageCount": args["package_count"],
        "totalPackageWeight": args["total_weight_oz"],
    }
    if args["carrier"] == "usps":
        return request | {"oneTimePickupDate": None, "warehouseReadyTime": "00:00", "warehouseCloseTime": "00:00"}
    if not args.get("date"):
        raise ToolError("A UPS pickup needs a date.", ErrorCode.INVALID_INPUT)
    return request | {
        "oneTimePickupDate": args["date"],
        "warehouseReadyTime": args.get("ready_time", "09:00"),
        "warehouseCloseTime": args.get("close_time", "17:00"),
        "hasUpsOverweightPackages": args.get("overweight", False),
    }


def pickup_out(item: dict[str, Any]) -> dict[str, Any]:
    warehouse = item.get("warehouse") or {}
    origin = warehouse.get("originAddress") or {}
    return {
        "id": item.get("id"),
        "carrier": (item.get("carrier") or {}).get("carrierKey"),
        "date": item.get("oneTimePickupDate"),
        "ready_time": item.get("warehouseReadyTime"),
        "close_time": item.get("warehouseCloseTime"),
        "status": item.get("status"),
        "confirmation_number": item.get("confirmationNumber"),
        "package_count": item.get("totalPackageCount"),
        "total_weight_oz": item.get("totalPackageWeight"),
        "location": item.get("packageLocation"),
        "instructions": item.get("specialInstructions") or "",
        "price_usd": (item.get("rate") or {}).get("totalPrice", 0),
        "can_cancel": bool(item.get("canCancel")),
        "ship_from": {"title": warehouse.get("title"), "city": origin.get("city"), "zip": origin.get("postcode")},
    }


EXAMPLE_PICKUP: dict[str, Any] = {
    "id": "88120",
    "carrier": "usps",
    "date": "2026-10-20",
    "ready_time": "00:00",
    "close_time": "00:00",
    "status": "SCHEDULED",
    "confirmation_number": "WTC67845321",
    "package_count": 3,
    "total_weight_oz": 96,
    "location": "FRONT_DOOR",
    "instructions": "",
    "price_usd": 0,
    "can_cancel": True,
    "ship_from": {"title": "Home office", "city": "Charlotte", "zip": "28203"},
}
