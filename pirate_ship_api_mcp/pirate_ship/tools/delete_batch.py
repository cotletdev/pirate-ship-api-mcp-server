"""Delete batch: drops an unpaid draft (Pirate Ship refuses bought batches; refund those instead)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import mutate, refusal

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"batch_id": {"type": "string", "minLength": 1}},
    "required": ["batch_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"deleted": "632575376"}


@tool(
    name="delete_batch",
    title="Delete batch",
    access="write",
    confirm=True,
    description="Deletes an unpaid draft batch or single shipment.",
    details=(
        "Removes a draft from create_shipment (or any batch not yet bought) from Pirate Ship. Bought labels "
        "cannot be deleted: refund_label or refund_batch returns their cost."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /batches/{batch_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def delete_batch(ctx: ToolContext, args: dict[str, Any]) -> Any:
    answer = await mutate(ctx, "DeleteBatchMutation", {"id": str(args["batch_id"])})
    if answer["errors"] or not answer["data"].get("deleteBatch"):
        raise refusal(answer["errors"], "Pirate Ship did not delete the batch.")
    return {"deleted": str(args["batch_id"])}
