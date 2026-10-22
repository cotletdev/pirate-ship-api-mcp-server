"""Get shipping stats: the charts and numbers of Pirate Ship's Reports page for one date range.

The page asks each chart separately with the same {startDatetime, endDatetime} (days, inclusive). Day charts
come as parallel `labels` ("9/18/26") and `charts` lists; "No Data" is the pie chart of an empty range.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.core.tools import tool
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

MAX_DAYS = 366

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "from_date": {"type": "string", "format": "date", "description": "First day, YYYY-MM-DD. Default 30 days ago."},
        "to_date": {
            "type": "string",
            "format": "date",
            "description": "Last day, YYYY-MM-DD, included. Default today.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "from_date": "2026-09-18",
    "to_date": "2026-10-18",
    "labels": {
        "count": 12,
        "total_usd": 96.4,
        "average_usd": 8.03,
        "average_domestic_usd": 8.03,
        "average_international_usd": 0,
    },
    "payments_usd": 100.0,
    "carrier_adjustments_usd": 1.26,
    "savings_usd": 151.2,
    "pending_refunds": {"count": 1, "amount_usd": 8.32},
    "pending_returns": {"count": 0, "amount_usd": 0},
    "tracking": {"new": 1, "in_transit": 3, "delivered": 8, "delivery_issue": 0},
    "auto_refunded": {"count": 0, "amount_usd": 0},
    "by_day": [{"date": "2026-10-16", "labels": 3, "average_cost_usd": 7.12, "payments_usd": 50.0}],
    "by_carrier": [{"label": "USPS", "percent": 75.0}, {"label": "UPS", "percent": 25.0}],
    "by_zone": [{"zone": "Zone 4", "labels": 6}],
    "by_state": [{"state": "NY", "name": "New York", "labels": 4, "percent": 33.3, "total_usd": 27.4}],
    "by_country": [{"country": "US", "name": "United States", "labels": 12, "percent": 100.0, "total_usd": 96.4}],
}


def _range(ctx: ToolContext, args: dict[str, Any]) -> tuple[date, date]:
    today = datetime.now(ZoneInfo(ctx.profile.timezone)).date()
    try:
        end = date.fromisoformat(args["to_date"]) if args.get("to_date") else today
        start = date.fromisoformat(args["from_date"]) if args.get("from_date") else end - timedelta(days=30)
    except ValueError as error:
        raise ToolError("from_date and to_date must be YYYY-MM-DD.", ErrorCode.INVALID_INPUT) from error
    if start > end or (end - start).days > MAX_DAYS:
        raise ToolError(f"from_date must be before to_date and at most {MAX_DAYS} days apart.", ErrorCode.INVALID_INPUT)
    return start, end


def _day(label: str) -> str:
    try:
        return datetime.strptime(label, "%m/%d/%y").date().isoformat()
    except ValueError:
        return label


def _series(chart: dict[str, Any]) -> dict[str, Any]:
    """One day chart as {date: value}; a chart with several series keeps only flat numbers."""
    values = chart.get("charts") or []
    return {_day(label): value for label, value in zip(chart.get("labels") or [], values, strict=False)}


def _amount(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {"count": item.get("count", 0), "amount_usd": item.get("amount", 0)}


def _distribution(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [
        {
            key: item.get("key"),
            "name": item.get("name"),
            "labels": item.get("count"),
            "percent": item.get("percent"),
            "total_usd": item.get("price"),
        }
        for item in items
    ]


@tool(
    name="get_shipping_stats",
    title="Get shipping stats",
    access="read",
    confirm=False,
    description="Labels, spend, savings, tracking and where packages went for a date range, as on Reports.",
    details=(
        "Everything the Reports page charts for a date range (default the last 30 days, at most a year): "
        "label count, total and average cost (domestic and international), payments, carrier adjustments, "
        "savings against retail, pending refunds and returns, tracking states, labels and average cost per "
        "day, the carrier split, labels per zone and per US state and country. Money is in US dollars."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /stats",
    example_response=EXAMPLE_RESPONSE,
    timeout_s=60,
)
async def get_shipping_stats(ctx: ToolContext, args: dict[str, Any]) -> Any:
    start, end = _range(ctx, args)
    window = {"datetimeRange": {"startDatetime": start.isoformat(), "endDatetime": end.isoformat()}}

    async def ask(operation: str, field: str) -> Any:
        return (await graphql(ctx, operation, window))["data"].get(field)

    numbers = await ask("NumbersQuery", "numbers") or {}
    pending = numbers.get("pendingNumbers") or {}
    tracking = await ask("ShipmentTrackingNumbersQuery", "shipmentTrackingNumbers") or {}
    labels = _series(await ask("ShipmentChartQuery", "shipmentChart") or {})
    costs = _series(await ask("AverageCostChartQuery", "averageCostChart") or {})
    payments = _series(await ask("PaymentChartQuery", "paymentChart") or {})
    pie = await ask("ShipmentPieChartQuery", "shipmentPieChart") or {}
    zones = await ask("ZoneChartQuery", "zoneChart") or {}
    states = await ask("StateDistributionChartQuery", "stateDistributionChart") or {}
    countries = await ask("CountryDistributionChartQuery", "countryDistributionChart") or {}
    savings = await ask("CompanySavingsQuery", "companySavings")
    refunded = (await graphql(ctx, "AutoRefundedShipmentsSummaryQuery"))["data"].get("autoRefundedShipmentsSummary")

    return {
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "labels": {
            "count": numbers.get("netLabelCount", 0),
            "total_usd": numbers.get("netLabelTotal", 0),
            "average_usd": numbers.get("netLabelAverage", 0),
            "average_domestic_usd": numbers.get("netLabelAverageDom", 0),
            "average_international_usd": numbers.get("netLabelAverageInt", 0),
        },
        "payments_usd": numbers.get("payments", 0),
        "carrier_adjustments_usd": numbers.get("carrierAdjustmentsAmount", 0),
        "savings_usd": savings or 0,
        "pending_refunds": _amount(pending.get("refunds")),
        "pending_returns": _amount(pending.get("returns")),
        "tracking": {
            "new": tracking.get("shipmentsNew", 0),
            "in_transit": tracking.get("shipmentsTransit", 0),
            "delivered": tracking.get("shipmentsDelivered", 0),
            "delivery_issue": tracking.get("shipmentsDeliveryIssue", 0),
        },
        "auto_refunded": _amount(refunded),
        "by_day": [
            {"date": day, "labels": count, "average_cost_usd": costs.get(day), "payments_usd": payments.get(day)}
            for day, count in labels.items()
            if count or costs.get(day) or payments.get(day)
        ],
        "by_carrier": [
            {"label": label, "percent": value}
            for label, value in zip(pie.get("labels") or [], pie.get("charts") or [], strict=False)
            if label != "No Data"
        ],
        "by_zone": [
            {"zone": label, "labels": value}
            for label, value in zip(zones.get("labels") or [], zones.get("charts") or [], strict=False)
            if value
        ],
        "by_state": _distribution(states.get("stateDistributions") or [], "state"),
        "by_country": _distribution(countries.get("countryDistributions") or [], "country"),
    }
