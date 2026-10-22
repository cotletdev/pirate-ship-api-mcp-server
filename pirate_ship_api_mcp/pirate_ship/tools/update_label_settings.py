"""Update label settings: Settings, General, Save (UpdateGeneralSettingsMutation sends every field)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import mutate, refusal
from pirate_ship_api_mcp.pirate_ship.tools._labels import (
    ADDRESS_CORRECTION,
    EXAMPLE,
    PACKING_LIST,
    PROPERTIES,
    raw_settings,
    settings_out,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": PROPERTIES,
    "required": [],
    "minProperties": 1,
    "additionalProperties": False,
}


def _key(mapping: dict[str, str], value: str) -> str:
    return next(key for key, name in mapping.items() if name == value)


@tool(
    name="update_label_settings",
    title="Update label settings",
    access="write",
    confirm=False,
    description="Changes label size, file format, packing list, logo, QR codes, address correction or export format.",
    details=(
        "Saves Settings, General for the whole account. Fields you leave out keep their values. Applies to "
        "labels made from now on; get_label_settings shows the current values."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /label-settings",
    example_response=EXAMPLE,
)
async def update_label_settings(ctx: ToolContext, args: dict[str, Any]) -> Any:
    raw = await raw_settings(ctx)
    if not raw:
        raise ToolError("Pirate Ship did not return the settings.", ErrorCode.TARGET_ERROR)
    current = settings_out(raw)
    wanted = {**current, **args}
    variables = {
        "areMobileCodesEnabled": wanted["mobile_codes"],
        "shipmentLabelSize": wanted["label_size"],
        "shipmentLabelFileFormat": wanted["label_format"],
        "packingListTemplate": _key(PACKING_LIST, wanted["packing_list"]),
        "showLogoOnLabel": wanted["logo_on_label"],
        "shipmentSpreadsheetFormat": wanted["report_format"],
        "addressCorrection": _key(ADDRESS_CORRECTION, wanted["address_correction"]),
    }
    answer = await mutate(ctx, "UpdateGeneralSettingsMutation", variables)
    if answer["errors"]:
        raise refusal(answer["errors"], "Pirate Ship did not save the settings.")
    return settings_out(await raw_settings(ctx))
