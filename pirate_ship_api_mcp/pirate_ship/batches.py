"""Pirate Ship batches: every label, single or bulk, is a batch (draft, rated, billed), recorded 18.10.2026.

The single shipment form saves the package as a hidden preset (CreateScopedShipmentPreset), makes a batch from
it (CreateBatchFromSingleShipmentMutation, answer: step RATED) and BatchQuery lists the rates per rate group.
A rate id here is "<rate group>:<uniqueId>", the uniqueId being "<mailClassId>-<packageTypeId>-<saturday 0|1>"
as the buy page sends it in rateSelection.
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.pirate_ship.client import graphql
from pirate_ship_api_mcp.pirate_ship.tools.get_rates import PACKAGING

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

_MARKUP = re.compile(r"\[/?(b|i|link[^\]]*)\]")
_UNIQUE_ID = re.compile(r"^\d+-\d+-[01]$")

ADDRESS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string", "minLength": 1, "maxLength": 100},
        "company": {"type": "string", "maxLength": 100},
        "address1": {"type": "string", "minLength": 1, "maxLength": 100},
        "address2": {"type": "string", "maxLength": 100},
        "city": {"type": "string", "minLength": 1, "maxLength": 60},
        "state": {"type": "string", "maxLength": 60, "description": "State or region code, e.g. NY."},
        "zip": {"type": "string", "minLength": 3, "maxLength": 12},
        "country": {"type": "string", "pattern": "^[A-Z]{2}$", "default": "US"},
        "email": {"type": "string", "maxLength": 120},
        "phone": {"type": "string", "maxLength": 30},
    },
    "required": ["full_name", "address1", "city", "zip"],
    "additionalProperties": False,
}


_SOFT = ("Parcel", "SoftEnvelope", "Irregular")

PACKAGE_SCHEMA: dict[str, Any] = {
    "weight_oz": {"type": "number", "exclusiveMinimum": 0, "maximum": 2400, "description": "Weight in ounces."},
    "length_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
    "width_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
    "height_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
    "packaging": {"type": "string", "enum": PACKAGING, "default": "Parcel"},
    "package_preset_id": {
        "type": "string",
        "description": "A saved package: its type, size and weight replace the fields above.",
    },
    "ship_from_id": {"type": "string", "description": "Ship-from address id; default: the account's default."},
    "insured_value_usd": {"type": "number", "minimum": 0, "maximum": 10000},
    "signature": {"type": "string", "enum": ["none", "signature", "adult_signature"], "default": "none"},
}


def strip_markup(text: str | None) -> str:
    return _MARKUP.sub("", text or "")


def address(item: dict[str, Any] | None) -> dict[str, Any] | None:
    """Pirate Ship's address in this integration's field names."""
    if not item:
        return None
    zip4 = item.get("zip4")
    return {
        "full_name": item.get("fullName") or "",
        "company": item.get("company") or "",
        "address1": item.get("address1") or "",
        "address2": item.get("address2") or "",
        "city": item.get("city") or "",
        "state": item.get("regionCode") or "",
        "zip": f"{item.get('postcode') or ''}{'-' + zip4 if zip4 else ''}",
        "country": item.get("countryCode") or "",
    }


async def mutate(ctx: ToolContext, operation: str, variables: dict[str, Any]) -> dict[str, Any]:
    """A write whose refusal keeps its extensions (address correction, payment failure)."""
    return await graphql(ctx, operation, variables, refusals=True)


def refusal(errors: list[dict[str, Any]], fallback: str) -> ToolError:
    message = next((item.get("message") for item in errors if item.get("message")), None)
    return ToolError(strip_markup(message) or fallback, ErrorCode.TARGET_ERROR)


async def load_batch(ctx: ToolContext, batch_id: str) -> dict[str, Any]:
    """BatchQuery's data (batch, company, user); a missing or foreign batch is a not-found error."""
    data = (await graphql(ctx, "BatchQuery", {"id": str(batch_id)}))["data"]
    if not data.get("batch"):
        raise ToolError("No such batch in this Pirate Ship account.", ErrorCode.INVALID_INPUT)
    return data


async def settled_batch(ctx: ToolContext, batch_id: str, wait_s: float = 30) -> dict[str, Any]:
    """BatchQuery after the batch's running process (rating, buying, refunding) finished, or after wait_s."""
    waited = 0.0
    while True:
        data = await load_batch(ctx, batch_id)
        if data["batch"].get("status") != "RUNNING" or waited >= wait_s:
            return data
        await asyncio.sleep(2)
        waited += 2


def rates(batch: dict[str, Any]) -> list[dict[str, Any]]:
    """Every rate the package qualifies for, in every rate group, cheapest first."""
    found = []
    for group in batch.get("rateGroups") or []:
        key = (group.get("groupKey") or {}).get("string") or ""
        for item in group.get("rateSummaries") or []:
            if item.get("errorMessage"):
                continue
            found.append(
                {
                    "rate_id": f"{key}:{item.get('uniqueId')}",
                    "group": key,
                    "carrier": (item.get("carrier") or {}).get("title"),
                    "service": item.get("mailClassTitle"),
                    "mail_class": (item.get("firstMailClass") or {}).get("mailClassKey"),
                    "package_type": (item.get("packageType") or {}).get("packageTypeKey"),
                    "price_usd": item.get("totalPrice"),
                    "retail_usd": item.get("crossedTotalPrice"),
                    "shipments": item.get("shipmentCount"),
                    "zone": item.get("firstZone"),
                    "delivery": strip_markup(item.get("serviceTitle")),
                    "delivery_days": item.get("deliveryDays"),
                    "surcharges": [
                        {"title": extra.get("title"), "price_usd": extra.get("price")}
                        for extra in item.get("surcharges") or []
                    ],
                    "ship_dates": item.get("availableShipDates") or [],
                    "cheapest": bool(item.get("cheapest")),
                    "fastest": bool(item.get("fastest")),
                    "best": bool(item.get("best")),
                }
            )
    found.sort(key=lambda item: item["price_usd"] if item["price_usd"] is not None else float("inf"))
    return found


def summary(batch: dict[str, Any]) -> dict[str, Any]:
    """The batch as get_batch and create_shipment return it."""
    package = batch.get("packageSummary") or {}
    shipments = [
        {
            "shipment_id": item.get("id"),
            "recipient": address(item.get("recipientAddress")),
            "weight_oz": item.get("weight"),
            "dimensions_in": [item.get("dimensionX"), item.get("dimensionY"), item.get("dimensionZ")],
            "return_label": bool(item.get("isReturnLabel")),
            "order_id": (item.get("order") or {}).get("foreignOrderId"),
        }
        for item in batch.get("shipments") or []
    ]
    return {
        "batch_id": batch.get("id"),
        "title": batch.get("title"),
        "step": batch.get("stepText") or batch.get("step"),
        "process": batch.get("status"),
        "ship_date": batch.get("shipDate"),
        "shipment_count": batch.get("numShipments"),
        "ship_from": address((batch.get("warehouse") or {}).get("originAddress")),
        "package": {
            "type": package.get("packageTypeSummary"),
            "dimensions": package.get("dimensionsSummary"),
            "weight_oz": package.get("maxWeight"),
            "insured_usd": package.get("maxInsured"),
            "delivery_confirmation": package.get("deliveryConfirmationSummary"),
        },
        "label_format": {"size": batch.get("labelSize"), "file": batch.get("labelFileFormat")},
        "shipments": shipments,
        "rates": rates(batch),
    }


def rate_selection(batch: dict[str, Any], rate_ids: list[str]) -> tuple[list[dict[str, Any]], float]:
    """rateSelection for BuyBatchMutation and its total price; one rate for every rate group of the batch."""
    groups: dict[str, dict[str, Any]] = {
        (group.get("groupKey") or {}).get("string"): group  # pyright: ignore[reportAssignmentType]  # every rate group has a key
        for group in batch.get("rateGroups") or []
    }
    if not groups:
        raise ToolError(
            "This batch has no rates: it is not ready to buy or was already bought.", ErrorCode.INVALID_INPUT
        )
    chosen: dict[str, dict[str, Any]] = {}
    for rate_id in rate_ids:
        key, _, unique_id = rate_id.rpartition(":")
        if key not in groups or not _UNIQUE_ID.match(unique_id):
            raise ToolError(f"Unknown rate_id {rate_id}: take one from get_batch.", ErrorCode.INVALID_INPUT)
        found = next(
            (item for item in groups[key].get("rateSummaries") or [] if item.get("uniqueId") == unique_id), None
        )
        if found is None or found.get("errorMessage"):
            raise ToolError(f"Rate {rate_id} is not available for this batch.", ErrorCode.INVALID_INPUT)
        chosen[key] = found
    missing = [key for key in groups if key not in chosen]
    if missing:
        raise ToolError(f"Choose one rate for each rate group; missing: {', '.join(missing)}.", ErrorCode.INVALID_INPUT)
    selection = []
    for key, item in chosen.items():
        mail_class, package_type, saturday = item["uniqueId"].split("-")
        traits = (groups[key].get("groupKey") or {}).get("traits") or []
        selection.append(
            {
                "groupKeyInput": {"traits": [{"layer": trait["layer"], "value": trait["value"]} for trait in traits]},
                "mailClassId": mail_class,
                "packageTypeId": package_type,
                "isSaturdayDelivery": saturday == "1",
            }
        )
    total = round(sum(item.get("totalPrice") or 0 for item in chosen.values()), 2)
    return selection, total


def charge(balance: float, total: float, default_charge: float | None) -> float:
    """What the buy page charges the payment method: nothing when the balance covers it, else at least $1."""
    if balance >= total:
        return 0.0
    return round(max(1.0, total - balance, default_charge or 0), 2)


async def batch_details(ctx: ToolContext, batch_id: str) -> dict[str, Any]:
    """summary() plus each shipment's label state and tracking and the price summary (BatchDetailsPageQuery)."""
    batch = (await settled_batch(ctx, batch_id))["batch"]
    result = summary(batch)
    details = (await graphql(ctx, "BatchDetailsPageQuery", {"batchId": str(batch_id)}))["data"].get("batch") or {}
    by_id = {item.get("id"): item for item in details.get("shipments") or []}
    tracking = {}
    if details.get("step") not in (None, "NEW", "RATED"):
        listed = await graphql(ctx, "LatestBatchesQuery", {"pageIndex": 0})
        for item in (listed["data"].get("latestBatches") or {}).get("batches") or []:
            if item.get("id") == batch.get("id"):
                tracking = {ship.get("id"): ship for ship in item.get("shipments") or []}
    for shipment in result["shipments"]:
        extra = by_id.get(shipment["shipment_id"]) or {}
        found = tracking.get(shipment["shipment_id"]) or {}
        shipment.update(
            {
                "status": extra.get("status"),
                "carrier": extra.get("carrierKey"),
                "tracking_number": found.get("trackingNr"),
                "tracking_url": found.get("trackingLink"),
                "can_print": bool(extra.get("canPrint")),
                "can_refund": bool(extra.get("canInstantRefundShipment")),
                "downloaded": bool(extra.get("hasBeenDownloaded")),
            }
        )
    result["refundable"] = bool(details.get("canRefund"))
    result["price_summary"] = [
        {
            "service": item.get("title"),
            "shipments": item.get("shipmentCount"),
            "average_usd": item.get("averagePrice"),
            "total_usd": item.get("totalPrice"),
            "refunded": bool(item.get("isRefunded")),
        }
        for item in details.get("priceSummary") or []
    ]
    return result


def _package_values(args: dict[str, Any], preset: dict[str, Any] | None, signer: str) -> dict[str, Any]:
    if preset is not None:
        values = {key: preset.get(key) for key in _PRESET_KEYS}
        values["customsItems"] = [
            {key: value for key, value in item.items() if key != "__typename"}
            for item in preset.get("customsItems") or []
        ]
    else:
        packaging = args.get("packaging", "Parcel")
        dims = [args.get("length_in"), args.get("width_in"), args.get("height_in")]
        if "weight_oz" not in args:
            raise ToolError("weight_oz is required without package_preset_id.", ErrorCode.INVALID_INPUT)
        if packaging in _SOFT and not all(dims[:2]):
            raise ToolError(
                f"{packaging} needs length_in and width_in (and height_in for a box).", ErrorCode.INVALID_INPUT
            )
        values = {
            "title": "Scoped Preset",
            "packageTypeKey": packaging,
            "dimensionX": dims[0] or 0,
            "dimensionY": dims[1] or 0,
            "dimensionZ": dims[2] or 0,
            "weight": args["weight_oz"],
            "returnLabelFlag": False,
            "returnLabel": "return",
            "qualifiesAsMediaMail": False,
            "irregularPackage": packaging == "Irregular",
            "hazardousMaterialsEnabled": False,
            "customsFormEnabled": False,
            "customsContentType": "Merchandise",
            "customsSigner": signer,
            "customsItems": [],
            "exporterTaxId": "",
            "recipientTaxId": "",
        }
    signature = args.get("signature", "none")
    insured = args.get("insured_value_usd") or 0
    values.update(
        {
            "title": "Scoped Preset",
            "deliveryConfirmationFlag": signature != "none",
            "deliveryConfirmation": signature if signature != "none" else "signature",
            "insuredValueFlag": insured > 0,
            "insuredValue": insured,
        }
    )
    return values


_PRESET_KEYS = (
    "packageTypeKey",
    "dimensionX",
    "dimensionY",
    "dimensionZ",
    "weight",
    "returnLabelFlag",
    "returnLabel",
    "qualifiesAsMediaMail",
    "irregularPackage",
    "hazardousMaterialsEnabled",
    "customsFormEnabled",
    "customsContentType",
    "customsSigner",
    "exporterTaxId",
    "recipientTaxId",
)


async def package_for(ctx: ToolContext, args: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """The ship-from address and a hidden one-off preset for the package, as the web forms make them."""
    form = (await graphql(ctx, "SingleShipmentFormQuery"))["data"].get("company") or {}
    warehouses = form.get("warehouses") or []
    wanted = args.get("ship_from_id") or (form.get("settings") or {}).get("defaultWarehouseId")
    warehouse = next((item for item in warehouses if item.get("id") == wanted), None)
    if warehouse is None and not args.get("ship_from_id") and warehouses:
        warehouse = warehouses[0]
    if warehouse is None:
        raise ToolError("No such ship-from address: add one in Pirate Ship or pick another.", ErrorCode.INVALID_INPUT)
    preset = None
    if preset_id := args.get("package_preset_id"):
        preset = next((item for item in form.get("shipmentPresets") or [] if item.get("id") == str(preset_id)), None)
        if preset is None:
            raise ToolError("No such saved package.", ErrorCode.INVALID_INPUT)
    signer = ((warehouse.get("originAddress") or {}).get("fullName") or "").strip()
    scoped = await graphql(
        ctx,
        "CreateScopedShipmentPreset",
        {
            "originalPresetId": str(preset["id"]) if preset else "0",
            "shipmentPreset": _package_values(args, preset, signer),
        },
    )
    preset_ref = (scoped["data"].get("createScopedShipmentPreset") or {}).get("id")
    if not preset_ref:
        raise refusal(scoped["errors"], "Pirate Ship did not accept the package.")
    return warehouse, preset_ref
