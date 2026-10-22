"""Rename batch: the batch title shown on the Ship page and in reports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import mutate, refusal

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "batch_id": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1, "maxLength": 100},
    },
    "required": ["batch_id", "title"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"batch_id": "632575376", "title": "October orders"}


@tool(
    name="rename_batch",
    title="Rename batch",
    access="write",
    confirm=False,
    description="Changes a batch's title.",
    details="Sets the title Pirate Ship shows for a batch or single label on the Ship page and in reports.",
    input_schema=INPUT_SCHEMA,
    route="PATCH /batches/{batch_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def rename_batch(ctx: ToolContext, args: dict[str, Any]) -> Any:
    answer = await mutate(ctx, "UpdateBatchTitleMutation", {"id": str(args["batch_id"]), "title": args["title"]})
    batch = answer["data"].get("updateBatchTitle")
    if answer["errors"] or not batch:
        raise refusal(answer["errors"], "Pirate Ship did not rename the batch.")
    return {"batch_id": batch.get("id"), "title": batch.get("title")}
