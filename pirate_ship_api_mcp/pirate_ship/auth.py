"""Who is signed in: Pirate Ship's UserQuery, for "Signed in as ..."."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pirate_ship_api_mcp.core.errors import AuthExpiredError
from pirate_ship_api_mcp.pirate_ship.client import user

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext


async def whoami(ctx: ToolContext) -> str | None:
    """None only when Pirate Ship says signed out; any other failure raises (detection tries again later)."""
    try:
        me = await user(ctx)
    except AuthExpiredError:
        return None
    if not me:
        return None
    name = " ".join(part for part in (me.get("firstName"), me.get("lastName")) if part).strip()
    email = me.get("email")
    return f"{name} ({email})" if name and email else name or email or None
