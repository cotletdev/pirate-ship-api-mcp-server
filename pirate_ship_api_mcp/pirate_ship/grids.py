"""Pirate Ship's report tables (DataGrid): one *GridRowsQuery per report, the same paging, search and filters.

A row is a dict keyed by the grid's column fields (e.g. tracking_nr, client_price, status). Filters are
{field, operator, values}, sorting {field, direction}: the grid's own shape, recorded 18.10.2026.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.pirate_ship.client import graphql

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

PAGING_SCHEMA: dict[str, Any] = {
    "search": {"type": "string", "maxLength": 200, "description": "Free text, as in the report's search box."},
    "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 25,
        "description": "Rows per page, 1 to 100.",
    },
    "offset": {
        "type": "integer",
        "minimum": 0,
        "default": 0,
        "description": "Rows to skip: the next page starts at offset + limit while it is below total.",
    },
}


DATE_SCHEMA: dict[str, Any] = {
    "from_date": {"type": "string", "format": "date", "description": "First day, YYYY-MM-DD, in your timezone."},
    "to_date": {"type": "string", "format": "date", "description": "Last day, YYYY-MM-DD, included."},
    "sort": {"type": "string", "enum": ["newest", "oldest"], "default": "newest", "description": "Order by date."},
}


def values_schema(description: str) -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string", "maxLength": 100}, "maxItems": 20, "description": description}


def report_filters(ctx: ToolContext, args: dict[str, Any], date_field: str, lists: dict[str, str]) -> list[dict]:
    """The grid's filters: gte/lte on date_field (UTC instants of local midnights), `in` for each list."""
    zone = ZoneInfo(ctx.profile.timezone)
    filters = []
    for key, operator, at in (("from_date", "gte", time.min), ("to_date", "lte", time.max)):
        if not args.get(key):
            continue
        try:
            day = date.fromisoformat(args[key])
        except ValueError as error:
            raise ToolError(f"{key} must be YYYY-MM-DD.", ErrorCode.INVALID_INPUT) from error
        instant = datetime.combine(day, at, zone).astimezone(ZoneInfo("UTC"))
        filters.append(
            {"field": date_field, "operator": operator, "values": [instant.isoformat(timespec="milliseconds")]}
        )
    for key, field in lists.items():
        if args.get(key):
            filters.append({"field": field, "operator": "in", "values": [str(value) for value in args[key]]})
    return filters


def report_sorting(args: dict[str, Any], date_field: str) -> list[dict[str, str]]:
    return [{"field": date_field, "direction": "ASC" if args.get("sort") == "oldest" else "DESC"}]


def renamed(rows: list[dict[str, Any]], fields: dict[str, str]) -> list[dict[str, Any]]:
    """Grid rows with the report's column keys turned into the tool's names."""
    return [{name: row.get(field) for field, name in fields.items()} for row in rows]


async def grid_rows(
    ctx: ToolContext,
    operation: str,
    root: str,
    args: dict[str, Any],
    filters: list[dict[str, Any]] | None = None,
    sorting: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rows of one report: {"total": n, "rows": [...]}; no rows is an empty list."""
    variables = {
        "searchTerm": args.get("search") or "",
        "filters": filters or [],
        "sorting": sorting or [],
        "limit": args.get("limit", 25),
        "offset": args.get("offset", 0),
        **(extra or {}),
    }
    data = (await graphql(ctx, operation, variables))["data"].get(root) or {}
    rows = data.get("rows") or {}
    return {"total": rows.get("totalCount", 0), "rows": [_clean(node) for node in rows.get("nodes") or []]}


def _clean(node: Any) -> Any:
    """Drops the grid's UI-only cells (checkbox, action buttons)."""
    if not isinstance(node, dict):
        return node
    return {key: value for key, value in node.items() if key not in ("selectable", "row_actions", "__typename")}


async def grid_export(ctx: ToolContext, operation: str, root: str, variables: dict[str, Any]) -> dict[str, Any]:
    """The Export button: the first call starts a CSV, the same call with its exportId every two seconds
    until the file is downloadable. A table with no rows answers "There is no data for this grid"."""
    variables = dict(variables)
    for _ in range(30):
        try:
            data = (await graphql(ctx, operation, variables))["data"]
        except ToolError as error:
            if "no data" in str(error).lower():
                return {"url": None, "filename": None, "empty": True}
            raise
        export = (data.get(root) or {}).get("exportUrl") or {}
        if export.get("downloadable") and export.get("url"):
            return {"url": export["url"], "filename": export.get("filename"), "empty": False}
        variables["exportId"] = export.get("exportId")
        await asyncio.sleep(2)
    raise ToolError("Pirate Ship is still building the export; try again in a minute.", ErrorCode.TIMEOUT)
