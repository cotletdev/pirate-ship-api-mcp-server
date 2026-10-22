"""List store connections: Settings, Integrations (Shopify, Etsy, eBay, WooCommerce ...)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


@tool(
    name="list_store_connections",
    title="List store connections",
    access="read",
    confirm=False,
    description="Stores and marketplaces connected to Pirate Ship for order import, with their status.",
    details=(
        "Every connected store (Shopify, Etsy, eBay, WooCommerce, Squarespace and others): its name, "
        "platform, whether it is active and still authorised (valid false means reconnect it in Pirate Ship) "
        "and whether orders sync on their own. Connecting a store happens in Pirate Ship, not here."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /store-connections",
    example_response={
        "stores": [
            {
                "id": "120044",
                "title": "Campbell Candles",
                "platform": "Etsy",
                "platform_key": "etsy",
                "active": True,
                "valid": True,
                "auto_sync": True,
            }
        ]
    },
)
async def list_store_connections(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "ChannelsQuery", {"id": None}))["data"].get("company") or {}
    return {
        "stores": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "platform": (item.get("platform") or {}).get("title"),
                "platform_key": (item.get("platform") or {}).get("platformKey"),
                "active": bool(item.get("active")),
                "valid": bool(item.get("valid")),
                "auto_sync": bool(item.get("autoSyncEnabled")),
            }
            for item in company.get("channels") or []
        ]
    }
