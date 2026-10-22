"""Pirate Ship's web GraphQL, recorded 18.10.2026.

Every operation is a persisted query: the page sends only its name and the sha256 of the query text, and
the server runs the stored query. The hashes come from the web app's bundle and change only when Pirate
Ship changes that query; then the answer is PersistedQueryNotFound and the hash here needs a new recording.
Money is in US dollars as numbers, weights in ounces, sizes in inches.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.pirate_ship.operations import HASHES

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext

WEB = "https://ship.pirateship.com"
GRAPHQL = f"{WEB}/api/graphql"


def _extensions(operation: str) -> dict[str, Any]:
    return {"persistedQuery": {"version": 1, "sha256Hash": HASHES[operation]}}


def persisted_url(operation: str) -> str:
    """The same persisted query as a GET, for the session check and keep-alive."""
    query = {
        "operationName": operation,
        "variables": "{}",
        "extensions": json.dumps(_extensions(operation), separators=(",", ":")),
    }
    return f"{GRAPHQL}?{urlencode(query)}"


async def graphql(
    ctx: ToolContext, operation: str, variables: dict[str, Any] | None = None, *, refusals: bool = False
) -> dict[str, Any]:
    """`data` and `errors` of one operation. Errors that come with data (a carrier without a rate) stay with the
    caller; with refusals=True so does an answer without data, whose errors carry the reason in `extensions`
    (address correction, payment failure)."""
    payload = {"operationName": operation, "variables": variables or {}, "extensions": _extensions(operation)}
    response = await ctx.call(
        "POST",
        f"{GRAPHQL}?opname={operation}",
        json=payload,
        headers={"content-type": "application/json", "origin": WEB, "referer": f"{WEB}/ship"},
    )
    if response.status >= 400:
        raise ToolError(f"Pirate Ship answered {response.status}.", ErrorCode.TARGET_ERROR)
    body = response.json()
    errors = body.get("errors") or []
    if any((item.get("message") or "") == "PersistedQueryNotFound" for item in errors):
        raise ToolError("Pirate Ship changed its app; this tool needs an update.", ErrorCode.TARGET_ERROR)
    data = body.get("data")
    if data is None and not refusals:
        message = next((item.get("message") for item in errors if item.get("message")), None)
        raise ToolError(message or "Pirate Ship returned no data.", ErrorCode.TARGET_ERROR)
    return {"data": data or {}, "errors": errors}


async def user(ctx: ToolContext) -> dict[str, Any] | None:
    return (await graphql(ctx, "UserQuery"))["data"].get("user")
