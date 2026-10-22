"""List transactions: Pirate Ship's Reports, Transaction History table (TransactionHistoryGridRowsQuery)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.grids import (
    DATE_SCHEMA,
    PAGING_SCHEMA,
    grid_rows,
    renamed,
    report_filters,
    report_sorting,
)

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

FIELDS = {
    "id": "transaction_id",
    "created_at": "created_at",
    "transaction_type": "type",
    "title": "description",
    "amount": "amount_usd",
    "balance": "balance_usd",
}
LISTS = {"type": "transaction_type"}
DATE_FIELD = "created_at"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **PAGING_SCHEMA,
        **DATE_SCHEMA,
        "type": {
            "type": "array",
            "items": {"type": "string", "maxLength": 100},
            "maxItems": 20,
            "description": "Transaction types as the table shows them, e.g. Label, Payment, Refund.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total": 1,
    "transactions": [
        {
            "transaction_id": "88812345",
            "created_at": "2026-10-16T14:02:11-04:00",
            "type": "Label",
            "description": "USPS Ground Advantage label to Linda Morales",
            "amount_usd": -6.86,
            "balance_usd": 13.14,
        }
    ],
}


@tool(
    name="list_transactions",
    title="List transactions",
    access="read",
    confirm=False,
    description="Every charge, payment and refund on the Pirate Ship balance, newest first.",
    details=(
        "The Reports, Transaction History table: each label purchase, payment, refund and carrier adjustment "
        "with its amount in US dollars (negative takes from the balance) and the balance after it. from_date "
        "and to_date narrow by day, type by the table's transaction types, search works like its search box."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /transactions",
    example_response=EXAMPLE_RESPONSE,
)
async def list_transactions(ctx: ToolContext, args: dict[str, Any]) -> Any:
    result = await grid_rows(
        ctx,
        "TransactionHistoryGridRowsQuery",
        "transactionHistory",
        args,
        filters=report_filters(ctx, args, DATE_FIELD, LISTS),
        sorting=report_sorting(args, DATE_FIELD),
    )
    return {"total": result["total"], "transactions": renamed(result["rows"], FIELDS)}
