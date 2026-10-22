"""Change ship date: re-rates a draft batch for another ship date (rates and delivery estimates follow)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import mutate, refusal, settled_batch, summary

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "batch_id": {"type": "string", "minLength": 1},
        "ship_date": {"type": "string", "format": "date", "description": "One of the rate's ship_dates (YYYY-MM-DD)."},
    },
    "required": ["batch_id", "ship_date"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "batch_id": "632575376",
    "ship_date": "2026-10-20",
    "rates": [{"rate_id": "domestic_big_or_heavy_business:3-1-0", "carrier": "USPS", "price_usd": 7.12}],
}


@tool(
    name="change_ship_date",
    title="Change ship date",
    access="write",
    confirm=False,
    description="Moves a draft batch to another ship date and returns its new rates.",
    details=(
        "The ship date on Pirate Ship's buy page: rates are fetched again for that day, so prices and "
        "estimated delivery can change. Pick a date from a rate's ship_dates. Works on drafts only."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /batches/{batch_id}/ship-date",
    example_response=EXAMPLE_RESPONSE,
)
async def change_ship_date(ctx: ToolContext, args: dict[str, Any]) -> Any:
    answer = await mutate(ctx, "RerateBatchMutation", {"id": str(args["batch_id"]), "shipDate": args["ship_date"]})
    if answer["errors"] or not answer["data"].get("rerateBatch"):
        raise refusal(answer["errors"], "Pirate Ship did not change the ship date.")
    return summary((await settled_batch(ctx, args["batch_id"]))["batch"])
