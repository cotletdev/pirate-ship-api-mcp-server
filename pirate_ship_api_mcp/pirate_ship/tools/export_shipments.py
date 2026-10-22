"""Export shipments: the Export button of Reports, Shipments (ShipmentReportGridExportQuery)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.grids import grid_export, report_filters, report_sorting
from pirate_ship_api_mcp.pirate_ship.tools.list_shipments import DATE_FIELD, FIELDS, LISTS
from pirate_ship_api_mcp.pirate_ship.tools.list_shipments import INPUT_SCHEMA as LIST_SCHEMA

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

# Every report column; id and batch_id are row keys, not columns.
COLUMNS = [field for field in FIELDS if field not in ("id", "batch_id")]

INPUT_SCHEMA: dict[str, Any] = {
    **LIST_SCHEMA,
    "properties": {key: value for key, value in LIST_SCHEMA["properties"].items() if key not in ("limit", "offset")},
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "url": "https://ship.pirateship.com/export/shipments-2026-10-18.csv",
    "filename": "shipments-2026-10-18.csv",
    "empty": False,
}


@tool(
    name="export_shipments",
    title="Export shipments",
    access="read",
    confirm=False,
    description="A CSV of the shipments report with every column, as a download link.",
    details=(
        "Builds the same spreadsheet as the Export button of Reports, Shipments: one row per label with every "
        "column (recipient and address, tracking, carrier and service, cost, package, batch, ship-from, order "
        "id, rubber stamps). Takes the filters of list_shipments. Returns a link to the CSV; a filter with no "
        "matching labels returns empty true and no link. Large exports can take up to a minute."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /shipments/export",
    example_response=EXAMPLE_RESPONSE,
    timeout_s=90,
)
async def export_shipments(ctx: ToolContext, args: dict[str, Any]) -> Any:
    variables: dict[str, Any] = {
        "searchTerm": args.get("search") or "",
        "filters": report_filters(ctx, args, DATE_FIELD, LISTS),
        "sorting": report_sorting(args, DATE_FIELD),
        "columns": COLUMNS,
    }
    return await grid_export(ctx, "ShipmentReportGridExportQuery", "shipmentReport", variables)
