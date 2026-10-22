"""Parse address: Pirate Ship's "Paste Address" box, free text to address fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import address
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "minLength": 5,
            "maxLength": 500,
            "description": "An address as written, lines separated by newlines or commas.",
        }
    },
    "required": ["text"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "full_name": "Daniel Brooks",
    "company": "Brooks Studio",
    "address1": "233 S Wacker Dr",
    "address2": "Ste 4400",
    "city": "Chicago",
    "state": "IL",
    "zip": "60606",
    "country": "US",
    "email": "",
}


@tool(
    name="parse_address",
    title="Parse address",
    access="read",
    confirm=False,
    description="Splits a pasted address into name, street, city, state, ZIP and country.",
    details=(
        "Pirate Ship's Paste Address: free text such as a line copied from an email or an order becomes the "
        "fields create_shipment takes. It only parses; the address is checked when the shipment is created."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /addresses/parse",
    example_response=EXAMPLE_RESPONSE,
)
async def parse_address(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found = (await graphql(ctx, "ParsedAddressQuery", {"address": args["text"]}))["data"].get("parsedAddress")
    return {**(address(found) or {}), "email": (found or {}).get("email") or ""}
