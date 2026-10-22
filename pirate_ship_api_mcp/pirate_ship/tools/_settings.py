"""Shapes shared by the Settings tools: ship-from addresses, saved packages and tracking email templates.

Recorded 18.10.2026 from Pirate Ship's settings pages (WarehouseFragment, ShipmentPresetFragment,
MailTemplateFragment). Weights in ounces, sizes in inches, money in US dollars.
"""

from __future__ import annotations

from typing import Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError

ADDRESS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string", "minLength": 1, "maxLength": 100},
        "company": {"type": "string", "maxLength": 100},
        "address1": {"type": "string", "minLength": 1, "maxLength": 100, "description": "Street and number."},
        "address2": {"type": "string", "maxLength": 100, "description": "Apt, unit, suite."},
        "city": {"type": "string", "minLength": 1, "maxLength": 60},
        "state": {"type": "string", "minLength": 2, "maxLength": 2, "description": "US state code, e.g. NC."},
        "zip": {"type": "string", "minLength": 5, "maxLength": 10},
        "phone": {"type": "string", "maxLength": 20},
    },
    "required": ["full_name", "address1", "city", "state", "zip"],
    "additionalProperties": False,
}

EXAMPLE_ADDRESS: dict[str, Any] = {
    "full_name": "Jane Doe",
    "company": "",
    "address1": "100 Main St",
    "address2": "",
    "city": "Charlotte",
    "state": "NC",
    "zip": "28203",
    "zip4": "4239",
    "country": "US",
    "phone": "7045550100",
}

EXAMPLE_SHIP_FROM: dict[str, Any] = {
    "id": "1000001",
    "title": "Home office",
    "default": True,
    "origin": EXAMPLE_ADDRESS,
    "return_address": {key: value for key, value in EXAMPLE_ADDRESS.items() if key != "phone"},
    "origin_is_return": True,
}


def address_input(address: dict[str, Any]) -> dict[str, Any]:
    """Our address fields as Pirate Ship's AddressInput (US only, like the Settings form)."""
    return {
        "fullName": address["full_name"].strip(),
        "company": address.get("company", ""),
        "address1": address["address1"].strip(),
        "address2": address.get("address2", ""),
        "city": address["city"].strip(),
        "regionCode": address["state"].upper(),
        "postcode": address["zip"].strip(),
        "countryCode": "US",
        "phone": address.get("phone", ""),
    }


def address_out(address: dict[str, Any] | None) -> dict[str, Any] | None:
    if not address:
        return None
    out = {
        "full_name": address.get("fullName"),
        "company": address.get("company") or "",
        "address1": address.get("address1"),
        "address2": address.get("address2") or "",
        "city": address.get("city"),
        "state": address.get("regionCode"),
        "zip": address.get("postcode"),
        "zip4": address.get("zip4") or "",
        "country": address.get("countryCode"),
    }
    if "phone" in address:
        out["phone"] = address.get("phone") or ""
    return out


def ship_from_out(warehouse: dict[str, Any], default_id: str | None) -> dict[str, Any]:
    return {
        "id": warehouse["id"],
        "title": warehouse.get("title"),
        "default": warehouse["id"] == default_id,
        "origin": address_out(warehouse.get("originAddress")),
        "return_address": address_out(warehouse.get("returnAddress")),
        "origin_is_return": bool(warehouse.get("useOriginAsReturnAddress")),
    }


PACKAGE_TYPES = [
    "Parcel",
    "SoftEnvelope",
    "Irregular",
    "SmallFlatRateBox",
    "MediumFlatRateBox",
    "LargeFlatRateBox",
    "FlatRateEnvelope",
    "FlatRateLegalEnvelope",
    "FlatRatePaddedEnvelope",
]
SIGNATURE = {"none": "none", "signature": "signature", "adult_signature": "adult_signature"}
RETURN_LABEL = ["none", "return", "standard_and_return"]

PACKAGE_PROPERTIES: dict[str, Any] = {
    "title": {"type": "string", "minLength": 1, "maxLength": 100, "description": "Name shown in Saved Packages."},
    "packaging": {"type": "string", "enum": PACKAGE_TYPES, "default": "Parcel"},
    "length_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
    "width_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
    "height_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
    "weight_oz": {"type": "number", "minimum": 0, "maximum": 2400, "description": "0 leaves the weight to each label."},
    "signature": {"type": "string", "enum": list(SIGNATURE), "default": "none"},
    "insured_value_usd": {"type": "number", "minimum": 0, "maximum": 10000, "default": 0},
    "return_label": {
        "type": "string",
        "enum": RETURN_LABEL,
        "default": "none",
        "description": "return: return labels only; standard_and_return: an extra return label.",
    },
    "media_mail": {"type": "boolean", "default": False, "description": "Qualifies for USPS Media Mail."},
    "irregular": {"type": "boolean", "default": False},
    "hazardous_materials": {"type": "boolean", "default": False},
    "default": {"type": "boolean", "default": False, "description": "Preselect it on new shipments."},
}

EXAMPLE_PACKAGE: dict[str, Any] = {
    "id": "518829001",
    "title": "Medium box",
    "default": False,
    "packaging": "Parcel",
    "length_in": 12,
    "width_in": 10,
    "height_in": 6,
    "weight_oz": 24,
    "signature": "none",
    "insured_value_usd": 0,
    "return_label": "none",
    "media_mail": False,
    "irregular": False,
    "hazardous_materials": False,
    "customs_form": False,
}


def package_input(args: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
    """ShipmentPresetInput as the Saved Package form sends it; fields not given keep the current values."""
    base = current or {}

    def pick(key: str, field: str, fallback: Any) -> Any:
        return args[key] if key in args else base.get(field, fallback)

    packaging = pick("packaging", "packageTypeKey", "Parcel")
    if packaging in ("Parcel", "SoftEnvelope", "Irregular") and not (
        pick("length_in", "dimensionX", 0) and pick("width_in", "dimensionY", 0)
    ):
        raise ToolError(f"{packaging} needs length_in and width_in.", ErrorCode.INVALID_INPUT)
    signature = pick("signature", "deliveryConfirmation", "none") or "none"
    return_label = pick("return_label", "returnLabel", "none") or "none"
    insured = pick("insured_value_usd", "insuredValue", 0) or 0
    return {
        "title": pick("title", "title", ""),
        "packageTypeKey": packaging,
        "dimensionX": pick("length_in", "dimensionX", 0) or 0,
        "dimensionY": pick("width_in", "dimensionY", 0) or 0,
        "dimensionZ": pick("height_in", "dimensionZ", 0) or 0,
        "weight": pick("weight_oz", "weight", 0) or 0,
        "deliveryConfirmationFlag": signature != "none",
        "deliveryConfirmation": signature if signature != "none" else "signature",
        "returnLabelFlag": return_label != "none",
        "returnLabel": return_label if return_label != "none" else "return",
        "insuredValueFlag": insured > 0,
        "insuredValue": insured,
        "qualifiesAsMediaMail": pick("media_mail", "qualifiesAsMediaMail", False),
        "irregularPackage": pick("irregular", "irregularPackage", False),
        "hazardousMaterialsEnabled": pick("hazardous_materials", "hazardousMaterialsEnabled", False),
        "customsFormEnabled": base.get("customsFormEnabled", False),
        "customsContentType": base.get("customsContentType") or "Merchandise",
        "customsSigner": base.get("customsSigner") or "",
        "customsItems": [
            {k: v for k, v in item.items() if k != "__typename"} for item in base.get("customsItems") or []
        ],
        "exporterTaxId": base.get("exporterTaxId") or "",
        "recipientTaxId": base.get("recipientTaxId") or "",
    }


def package_out(preset: dict[str, Any], default_id: str | None) -> dict[str, Any]:
    return {
        "id": preset["id"],
        "title": preset.get("title"),
        "default": preset["id"] == default_id,
        "packaging": preset.get("packageTypeKey"),
        "length_in": preset.get("dimensionX"),
        "width_in": preset.get("dimensionY"),
        "height_in": preset.get("dimensionZ"),
        "weight_oz": preset.get("weight"),
        "signature": preset.get("deliveryConfirmation") if preset.get("deliveryConfirmationFlag") else "none",
        "insured_value_usd": preset.get("insuredValue") if preset.get("insuredValueFlag") else 0,
        "return_label": preset.get("returnLabel") if preset.get("returnLabelFlag") else "none",
        "media_mail": bool(preset.get("qualifiesAsMediaMail")),
        "irregular": bool(preset.get("irregularPackage")),
        "hazardous_materials": bool(preset.get("hazardousMaterialsEnabled")),
        "customs_form": bool(preset.get("customsFormEnabled")),
    }


TEMPLATE_PROPERTIES: dict[str, Any] = {
    "name": {"type": "string", "minLength": 1, "maxLength": 100, "description": "Template name in Settings."},
    "subject": {"type": "string", "minLength": 1, "maxLength": 200},
    "html": {
        "type": "string",
        "minLength": 1,
        "maxLength": 20000,
        "description": "Body as HTML. Placeholders: [Recipient First Name], [Ship Date], [Shipping Service], "
        "[Recipient Address], [Tracking #].",
    },
    "sender_name": {"type": "string", "minLength": 1, "maxLength": 100},
    "sender_email": {"type": "string", "format": "email", "description": "Reply-to address recipients see."},
    "bcc_email": {"type": "string", "description": "A copy of every email goes here. Empty for none."},
    "default": {"type": "boolean", "default": False, "description": "Use it for new labels."},
}

EXAMPLE_TEMPLATE: dict[str, Any] = {
    "id": "6800981",
    "name": "Default",
    "default": True,
    "subject": "Your shipment is on its way!",
    "sender_name": "Jane Doe",
    "sender_email": "jane@example.com",
    "bcc_email": "",
    "html": "Dear [Recipient First Name],<br><br>Your package will ship on [Ship Date] via [Shipping Service]. "
    "Track it: [Tracking #]",
}


def template_out(template: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": template["id"],
        "name": template.get("name"),
        "default": bool(template.get("asDefault")),
        "subject": template.get("subject"),
        "sender_name": template.get("senderName"),
        "sender_email": template.get("senderEmail"),
        "bcc_email": template.get("bccEmail") or "",
        "html": template.get("templateHtml"),
    }
