# AGENTS.md

You are an AI agent in a clone of this repo. It is a self-hosted Pirate Ship API and MCP server: 51 tools that work in the user's own Pirate Ship account, through the session of their own Google Chrome. Your usual job is one of three: set it up for the user, use its tools for them, or change its code. Human docs: `README.md`.

## Before you start

- The license allows noncommercial use only (PolyForm Noncommercial 1.0.0, `LICENSE`). If the user is setting this up for a company, a team or clients, say so and point to the hosted version at https://cotlet.dev/integrations/pirate-ship-api-mcp-server. Do not continue the setup for that use.
- Every tool acts as the user on Pirate Ship. Tools with access `write` create or delete drafts, addresses, packages and templates, or change settings. Tracking email settings and templates change what the user's customers receive.
- No tool here buys a label, refunds one, books a pickup or disputes a charge. The user does those in Pirate Ship. Do not add them back.

## Set it up for the user

Do the steps yourself. Ask the user only for what needs their hands in Chrome.

1. Check Python: `python3 --version` must be 3.11 or newer.
2. Install in the repo root:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e .
   .venv/bin/pirate-ship-mcp --version
   ```

   On Windows the path is `.venv\Scripts\pirate-ship-mcp`. With uv: `uv venv && uv pip install -e .`.
3. Ask the user to do two things in Chrome. You cannot open `chrome://` pages for them.
   - Open `chrome://inspect/#remote-debugging` and switch remote debugging on.
   - Be signed in at https://ship.pirateship.com, with "Stay signed in" ticked.
4. Run `.venv/bin/pirate-ship-mcp connect`. Tell the user to click **Allow** when Chrome asks about the connection. Success prints `Signed in to Pirate Ship as <name> (<email>)`.
5. Check: `.venv/bin/pirate-ship-mcp status`, then `.venv/bin/pirate-ship-mcp call get_account_balance`.
6. Add the MCP server to the user's client. Use the absolute path of `.venv/bin/pirate-ship-mcp`:
   - Claude Code: `claude mcp add pirate-ship -- <abs path>/.venv/bin/pirate-ship-mcp mcp`
   - Claude Desktop, Cursor, Codex: the config blocks in `README.md`, section "MCP server".
   - Add `--read-only` after `mcp` if the user only wants to read.
   The client loads new MCP servers on its next start. Tell the user.

If step 4 fails:

| Message | What to do |
|---|---|
| `Chrome remote debugging is off` | Step 3 is not done, or Chrome is Beta, Canary or a custom profile: pass `--profile-dir "<profile folder>"`. |
| `Could not connect to Chrome` | The user did not click Allow, or Chrome is closed. Run `connect` again. |
| `This Chrome is not signed in to Pirate Ship` | The user signs in at ship.pirateship.com in that Chrome, then run `connect` again. |
| No Chrome on this machine (a server) | The user copies the `pirate_id_f0fecf84` cookie from Chrome DevTools (Application, Cookies, https://ship.pirateship.com) and runs `pirate-ship-mcp connect --token` themselves. Never ask them to paste the cookie into the chat. It lasts about a day without use. |

## Use the tools

- With the MCP server added, call its tools. Without it: `.venv/bin/pirate-ship-mcp call <tool> key=value ...`, or one JSON object as the argument.
- `.venv/bin/pirate-ship-mcp tools` lists every tool with access and route. `tools --json` adds the input schemas.
- Start with `get_account_balance` and `list_ship_from_addresses`. `get_rates` quotes a package and saves nothing. `list_saved_packages` gives the `package_preset_id` that batches take.
- Money is in US dollars, weights in ounces, sizes in inches. Dates are in Chrome's time zone, read at `connect`.
- Report lists (`list_shipments`, `list_transactions` ...) take `limit` and `offset` and answer with `total`.
- A draft from `create_shipment` or `create_batch` costs nothing. Descriptions say "buy it with buy_label": that tool is not in this repo, so tell the user to buy the draft in Pirate Ship.
- Before a `write` tool, show the user what you will change and get their OK.
- For a script or a cron job, use `pirate_ship_api_mcp.scripting` (`call`, `paginate_offset`, `write_rows`) and the scripts in `examples/` as models.
- For a REST API (n8n, other languages): `.venv/bin/pirate-ship-mcp serve`, routes under `http://127.0.0.1:8787/api/v1/pirate-ship`, docs at `/docs`.

Errors come as `<code>: <message>`. `auth_expired` means Pirate Ship signed the session out: the user signs in again in Chrome and you run `connect`. "Pirate Ship changed its app" means a recorded GraphQL hash is out of date: tell the user to `git pull`, or report it. More codes: `README.md`, section "Errors".

## Keep secrets out

- `~/.config/pirate-ship-api-mcp/session.json` and `PIRATE_SHIP_AUTH_TOKEN` give full access to the user's Pirate Ship account. Never print, log, commit or copy their content.
- `serve` listens on 127.0.0.1. Never start it on another address without `PIRATE_SHIP_MCP_TOKEN`.

## Change the code

| Path | What | Edit? |
|---|---|---|
| `pirate_ship_api_mcp/pirate_ship/` | the Pirate Ship tools, one file per tool in `tools/`; `client.py` sends one GraphQL operation, `operations.py` is the allowlist of operations and their hashes, `batches.py` and `grids.py` hold shared batch and report code | Yes for a local fix, but the next `git pull` brings our version of these files. Report the bug at https://github.com/cotletdev/pirate-ship-api-mcp-server/issues |
| `pirate_ship_api_mcp/app.py` | app name, domains, session cookie, REST prefix | Rarely |
| `pirate_ship_api_mcp/core/` | `@tool` declaration, errors, the account guard, the HTTP client with the session (`context.py`) | Yes |
| `pirate_ship_api_mcp/session.py` | reading cookies and the time zone from Chrome over CDP, the session file | Yes |
| `pirate_ship_api_mcp/runner.py`, `api.py`, `mcp_server.py`, `mcp_context.py`, `cli.py` | tool registry, REST API, MCP server, its prompts and resources, command line | Yes |
| `examples/` | scripts for common jobs | Yes |

A new tool is a new file in `pirate_ship_api_mcp/pirate_ship/tools/` with a `@tool(...)` declaration (name, access, input schema, `route`). The registry finds it, and the REST API, the MCP server and the CLI show it without other changes. A new GraphQL operation also needs its name and sha256 in `operations.py`.

There is no test suite. After a change, run `.venv/bin/pirate-ship-mcp tools` and one read tool against the user's account.
