"""Everything the server knows about Pirate Ship outside `pirate_ship/`: names, domains and the session cookie.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Pirate Ship"
SLUG = "pirate-ship"
# The command and the prefix of every environment variable (PIRATE_SHIP_AUTH_TOKEN, PIRATE_SHIP_MCP_TOKEN ...).
CLI = "pirate-ship-mcp"
ENV = "PIRATE_SHIP"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome.
DOMAINS = ("pirateship.com",)
# Present only while signed in. The first is the cookie a pasted token sets.
SESSION_COOKIES = ("pirate_id_f0fecf84",)
COOKIE_DOMAIN = "ship.pirateship.com"
LOGIN_URL = "https://ship.pirateship.com/"
# A final URL with one of these means the app signed the session out.
LOGGED_OUT_MARKERS = ("/login",)
# Pirate Ship answers every call on one GraphQL path, so no account path to refuse here: the allowlist of
# operations in pirate_ship/operations.py leaves out account, payment and identity operations instead.
ACCOUNT_PATHS: tuple[str, ...] = ()
# A 401 or 403 body with one of these means "sign in again before this action". Pirate Ship has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/pirate-ship"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = (
    "Start with get_account_balance and list_ship_from_addresses; get_rates quotes a package without saving anything."
)
