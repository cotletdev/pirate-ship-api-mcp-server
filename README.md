# Pirate Ship API and MCP server, self-hosted

<!-- mcp-name: dev.cotlet/pirate-ship -->

A **Pirate Ship API** and a **Pirate Ship MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. 51 of the 57 Pirate Ship tools we run in production at [Cotlet](https://cotlet.dev/integrations/pirate-ship-api-mcp-server): USPS and UPS rates, draft labels and batches, label downloads, SCAN Forms, shipments and tracking, reports, store order import, Ship From Addresses, Saved Packages, tracking emails and label settings. The six tools that spend or refund money are [not in this version](#not-in-this-version).

Pirate Ship has no public API and no official MCP server. This repo gives you both:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/pirate-ship`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("get_rates", to_zip="10001", weight_oz=16)`, plus 11 ready scripts in [`examples/`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/).

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when Pirate Ship changes its app, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/pirate-ship-api-mcp-server).

[![Pirate Ship MCP server](https://img.shields.io/badge/Pirate%20Ship%20MCP-51%20tools-6d4aef)](#all-51-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/LICENSE)
[![MCP Badge](https://lobehub.com/badge/mcp/cotletdev-pirate-ship-api-mcp-server)](https://lobehub.com/mcp/cotletdev-pirate-ship-api-mcp-server)

```bash
git clone https://github.com/cotletdev/pirate-ship-api-mcp-server.git && cd pirate-ship-api-mcp-server
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
pirate-ship-mcp connect                            # reads your Pirate Ship session from Chrome
pirate-ship-mcp call get_rates to_zip=10001 weight_oz=16
claude mcp add pirate-ship -- "$PWD/.venv/bin/pirate-ship-mcp" mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 51 tools](#all-51-tools)
- [Configuration](#configuration)
- [Security and your Pirate Ship account](#security-and-your-pirate-ship-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ pirate-ship-mcp on your computer ──your cookies──▶ ship.pirateship.com
                                                     ▲
                       pirate-ship-mcp connect ──────┘ reads them once from your Chrome (DevTools Protocol)
```

1. You sign in to Pirate Ship in your own Chrome, the way you always do.
2. `pirate-ship-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the pirateship.com cookies and Chrome's time zone, and saves them to `~/.config/pirate-ship-api-mcp/session.json`, readable by your user only. It never sees or stores your password.
3. Every tool call is one of the GraphQL operations Pirate Ship's own web app sends to `ship.pirateship.com/api/graphql`, with those cookies, sent with [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No headless browser runs.

Pirate Ship's web app sends each operation as a persisted query: its name and the sha256 of the query text. The tools may send only the operations listed in [`operations.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/pirate_ship_api_mcp/pirate_ship/operations.py), and account, password, payment method and identity operations are not on that list. When Pirate Ship changes one of the listed queries, the tool answers "Pirate Ship changed its app" until we record the new hash.

Pirate Ship's session cookie lives about a day and is renewed by use. When Pirate Ship signs you out, the server reads the cookies from Chrome again, if Chrome is open with remote debugging on. Tick "Stay signed in" when you sign in, so Chrome keeps you signed in between visits.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in to Pirate Ship. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows.
- A Pirate Ship account with a Ship From Address. Rates, drafts, reports and settings need nothing else. Buying labels needs Account Balance or a payment method, and you buy in Pirate Ship itself.

## Install

```bash
git clone https://github.com/cotletdev/pirate-ship-api-mcp-server.git
cd pirate-ship-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
pirate-ship-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run pirate-ship-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `git pull && pip install -e .`. We copy every change of the hosted Pirate Ship tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Make sure you are signed in at [ship.pirateship.com](https://ship.pirateship.com).
3. Run:

   ```bash
   pirate-ship-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 32 Pirate Ship cookies to /Users/you/.config/pirate-ship-api-mcp/session.json
Signed in to Pirate Ship as Linda Morales (linda@example.com)
```

Leave remote debugging on if you want the server to pick up a new session by itself after Pirate Ship signs you out. With a one-day cookie, that happens more often than with most apps.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to Pirate Ship there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-pirate-ship"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-pirate-ship"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-pirate-ship"

pirate-ship-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel.

### Option C: paste the cookie by hand

For a server with no Chrome: in Chrome open DevTools on ship.pirateship.com, **Application > Cookies > https://ship.pirateship.com**, copy the value of `pirate_id_f0fecf84`, then:

```bash
pirate-ship-mcp connect --token          # paste it, input is hidden
# or, without a session file:
export PIRATE_SHIP_AUTH_TOKEN=...
```

A pasted cookie is not refreshed on its own, and this one lasts about a day without use. Paste a new one when Pirate Ship signs you out.

Check the session at any time:

```bash
pirate-ship-mcp status
```

## MCP server

The MCP server lists every tool with its input schema, a description written for agents, and hints: read tools are marked read-only, and tools that delete something or change what your recipients get are marked so your client asks before running them.

### Claude Code

```bash
claude mcp add pirate-ship -- /path/to/pirate-ship-api-mcp-server/.venv/bin/pirate-ship-mcp mcp
# read only:
claude mcp add pirate-ship -- /path/to/pirate-ship-api-mcp-server/.venv/bin/pirate-ship-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pirate-ship": {
      "command": "/path/to/pirate-ship-api-mcp-server/.venv/bin/pirate-ship-mcp",
      "args": ["mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.pirate-ship]
command = "/path/to/pirate-ship-api-mcp-server/.venv/bin/pirate-ship-mcp"
args = ["mcp"]
```

### Over HTTP

`pirate-ship-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
pirate-ship-mcp serve
claude mcp add --transport http pirate-ship http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *What does a 2 lb box, 12x10x6, cost to ZIP 94103 with USPS and UPS? Cheapest first.*
>
> *Make a draft batch from orders.csv with my "Small box" Saved Package and show me the rates per group.*
>
> *Which labels from the last 10 days still have no carrier scan?*
>
> *How much did I spend on labels in October, and what were the carrier adjustments?*

## REST API

```bash
pirate-ship-mcp serve              # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/pirate-ship`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments, and a JSON body adds the rest.

```bash
curl 'http://127.0.0.1:8787/api/v1/pirate-ship/balance'
curl 'http://127.0.0.1:8787/api/v1/pirate-ship/rates?to_zip=10001&weight_oz=16&length_in=10&width_in=8&height_in=4'
curl 'http://127.0.0.1:8787/api/v1/pirate-ship/shipments?from_date=2026-10-01&limit=50'
curl -X POST http://127.0.0.1:8787/api/v1/pirate-ship/shipments \
  -H 'Content-Type: application/json' \
  -d '{"full_name": "Linda Morales", "address1": "350 5th Ave", "city": "New York", "state": "NY", "zip": "10118", "weight_oz": 20}'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/pirate-ship/tools/list_shipments -d '{"carrier": ["UPS"]}'
```

- `GET /api/v1/pirate-ship/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. Report lists take `limit` and `offset` and answer with `total`.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
PIRATE_SHIP_MCP_TOKEN=$(openssl rand -hex 24) pirate-ship-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from pirate_ship_api_mcp import call
from pirate_ship_api_mcp.scripting import paginate_offset, write_rows

rates = call("get_rates", to_zip="10001", weight_oz=16, length_in=10, width_in=8, height_in=4)["rates"]
shipments = list(paginate_offset("list_shipments", {"from_date": "2026-10-01"}, "shipments"))
write_rows(shipments, "october.csv")
call("create_shipment", full_name="Linda Morales", address1="350 5th Ave", city="New York", zip="10118", weight_oz=20)
```

Or one tool from the shell: `pirate-ship-mcp call list_shipments limit=10`, or with a JSON object.

Ready scripts in [`examples/`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/). Each prints JSON or a short report, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`:

| Script | What it does |
|---|---|
| [`compare_rates.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/compare_rates.py) | USPS and UPS rates for one package, cheapest first. `--size 10x8x4`, `--country`. |
| [`draft_batch_from_csv.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/draft_batch_from_csv.py) | A CSV of recipients becomes one unpaid draft batch with a Saved Package; prints the rate of each group. Rows without an address are listed, not guessed. |
| [`store_orders.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/store_orders.py) | Refreshes your connected stores and lists the orders waiting to ship. |
| [`export_shipments.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/export_shipments.py) | Bought labels to CSV or JSON: recipient, tracking number, service, cost, status. `--since`, `--carrier`. |
| [`tracking_report.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/tracking_report.py) | Labels of the last N days that are not delivered, with the last event and a `stuck` flag. |
| [`refund_candidates.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/refund_candidates.py) | Duplicate labels and labels with no carrier scan in the 28-day refund window. Lists them; you refund in Pirate Ship. |
| [`scan_form.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/scan_form.py) | The USPS SCAN Form for today's labels, as a PDF link. |
| [`pickup_quote.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/pickup_quote.py) | Today's packages and weight per carrier, with the pickup price. Books nothing. |
| [`carrier_adjustments.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/carrier_adjustments.py) | Carrier adjustments with the weight and size you entered next to what the carrier measured. |
| [`spend_report.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/spend_report.py) | Labels, spend, savings, carrier split, top states and balance for a date range. `--transactions` saves every charge. |
| [`ship_from_addresses.py`](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/examples/ship_from_addresses.py) | Your Ship From Addresses and Saved Packages with the ids other tools take. |

```bash
python examples/compare_rates.py --to-zip 94103 --weight-oz 32 --size 12x10x6
python examples/draft_batch_from_csv.py orders.csv --title "Wholesale 19 Oct" --package "Small box"
```

On a schedule, cron on your own computer works while it is on: `0 18 * * 1-5 cd ~/pirate-ship-api-mcp-server && .venv/bin/python examples/tracking_report.py --days 10 --out late.csv`.

## All 51 tools

Money is in US dollars, weights in ounces, sizes in inches, dates in Chrome's time zone. `pirate-ship-mcp tools` prints this list, `pirate-ship-mcp tools --json` adds the input schemas.

### Rates and addresses

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_rates` | read | `GET /rates` | USPS and UPS services with price for one package, cheapest first. |
| `parse_address` | read | `GET /addresses/parse` | Splits a pasted address into name, street, city, state, ZIP and country. |
| `search_recipients` | read | `GET /recipients/search` | Past recipients' addresses matching a name, email or phone. |
| `list_package_types` | read | `GET /package-types` | Packaging types per carrier (box, envelope, flat rate) and the size and weight limits. |

### Draft labels and batches

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `create_shipment` | write | `POST /shipments` | Unpaid draft label for one package with every rate; buy it in Pirate Ship. |
| `create_batch` | write | `POST /batches` | Unpaid draft batch for many packages with the rates of each rate group; buy it in Pirate Ship. |
| `create_batch_from_orders` | write | `POST /batches/from-orders` | Turns store orders into a batch of shipments with one saved package; nothing is bought. |
| `get_batch` | read | `GET /batches/{batch_id}` | A draft or bought batch: shipments, tracking, rates to buy, what can be refunded. |
| `list_batches` | read | `GET /batches` | Latest batches and single labels, newest first, with status and tracking counts. |
| `change_ship_date` | write | `PUT /batches/{batch_id}/ship-date` | Moves a draft batch to another ship date and returns its new rates. |
| `rename_batch` | write | `PATCH /batches/{batch_id}` | Changes a batch's title. |
| `delete_batch` | write | `DELETE /batches/{batch_id}` | Deletes an unpaid draft batch or single shipment. |

### Printing and SCAN Forms

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `download_labels` | read | `GET /labels` | A download link for the printable labels of a batch or of chosen shipments. |
| `create_scan_form` | write | `POST /scan-forms` | USPS End of Day SCAN Form for the labels of one Ship Date, as a PDF link. |
| `list_scan_forms` | read | `GET /scan-forms` | USPS SCAN Forms per Ship From Address, with their PDF links and labels still without one. |

### Shipments and tracking

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_shipments` | read | `GET /shipments` | Labels bought in Pirate Ship with recipient, tracking, cost and status, newest first. |
| `get_shipment` | read | `GET /shipments/{shipment_id}` | One shipment with tracking, service, cost, recipient and carrier adjustments. |
| `export_shipments` | read | `GET /shipments/export` | A CSV of the shipments report with every column, as a download link. |

### Reports, balance and refunds

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_account_balance` | read | `GET /balance` | Account Balance, Pending Refunds and Pending Returns from the Reports page. |
| `get_shipping_stats` | read | `GET /stats` | Labels, spend, savings, tracking and where packages went for a date range, as on Reports. |
| `list_transactions` | read | `GET /transactions` | Every charge, payment and refund on the Pirate Ship balance, newest first. |
| `list_receipts` | read | `GET /receipts` | Payments made to Pirate Ship, newest first; get_receipt shows one. |
| `get_receipt` | read | `GET /receipts/{receipt_id}` | One payment to Pirate Ship with its billing address and the labels it paid for. |
| `list_refunds` | read | `GET /refunds` | Label refunds with their status and amount, newest request first. |
| `list_return_labels` | read | `GET /return-labels` | Pay-on-use return labels and whether a customer used them. |
| `list_carrier_adjustments` | read | `GET /carrier-adjustments` | Extra charges or credits the carrier made after a label was used, with old and actual package. |
| `export_report` | read | `GET /reports/{report}/export` | A CSV of the transactions, refunds, receipts, return labels or carrier adjustments report. |

### Pickups

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_pickup_quote` | read | `GET /pickups/quote` | What a USPS or UPS pickup would cost; USPS pickups are free. Nothing is booked. |
| `list_pickups` | read | `GET /pickups` | Your scheduled and past USPS and UPS pickups with confirmation numbers. |

### Store orders

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_store_connections` | read | `GET /store-connections` | Stores and marketplaces connected to Pirate Ship for order import, with their status. |
| `sync_store_orders` | write | `POST /import-orders/sync` | Pulls new orders from every connected store into Pirate Ship's Import list. |
| `list_import_orders` | read | `GET /import-orders` | Unshipped orders from your connected store integrations, as in the Import grid. |
| `ignore_orders` | write | `POST /import-orders/ignore` | Hides store orders from the Import list without shipping them. |
| `unignore_orders` | write | `DELETE /import-orders/ignore` | Puts ignored store orders back on the Import list. |

### Ship From Addresses

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_ship_from_addresses` | read | `GET /ship-from-addresses` | Your Ship From Addresses with their return addresses; one is the default. |
| `create_ship_from_address` | write | `POST /ship-from-addresses` | Adds a US Ship From Address, optionally with a separate return address. |
| `update_ship_from_address` | write | `PATCH /ship-from-addresses/{address_id}` | Changes a Ship From Address: its name, origin or return address. |
| `set_default_ship_from_address` | write | `PUT /ship-from-addresses/{address_id}/default` | Makes one Ship From Address the default for new shipments and rate quotes. |
| `delete_ship_from_address` | write | `DELETE /ship-from-addresses/{address_id}` | Removes a saved Ship From Address. The default address cannot be removed. |

### Saved Packages

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_saved_packages` | read | `GET /saved-packages` | Your Saved Packages from Settings: size, weight and the extra services stored with each. |
| `create_saved_package` | write | `POST /saved-packages` | Saves a package (type, size, weight, extra services) for reuse on labels. |
| `update_saved_package` | write | `PATCH /saved-packages/{package_id}` | Changes a Saved Package; fields you leave out keep their values. |
| `delete_saved_package` | write | `DELETE /saved-packages/{package_id}` | Removes a Saved Package. Labels made with it are not affected. |

### Tracking emails

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_tracking_email_settings` | read | `GET /tracking-email-settings` | Whether recipients get tracking emails by default, how long after purchase, and the template. |
| `update_tracking_email_settings` | write | `PATCH /tracking-email-settings` | Turns default tracking emails on or off and sets their delay after purchase. |
| `list_email_templates` | read | `GET /email-templates` | Tracking email templates: subject, sender, HTML body; one is the default. |
| `create_email_template` | write | `POST /email-templates` | Adds a tracking email template for the emails recipients get with their tracking link. |
| `update_email_template` | write | `PATCH /email-templates/{template_id}` | Changes a tracking email template; fields you leave out keep their values. |
| `delete_email_template` | write | `DELETE /email-templates/{template_id}` | Removes a tracking email template. |

### Label settings

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_label_settings` | read | `GET /label-settings` | Label size and file format, packing list, logo, QR codes, address correction, export format. |
| `update_label_settings` | write | `PATCH /label-settings` | Changes label size, file format, packing list, logo, QR codes, address correction or export format. |

### Not in this version

| Tool | Why |
|---|---|
| `buy_label` | Spends your Account Balance or charges your card. Buy in Pirate Ship. |
| `refund_label`, `refund_batch` | Refund requests are final and move money. Request them in Pirate Ship. |
| `schedule_pickup`, `cancel_pickup` | A UPS pickup is charged and its cancellation refunded. `get_pickup_quote` and `list_pickups` are here. |
| `dispute_adjustment` | A dispute is about a charge on your balance. `list_carrier_adjustments` is here. |

In tool descriptions "buy it with buy_label" means: buy the draft in Pirate Ship's web app. Never built, on purpose: your Pirate Ship sign-in, email, password, security settings, payment methods, billing and identity checks.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `PIRATE_SHIP_MCP_HOME` | `~/.config/pirate-ship-api-mcp` | Folder of `session.json`. |
| `PIRATE_SHIP_AUTH_TOKEN` | | The `pirate_id_f0fecf84` cookie, instead of `pirate-ship-mcp connect`. |
| `PIRATE_SHIP_PROXY` | | Proxy for every request to Pirate Ship, e.g. `http://user:pass@host:port`. |
| `PIRATE_SHIP_MCP_READ_ONLY` | | `1` hides and refuses every tool that changes Pirate Ship (same as `--read-only`). |
| `PIRATE_SHIP_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `PIRATE_SHIP_MCP_HOST`, `PIRATE_SHIP_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |
| `TZ` | Chrome's zone | Time zone for "today" and date ranges when `connect` could not read Chrome's. |

## Security and your Pirate Ship account

- **Your password never reaches this code.** Only cookies are read, and only those of pirateship.com.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you on Pirate Ship, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `PIRATE_SHIP_MCP_TOKEN`.
- **pirateship.com only.** Requests and redirects outside pirateship.com are refused.
- **No tool moves money.** None buys a label, requests a refund, books a paid pickup or touches your payment methods.
- **Read-only mode.** `--read-only` or `PIRATE_SHIP_MCP_READ_ONLY=1` exposes the 29 read tools only.
- **Some changes reach your recipients.** Tracking email settings and templates change the emails your customers get. MCP clients ask before those tools run; a script does not.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or Pirate Ship signed you out. Sign in to Pirate Ship in Chrome and run `pirate-ship-mcp connect`. |
| 403 | `scope_denied` | The server runs read-only. |
| 403 | `target_blocked` | Pirate Ship refused the request or showed a bot check. Open ship.pirateship.com in Chrome once, then retry. |
| 409 | `captcha_required` | Pirate Ship asks for a CAPTCHA. Solve it in Chrome. |
| 422 | `invalid_input` | An argument is missing or wrong; the message names it. |
| 429 | `rate_limited` | Pirate Ship is limiting the account. Wait a few minutes. |
| 502 | `target_error` | Pirate Ship answered with an error (an unknown id, an address it cannot rate), or changed its app. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/pirate-ship-api-mcp-server/issues). |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/pirate-ship-api-mcp-server) |
|---|---|---|
| Tools | 51 | all 57, with buying, refunds, pickups and disputes |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Pirate Ship session | your Chrome, cookies in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM, kept signed in |
| When Pirate Ship changes its app | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | purchases and refunds wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 20 to 30 credits (25 for most tools), failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does Pirate Ship have an official API?**
No. Pirate Ship has no API, no webhooks and no official MCP server (checked 11 Oct 2026). Its help center says so and points to the built-in store integrations and spreadsheet uploads instead. Details: [cotlet.dev/integrations/pirate-ship-api-mcp-server](https://cotlet.dev/integrations/pirate-ship-api-mcp-server).

**Is there a Pirate Ship MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `pirate-ship-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Pirate Ship MCP server](https://cotlet.dev/integrations/pirate-ship-api-mcp-server) gives you.

**Can I get USPS and UPS rates from a script?**
Yes. `get_rates` returns every service with Pirate Ship's price, the retail price, zone and delivery estimate, cheapest first, and saves nothing: `python examples/compare_rates.py --to-zip 10001 --weight-oz 16 --size 10x8x4`.

**Can it buy labels?**
Not this repo. It builds the draft (`create_shipment`, `create_batch`, `create_batch_from_orders`) with the rates of each group, and you click Buy in Pirate Ship. The hosted version has `buy_label` with a price cap per purchase.

**Can I create a batch from a spreadsheet or from my store orders?**
Yes. `create_batch` takes up to 500 recipients per call, `create_batch_from_orders` takes orders from your connected stores. `examples/draft_batch_from_csv.py` reads a CSV.

**Can I export shipments and tracking to CSV?**
Yes: `python examples/export_shipments.py --since 2026-10-01 --out october.csv`, or `export_shipments` for Pirate Ship's own spreadsheet with every column.

**Why does it need my Chrome?**
To read your Pirate Ship session without your password. Pirate Ship's sign-in sits behind a Cloudflare check, so you sign in in the browser and plain requests do the rest. Chrome is used once per sign-in, not for each call.

**What happens when Pirate Ship signs me out?**
Calls fail with `auth_expired`. With Chrome remote debugging on, the server reads the new cookies on the next call (click Allow when Chrome asks); otherwise run `pirate-ship-mcp connect` again.

**Can it run on a VPS or in Docker?**
Technically yes, with `PIRATE_SHIP_AUTH_TOKEN`. The cookie lasts about a day without use, Pirate Ship then sees your session from a datacenter IP. For an always-on setup the hosted version keeps your session in your own Cloud Browser.

**Will my Pirate Ship account get blocked?**
Requests carry Chrome's fingerprint and go out one at a time, as you would click. Nobody can promise a platform never acts. Keep to your normal use.

**Can I use it at work or for my clients?**
No, the license allows noncommercial use only. For a team, a company or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Is it open source?**
The source is public, the license is not an open source license: noncommercial use only, no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/pirate-ship-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](https://github.com/cotletdev/pirate-ship-api-mcp-server/blob/main/LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own Pirate Ship account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="https://raw.githubusercontent.com/cotletdev/pirate-ship-api-mcp-server/main/assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). Pirate Ship is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Pirate Ship.
