"""Get account balance: the Reports page's balance and pending refunds and returns."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "balance_usd": 42.17,
    "balance_settled_usd": 40.0,
    "payment_methods": 1,
    "pending_refunds": {"count": 1, "amount_usd": 8.32},
    "pending_returns": {"count": 0, "amount_usd": 0},
    "last_30_days": {"labels": 12, "label_total_usd": 96.4, "label_average_usd": 8.03, "payments_usd": 100.0},
}


@tool(
    name="get_account_balance",
    title="Get account balance",
    access="read",
    confirm=False,
    description="Account Balance, Pending Refunds and Pending Returns from the Reports page.",
    details=(
        "The Pirate Ship account balance in US dollars (balance_settled_usd leaves out payments still "
        "settling), how many payment methods are saved, refunds and return labels still pending, and the "
        "last 30 days of labels as the Reports page shows them: label count, total, average and payments."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /balance",
    example_response=EXAMPLE_RESPONSE,
)
async def get_account_balance(ctx: ToolContext, args: dict[str, Any]) -> Any:
    company = (await graphql(ctx, "ReportsPageQuery"))["data"].get("company") or {}
    today = datetime.now(ZoneInfo(ctx.profile.timezone)).date()
    window = {"startDatetime": (today - timedelta(days=30)).isoformat(), "endDatetime": today.isoformat()}
    numbers = (await graphql(ctx, "NumbersQuery", {"datetimeRange": window}))["data"].get("numbers") or {}
    pending = numbers.get("pendingNumbers") or {}

    def summary(key: str) -> dict[str, Any]:
        item = pending.get(key) or {}
        return {"count": item.get("count", 0), "amount_usd": item.get("amount", 0)}

    return {
        "balance_usd": company.get("accountBalance"),
        "balance_settled_usd": company.get("accountBalanceExcludingUnsettledPayments"),
        "payment_methods": len(company.get("paymentSources") or []),
        "pending_refunds": summary("refunds"),
        "pending_returns": summary("returns"),
        "last_30_days": {
            "labels": numbers.get("netLabelCount", 0),
            "label_total_usd": numbers.get("netLabelTotal", 0),
            "label_average_usd": numbers.get("netLabelAverage", 0),
            "payments_usd": numbers.get("payments", 0),
        },
    }
