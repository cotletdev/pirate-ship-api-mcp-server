"""Download labels: the Print Labels dialog, one PDF (or PNG/ZPL) link for bought labels of a batch or shipments.

The trigger answers a download id; LabelsQuery is polled until the file is FINISHED, as the dialog polls it
every second (canShowBatchLabels and SharePrintLabelsPage chunks, 18.10.2026).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import mutate, refusal
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "batch_id": {"type": "string", "description": "Every printable label of this batch."},
        "shipment_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 100},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "status": "FINISHED",
    "url": "https://ship.pirateship.com/download/labels/abc123.pdf",
    "file_format": "PDF",
    "page_layout": "4x6",
}


async def _printable(ctx: ToolContext, args: dict[str, Any]) -> int:
    """How many labels can be printed; the dialog checks this before it asks for a file."""
    if args.get("batch_id"):
        data = await graphql(ctx, "LabelsModalBatchArtifactsQuery", {"batchId": str(args["batch_id"])})
        shipments = (data["data"].get("batch") or {}).get("shipments") or []
    else:
        variables = {"shipmentIds": [str(item) for item in args["shipment_ids"]]}
        shipments = (await graphql(ctx, "ShipmentsAfterLabelDownloadQuery", variables))["data"].get("shipments") or []
    return sum(1 for item in shipments if item.get("canPrint"))


@tool(
    name="download_labels",
    title="Download labels",
    access="read",
    confirm=False,
    description="A download link for the printable labels of a batch or of chosen shipments.",
    details=(
        "Pirate Ship's Print Labels: builds one file with the bought, printable labels of batch_id or of "
        "shipment_ids, in the account's label size and format (Settings, Label Settings), and returns its "
        "link. Building takes a few seconds. Refunded labels and return labels that print later are left out."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /labels",
    example_response=EXAMPLE_RESPONSE,
)
async def download_labels(ctx: ToolContext, args: dict[str, Any]) -> Any:
    if not args.get("batch_id") and not args.get("shipment_ids"):
        raise ToolError("Give batch_id or shipment_ids.", ErrorCode.INVALID_INPUT)
    if not await _printable(ctx, args):
        raise ToolError(
            "Nothing to print there: buy the labels first (refunded labels do not print).", ErrorCode.INVALID_INPUT
        )
    if args.get("batch_id"):
        answer = await mutate(ctx, "TriggerDownloadLabelsByBatchesMutation", {"batchIds": [str(args["batch_id"])]})
        download_id = answer["data"].get("triggerLabelCreationByBatches")
    else:
        variables = {"shipmentIds": [str(item) for item in args["shipment_ids"]]}
        answer = await mutate(ctx, "TriggerDownloadLabelsByShipmentsMutation", variables)
        download_id = answer["data"].get("triggerLabelCreationByShipments")
    if answer["errors"] or not download_id:
        raise refusal(answer["errors"], "Pirate Ship has no printable labels there.")
    labels: dict[str, Any] = {}
    for _ in range(30):
        labels = (await graphql(ctx, "LabelsQuery", {"downloadId": str(download_id)}))["data"].get("labels") or {}
        if labels.get("status") in ("FINISHED", "ERROR"):
            break
        await asyncio.sleep(1.5)
    if labels.get("status") == "ERROR":
        raise ToolError("Pirate Ship could not build the label file.", ErrorCode.TARGET_ERROR)
    if labels.get("status") != "FINISHED":
        raise ToolError("Pirate Ship is still building the label file; call again in a minute.", ErrorCode.TIMEOUT)
    return {
        "status": labels["status"],
        "url": labels.get("url"),
        "file_format": labels.get("fileFormat"),
        "page_layout": labels.get("pageLayout"),
    }
