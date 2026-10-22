"""Create batch: Pirate Ship's "Upload a Spreadsheet" for many packages at once, up to the rates.

The recipients go up as a CSV (upload.py), CreateBatchFromUploadMutation maps its columns, and
CompleteBatchFromUploadMutation gives the batch its title, ship-from address and package; Pirate Ship then
validates and rates every row. Recorded 18.10.2026 on a production team account.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.batches import (
    ADDRESS_SCHEMA,
    PACKAGE_SCHEMA,
    mutate,
    package_for,
    refusal,
    settled_batch,
    summary,
)
from pirate_ship_api_mcp.pirate_ship.upload import to_csv, upload_csv

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

# CSV column -> Pirate Ship's shipment field, and how a recipient fills it.
_COLUMNS = (
    ("Name", "FULL_NAME", lambda row: row["full_name"]),
    ("Company", "COMPANY", lambda row: row.get("company")),
    ("Email", "EMAIL", lambda row: row.get("email")),
    ("Phone", "PHONE", lambda row: row.get("phone")),
    ("Address 1", "ADDRESS1", lambda row: row["address1"]),
    ("Address 2", "ADDRESS2", lambda row: row.get("address2")),
    ("City", "CITY", lambda row: row["city"]),
    ("State", "REGION_ID", lambda row: row.get("state")),
    ("Zip", "POSTCODE", lambda row: row["zip"]),
    ("Country", "COUNTRY_ID", lambda row: row.get("country", "US")),
    ("Weight oz", "WEIGHT", lambda row: row.get("weight_oz")),
    ("Length in", "DIMENSION_X", lambda row: row.get("length_in")),
    ("Width in", "DIMENSION_Y", lambda row: row.get("width_in")),
    ("Height in", "DIMENSION_Z", lambda row: row.get("height_in")),
    ("Order Id", "FOREIGN_ORDER_ID", lambda row: row.get("order_id")),
    ("Rubber Stamp 1", "RUBBER_STAMP1", lambda row: row.get("rubber_stamp_1")),
)

RECIPIENT_SCHEMA: dict[str, Any] = {
    **ADDRESS_SCHEMA,
    "properties": {
        **ADDRESS_SCHEMA["properties"],
        "weight_oz": {
            "type": "number",
            "exclusiveMinimum": 0,
            "maximum": 2400,
            "description": "Overrides the package.",
        },
        "length_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
        "width_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
        "height_in": {"type": "number", "exclusiveMinimum": 0, "maximum": 130},
        "order_id": {"type": "string", "maxLength": 50, "description": "Your order number, kept on the label."},
        "rubber_stamp_1": {"type": "string", "maxLength": 50},
    },
}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 100, "description": "Batch name."},
        "shipments": {"type": "array", "items": RECIPIENT_SCHEMA, "minItems": 1, "maxItems": 500},
        **PACKAGE_SCHEMA,
    },
    "required": ["title", "shipments"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "batch_id": "632576079",
    "title": "October orders",
    "step": "Rated",
    "process": "IDLE",
    "ship_date": "2026-10-19",
    "shipment_count": 2,
    "errors": 0,
    "rates": [
        {
            "rate_id": "domestic_big_or_heavy:30-1-0",
            "group": "domestic_big_or_heavy",
            "carrier": "UPS",
            "service": "UPS® Ground",
            "price_usd": 8.12,
            "shipments": 1,
            "cheapest": True,
        },
        {
            "rate_id": "domestic_light_and_small_business:30-1-0",
            "group": "domestic_light_and_small_business",
            "carrier": "UPS",
            "service": "UPS® Ground",
            "price_usd": 7.31,
            "shipments": 1,
            "cheapest": True,
        },
    ],
}


@tool(
    name="create_batch",
    title="Create batch",
    access="write",
    confirm=False,
    description="Unpaid draft batch for many packages with the rates of each rate group; buy it with buy_label.",
    details=(
        "Pirate Ship's spreadsheet upload: one batch for up to 500 recipients from your ship-from address, "
        "rated by Pirate Ship. The package (packaging, weight_oz and size, or package_preset_id) applies to "
        "every shipment; a recipient's own weight_oz or size overrides it. Pirate Ship splits the batch into "
        "rate groups (domestic small, big or heavy, international): buy_label needs one rate_id per group. "
        "errors counts rows Pirate Ship could not rate (an address it cannot find); get_batch shows them. "
        "Nothing is charged; delete_batch drops the draft."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /batches",
    example_response=EXAMPLE_RESPONSE,
    timeout_s=120,
)
async def create_batch(ctx: ToolContext, args: dict[str, Any]) -> Any:
    rows = args["shipments"]
    used = [column for column in _COLUMNS if any(column[2](row) not in (None, "") for row in rows)]
    text = to_csv([name for name, _, _ in used], [[value(row) for _, _, value in used] for row in rows])
    warehouse, preset_ref = await package_for(ctx, args)
    uploaded = await upload_csv(ctx, text)
    upload_id = uploaded.get("uploadId")
    if not upload_id:
        raise ToolError(uploaded.get("error") or "Pirate Ship did not take the spreadsheet.", ErrorCode.TARGET_ERROR)
    mapping = [{"shipmentKey": key, "valueOrMappingKey": name} for name, key, _ in used]
    answer = await mutate(ctx, "CreateBatchFromUploadMutation", {"uploadId": str(upload_id), "mapping": mapping})
    batch_id = (answer["data"].get("createBatchFromUpload") or {}).get("id")
    if not batch_id:
        raise refusal(answer["errors"], "Pirate Ship did not read the shipments.")
    variables = {
        "batchId": batch_id,
        "batchTitle": args["title"],
        "warehouseId": warehouse["id"],
        "shipmentPresetId": preset_ref,
    }
    answer = await mutate(ctx, "CompleteBatchFromUploadMutation", variables)
    if not answer["data"].get("completeBatchFromUpload"):
        raise refusal(answer["errors"], "Pirate Ship did not create the batch.")
    batch = (await settled_batch(ctx, batch_id, wait_s=90))["batch"]
    result = summary(batch)
    result.pop("shipments", None)
    return {**result, "errors": (batch.get("shipmentStatusSummary") or {}).get("errorCount", 0)}
