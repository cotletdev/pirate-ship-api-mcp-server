"""Sync store orders: the Import page's Refresh Data button."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "wait_seconds": {
            "type": "integer",
            "minimum": 0,
            "maximum": 60,
            "default": 20,
            "description": "How long to wait for the sync to finish; 0 only starts it.",
        }
    },
    "required": [],
    "additionalProperties": False,
}


async def _status(ctx: ToolContext) -> dict[str, Any]:
    status = (await graphql(ctx, "ChannelSyncStatus"))["data"].get("channelSyncStatus") or {}
    return {
        "running": bool(status.get("isRunning")),
        "progress": status.get("progress", 0),
        "error": bool(status.get("hasError")),
        "messages": [str(item) for item in status.get("messages") or []],
    }


@tool(
    name="sync_store_orders",
    title="Sync store orders",
    access="write",
    confirm=False,
    description="Pulls new orders from every connected store into Pirate Ship's Import list.",
    details=(
        "Starts Refresh Data for all connected stores and waits up to wait_seconds for it to finish; running "
        "true means it continues in the background. Then list_import_orders shows the orders. With no store "
        "connected nothing is imported."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /import-orders/sync",
    example_response={"running": False, "progress": 100, "error": False, "messages": []},
    timeout_s=90,
)
async def sync_store_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    await graphql(ctx, "TriggerChannelSyncMutation")
    status = await _status(ctx)
    waited = 0
    while status["running"] and waited < args.get("wait_seconds", 20):
        await asyncio.sleep(3)
        waited += 3
        status = await _status(ctx)
    return status
