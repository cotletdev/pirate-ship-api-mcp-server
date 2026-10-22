"""List SCAN forms: the End of Day (SCAN Forms) page."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


@tool(
    name="list_scan_forms",
    title="List SCAN forms",
    access="read",
    confirm=False,
    description="USPS SCAN Forms per Ship From Address, with their PDF links and labels still without one.",
    details=(
        "For every Ship From Address with USPS labels: how many labels can still go on a SCAN Form "
        "(labels_available) and the SCAN Forms already made, each with ship date, label count and PDF link. "
        "A SCAN Form lets the carrier scan all packages at once. Make one with create_scan_form."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /scan-forms",
    example_response={
        "ship_from": [
            {
                "id": "1000001",
                "title": "Home office",
                "default": True,
                "labels_available": 2,
                "scan_forms": [
                    {
                        "id": "77120",
                        "ship_date": "2026-10-19",
                        "labels": 5,
                        "url": "https://ship.pirateship.com/scanform/77120.pdf",
                        "updated_at": "2026-10-19T16:02:11+00:00",
                    }
                ],
            }
        ]
    },
)
async def list_scan_forms(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "ScanFormsQuery"))["data"].get("company") or {}
    default_id = (company.get("settings") or {}).get("defaultWarehouseId")
    return {
        "ship_from": [
            {
                "id": item["id"],
                "title": item.get("title"),
                "default": item["id"] == default_id,
                "labels_available": item.get("totalAvailableLabelsForScanForm", 0),
                "scan_forms": [
                    {
                        "id": form.get("id"),
                        "ship_date": form.get("shipDate"),
                        "labels": form.get("shipmentCount", 0),
                        "url": form.get("url"),
                        "updated_at": form.get("updatedAt"),
                    }
                    for form in item.get("scanForms") or []
                ],
            }
            for item in company.get("warehouses") or []
        ]
    }
