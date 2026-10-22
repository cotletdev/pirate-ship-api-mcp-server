"""Spreadsheet upload: the web app's "Upload a Spreadsheet" posts a CSV to /api/upload as multipart and
gets back an upload id that the GraphQL batch mutations take. Recorded 18.10.2026.
"""

from __future__ import annotations

import csv
import io
import secrets
from typing import TYPE_CHECKING, Any

from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError
from pirate_ship_api_mcp.pirate_ship.client import WEB

if TYPE_CHECKING:
    from pirate_ship_api_mcp.core.context import ToolContext


def to_csv(header: list[str], rows: list[list[Any]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(["" if value is None else value for value in row] for row in rows)
    return out.getvalue()


async def upload_csv(ctx: ToolContext, text: str, filename: str = "shipments.csv") -> dict[str, Any]:
    """Uploads one CSV and returns Pirate Ship's answer (with the upload id)."""
    boundary = f"----WebKitFormBoundary{secrets.token_hex(8)}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: text/csv\r\n\r\n"
        f"{text}\r\n"
        f"--{boundary}--\r\n"
    )
    response = await ctx.call(
        "POST",
        f"{WEB}/api/upload",
        data=body,
        headers={
            "content-type": f"multipart/form-data; boundary={boundary}",
            "origin": WEB,
            "referer": f"{WEB}/upload/new",
        },
    )
    if response.status >= 400:
        raise ToolError(f"Pirate Ship refused the spreadsheet ({response.status}).", ErrorCode.TARGET_ERROR)
    return response.json()
