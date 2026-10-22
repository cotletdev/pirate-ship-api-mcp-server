"""Label settings of Settings, General (GeneralSettingsQuery); option values from the page, 18.10.2026."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

ADDRESS_CORRECTION = {"0": "off", "1": "confirm", "2": "automatic"}
PACKING_LIST = {
    "disabled": "none",
    "default": "with_gift_message",
    "gift_only": "gift_message_only",
}

PROPERTIES: dict[str, Any] = {
    "label_size": {"type": "string", "enum": ["4x6", "2x7"], "description": "Label size in inches."},
    "label_format": {"type": "string", "enum": ["pdf", "zpl"], "description": "PDF, or ZPLII for thermal printers."},
    "packing_list": {"type": "string", "enum": list(PACKING_LIST.values())},
    "logo_on_label": {"type": "boolean"},
    "mobile_codes": {"type": "boolean", "description": "Offer USPS label-free QR codes."},
    "address_correction": {
        "type": "string",
        "enum": list(ADDRESS_CORRECTION.values()),
        "description": "What Pirate Ship does when it finds a better address: nothing, ask, or correct it.",
    },
    "report_format": {"type": "string", "enum": ["xlsx", "csv"], "description": "Spreadsheet format of exports."},
}

EXAMPLE: dict[str, Any] = {
    "label_size": "4x6",
    "label_format": "pdf",
    "packing_list": "none",
    "logo_on_label": True,
    "mobile_codes": False,
    "address_correction": "confirm",
    "report_format": "xlsx",
}


async def raw_settings(ctx: ToolContext) -> dict[str, Any]:
    return ((await graphql(ctx, "GeneralSettingsQuery"))["data"].get("company") or {}).get("settings") or {}


def settings_out(raw: dict[str, Any]) -> dict[str, Any]:
    packing = raw.get("packingListTemplate")
    return {
        "label_size": raw.get("shipmentLabelSize"),
        "label_format": raw.get("shipmentLabelFileFormat"),
        "packing_list": PACKING_LIST.get(packing, packing) if isinstance(packing, str) else packing,
        "logo_on_label": bool(raw.get("showLogoOnLabel")),
        "mobile_codes": bool(raw.get("areMobileCodesEnabled")),
        "address_correction": ADDRESS_CORRECTION.get(str(raw.get("addressCorrection")), raw.get("addressCorrection")),
        "report_format": raw.get("shipmentSpreadsheetFormat"),
    }
