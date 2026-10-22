"""Export report: the Export button of the other Reports tables (transactions, refunds, receipts, return
labels, carrier adjustments); export_shipments covers Shipments with its own filters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.grids import DATE_SCHEMA, grid_export, report_filters, report_sorting
from pirate_ship_api_mcp.pirate_ship.tools import (
    list_carrier_adjustments,
    list_receipts,
    list_refunds,
    list_return_labels,
    list_transactions,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

# report -> (export operation, grid root, the list tool's module with FIELDS and DATE_FIELD)
REPORTS = {
    "transactions": ("TransactionHistoryGridExportQuery", "transactionHistory", list_transactions),
    "refunds": ("RefundReportGridExportQuery", "refundReport", list_refunds),
    "receipts": ("ReceiptsReportGridExportQuery", "receiptsReport", list_receipts),
    "return_labels": ("ReturnLabelsReportGridExportQuery", "returnLabelsReport", list_return_labels),
    "carrier_adjustments": (
        "CarrierAdjustmentReportGridExportQuery",
        "carrierAdjustmentReport",
        list_carrier_adjustments,
    ),
}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "report": {"type": "string", "enum": list(REPORTS)},
        "search": {"type": "string", "maxLength": 200, "description": "Free text, as in the report's search box."},
        **DATE_SCHEMA,
    },
    "required": ["report"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "url": "https://ship.pirateship.com/export/transactions-2026-10-18.csv",
    "filename": "transactions-2026-10-18.csv",
    "empty": False,
}


@tool(
    name="export_report",
    title="Export report",
    access="read",
    confirm=False,
    description="A CSV of the transactions, refunds, receipts, return labels or carrier adjustments report.",
    details=(
        "Builds the same spreadsheet as the Export button of the chosen Reports table, with every column of "
        "the matching list_ tool, for an optional date range and search. Returns a link to the CSV; no matching "
        "rows return empty true and no link. Shipments have their own tool, export_shipments."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /reports/{report}/export",
    example_response=EXAMPLE_RESPONSE,
    timeout_s=90,
)
async def export_report(ctx: ToolContext, args: dict[str, Any]) -> Any:
    operation, root, source = REPORTS[args["report"]]
    variables = {
        "searchTerm": args.get("search") or "",
        "filters": report_filters(ctx, args, source.DATE_FIELD, {}),
        "sorting": report_sorting(args, source.DATE_FIELD),
        "columns": [field for field in source.FIELDS if field not in ("id", "batch_id")],
    }
    return await grid_export(ctx, operation, root, variables)
