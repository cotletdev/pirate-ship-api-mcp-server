"""Search recipients: addresses of past shipments, as the Ship To form suggests them while typing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import address
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

_FIELDS = {"name": "FULL_NAME", "email": "EMAIL", "phone": "PHONE"}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 2, "maxLength": 100},
        "field": {"type": "string", "enum": list(_FIELDS), "default": "name"},
    },
    "required": ["query"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "recipients": [
        {
            "full_name": "Linda Morales",
            "company": "",
            "address1": "350 5th Ave",
            "address2": "",
            "city": "New York",
            "state": "NY",
            "zip": "10118-0110",
            "country": "US",
            "email": "",
            "phone": "",
        }
    ]
}


@tool(
    name="search_recipients",
    title="Search recipients",
    access="read",
    confirm=False,
    description="Past recipients' addresses matching a name, email or phone.",
    details=(
        "The suggestions Pirate Ship's Ship To form shows while typing: addresses of people this account "
        "shipped to before, matched by the start of their name (or email or phone). Use one as create_shipment's to."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /recipients/search",
    example_response=EXAMPLE_RESPONSE,
)
async def search_recipients(ctx: ToolContext, args: dict[str, Any]) -> Any:
    variables = {"searchField": _FIELDS[args.get("field", "name")], "input": args["query"]}
    found = (await graphql(ctx, "HistoricShipmentAddressesQuery", variables))["data"].get("historicShipmentAddresses")
    return {
        "recipients": [
            {**(address(item) or {}), "email": item.get("email") or "", "phone": item.get("phone") or ""}
            for item in found or []
        ]
    }
