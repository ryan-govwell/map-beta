# GovWell Territory Dashboard — CLAUDE.md

**Owner:** Ali Cohen (ali@govwell.com)
**Repo:** `acohenGW/govwell-state-of-territory`
**Last updated:** June 1, 2026

---

## How to Work With Ali

Ali is non-technical. When working in this project:
- Explain things in plain language. Define jargon when you use it.
- Assume Ali won't run terminal commands directly. Prefer double-clickable `.command` files or browser-injected buttons for anything user-facing.
- Files Ali needs to see live in the **Territory Dashboard** folder. Session sandbox paths (`/sessions/...`) are internal — never show these to Ali.
- Finished deliverables always go to `/Users/alicohen/Documents/Claude/Projects/Territory Dashboard/` and are presented with file cards.

---

## Repository & Data Policy

This repo is **private on GitHub** (GitHub Pro). The privacy boundary is the repo itself — collaborators must be explicitly invited.

### Never commit
- API keys, tokens, passwords, or credentials of any kind
- Raw Salesforce export files (`.xlsx`) — gitignored, go in `All Data for Map/`
- `sfdc_raw.json` — gitignored, intermediate Salesforce query output (may contain full ARR, IDs, etc.)

### Safe to commit
All processed account data fields are safe to commit since the repo is private:
- `arr` (customer ARR), `id` (Salesforce Account ID), pipeline status, owner names, legacy software, population, coordinates — everything the map needs

### Salesforce MCP rule — CRITICAL
**Claude must never query Salesforce unless Ali explicitly asks for a data refresh.** The MCP tools exist in every session but must remain dormant. Querying Salesforce costs tokens and hits the live org. Only invoke `mcp__claude_ai_Salesforce_MCP_Read_Only__*` tools when Ali says something like "refresh the data from Salesforce" or "run the Salesforce refresh."

### Multi-team data policy (Phase 3/4)
When AE, CS, or other teams get their own views, each team's data file (`accounts_data_ae.json`, etc.) follows the same rule: safe to commit since the repo is private. Each team gets its own query config (`sfdc-query-ae.json`, etc.) — no changes to the map engine or shared infrastructure.

---

## What This Project Is

A top-of-funnel territory intelligence dashboard for GovWell's BDR team. It visualizes ~17,500 ICP accounts across all 50 US states as dots on a Leaflet + D3.js map, color-coded by pipeline status, filterable by BDR owner, tier, and status. Refreshed weekly from 5 Salesforce exports.

---

## Live Maps

- **BDR Territory Map (main):** https://acohengw.github.io/govwell-state-of-territory/bdr-map.html
- **Original Map:** https://acohengw.github.io/govwell-state-of-territory/
- **Password:** `Permitplease`

Only `bdr-map.html` gets updated on weekly refreshes. Do not overwrite `index.html`.

---

## File Structure

```
Territory Dashboard/
├── All Data for Map/            ← 5 Salesforce exports (replaced weekly)
├── bdr-map-template.html        ← UI source of truth — edit this, not bdr-map.html
├── view-config-bdr.json         ← BDR view config: statuses, roster, filters, owner label
├── build-map.py                 ← Stamps version + timestamp into template → bdr-map.html
├── data_processor.py            ← PERMANENT: reads exports → accounts_data.json
├── smoke-test.js                ← Structural verification (Node + jsdom)
├── runtime-test.js              ← Stubbed runtime verification (Node only)
├── accounts_data.json           ← Processed account data (rebuilt each refresh, pushed to GitHub)
├── geocode_master.csv           ← Coord lookup — persists across refreshes
├── bdr-map.html                 ← Built deliverable, pushed to GitHub
├── push-to-github.skill         ← Browser-injected GitHub pusher
└── CLAUDE.md                    ← This file
```

### Critical rules
- **Never edit `bdr-map.html` directly** — it's a build artifact. Edit the template, then rebuild.
- **`data_processor.py` is permanent** — do not rewrite it from scratch. Update it.
- **`build-map.py` uses relative paths** — always run from inside the Territory Dashboard folder.
- **`build-map.py` validates** — refuses to write if either placeholder (`%%DATA_VERSION%%`, `%%DATA_REFRESHED%%`) is unsubstituted, or if `%%ACCOUNTS_JSON%%` accidentally appears in the template.
- **`data_processor.py` uses `os.path.dirname(__file__)` for BASE path** — no hardcoded session paths.
- **Never edit `view-config-bdr.json` without also re-running `build-map.py`** — the template reads it at runtime, but the build still validates it.

---

## Build Pipeline

```
5 Salesforce exports (XLSX)
         ↓
  data_processor.py       ← reads exports + geocode_master.csv for coords
         ↓
  accounts_data.json      ← standardized account records (standalone file)
         ↓
  python3 build-map.py    ← stamps version + timestamp into template
         ↓
  bdr-map.html (~70 KB)   ← push to GitHub (alongside accounts_data.json + view-config-bdr.json)
```

### Template placeholders (substituted by build-map.py)
- `%%DATA_VERSION%%` — latest ICP export filename suffix
- `%%DATA_REFRESHED%%` — human-readable build timestamp (e.g. `Jun 1, 2026 · 9:00am`)

`accounts_data.json` is **not** injected into the HTML anymore. The map fetches it at runtime
via `fetch('accounts_data.json')`. This keeps `bdr-map.html` at ~70 KB instead of ~2 MB.

### Runtime fetches (on page load, in parallel)
- `fetch('view-config-bdr.json')` → populates status colors/labels, roster, filter buttons, owner label
- `fetch('accounts_data.json')` → populates the 17,500 account records

---

## The 5 Salesforce Exports

All go in `All Data for Map/`. The processor picks the **latest file matching each glob**.

| Pattern | Contents |
|---|---|
| `ICP Accounts by State_ARC-*.xlsx` | All ICP accounts: name, state, tier, owner, created date, **Account ID (18)** |
| `AE Sales Pipeline_ARC-*.xlsx` | Open pipeline: stage, ARR, close date, account name |
| `All Customers by State with*.xlsx` | Customers: name, state, legacy software, ARR |
| `Meetings Booked by Cold Call per State-*.xlsx` | Cold-call meeting history |
| `Activities by Account-*.xlsx` | BDR activity log with account name and date |

The ICP export must include the **"Account ID (18)"** column for the `id` field to be populated.
The processor detects it automatically; if absent, `id` is omitted gracefully (no crash).

---

## Account JSON Schema

Each account in `accounts_data.json`:

```json
{
  "a":   "Account Name",
  "s":   "California",
  "t":   "1",
  "o":   "Lucy Nemerov",
  "st":  "sq",
  "src": "bdr",
  "id":  "001Hr000028Zd6FIAS",
  "la":  37.4512,
  "lo":  -122.0943,
  "leg": "Accela",
  "arr": 12000,
  "ld":  "2026-02",
  "n":   1
}
```

| Field | Description |
|---|---|
| `a` | Account name |
| `s` | State |
| `t` | Tier ("1", "2", "3") |
| `o` | Owner (Salesforce account owner name) |
| `st` | Status code (see Status Codes table) |
| `src` | Data source team — `"bdr"` for all BDR records (enables multi-team joins) |
| `id` | Salesforce Account ID (18-char) — universal join key across teams |
| `la` | Latitude |
| `lo` | Longitude |
| `leg` | Legacy software (omitted if none) |
| `arr` | ARR in dollars (omitted if none) |
| `ld` | Last touched month as `YYYY-MM` (omitted unless status = `t`) |
| `n` | `1` if account was added to ICP on/after Mar 1 2026 (omitted otherwise) |

---

## Status Codes

Status codes and their visual properties are defined in `view-config-bdr.json`, not hardcoded in the template. The table below reflects the current BDR view config.

| Code | Label | Color | Priority |
|---|---|---|---|
| `cu` | Customer | gold `#fbbf24` | 10 |
| `vb` | Verbal | green `#22c55e` | 9 |
| `pr` | Proposal | orange `#f97316` | 8 |
| `dm` | Demo | purple `#c084fc` | 7 |
| `sq` | Sales Qualified | cyan `#00e5ff` | 6 |
| `mb` | Meeting Booked | blue `#3b82f6` | 5 |
| `ii` | Initial Interest | yellow `#fde047` | 4 |
| `cl` | Closed Lost | red `#ef4444` | 3 |
| `t`  | Touched | sky blue `#38bdf8` | 2 |
| `u`  | Untouched | slate `#cbd5e1` | 1 |

To change a color or label, edit `view-config-bdr.json` — no template changes needed.

---

## View Config (view-config-bdr.json)

This file externalizes all BDR-specific configuration from the map engine. A future AE or CS
view gets its own `view-config-*.json` without touching the map template.

```json
{
  "viewId":       "bdr",
  "ownerLabel":   "BDR",
  "statuses":     { "cu": { "label": "Customer", "color": "#fbbf24", "symbol": "star", "priority": 10 }, ... },
  "statusGroups": { "pipeline": ["vb","pr","dm","sq","mb","ii"], "touched": [...], "pipelineFull": [...] },
  "dotFilters":   [ { "id": "all", "label": "All" }, { "id": "customers", "label": "★ Customers" }, ... ],
  "roster":       [ "Catherine Silvestri", "Nick Martino", ... ]
}
```

### What's driven by this config at runtime
- Status colors, labels, and D3 marker symbols
- Which statuses count as "pipeline", "touched", "pipelineFull"
- The filter bar buttons (All / ★ Customers / ◆ Pipeline / ● Touched / ○ Untouched)
- The owner pill row header label ("BDR")
- The owner field label in the hover tooltip
- The roster of team members shown as filter pills

---

## BDR Roster

The roster lives in `view-config-bdr.json` under `"roster"`. To add or remove a BDR, edit
that file and re-run `build-map.py` (the template reads it at runtime, but rebuilding keeps
the repo in sync).

Current roster:
```
Catherine Silvestri, Nick Martino, Ali Cohen, Ryan Minter, Alicia Gopal,
Lucy Nemerov, Hugh Bargeron, Sydney Ireland, Emily Murnane, Ben Laddis,
Blake Anderson, Mihir Shah, Maia Golub
```

---

## Weekly Refresh Workflow

1. Ali downloads 5 new Salesforce exports into `All Data for Map/`
2. Claude runs `data_processor.py` → produces `accounts_data.json`
3. Run `python3 build-map.py` → writes `bdr-map.html`
4. Run `node smoke-test.js` and `node runtime-test.js`
5. Push via the `push-to-github` skill — pushes **both** `bdr-map.html` and `accounts_data.json` in one commit

The `push-to-github` skill uses the GitHub Git Data API (blob → tree → commit → ref).
`view-config-bdr.json` only needs to be pushed when it changes (rare — not weekly).

---

## GitHub Deployment

- **Repo:** https://github.com/acohenGW/govwell-state-of-territory
- **Branch:** `main`
- **Token:** stored locally only — never commit to repo. Needs `repo` scope. Regenerate at github.com/settings/tokens if expired.
- Push uses the Git Data API: blob → tree → commit → ref update
- **Files that must always be deployed together:** `bdr-map.html` + `accounts_data.json`
- `view-config-bdr.json` must also be deployed if modified

---

## Phase Roadmap

This project is being migrated from Cowork to Claude Code and expanded for org-wide use.

### ✅ Phase 1 — Stabilize Infrastructure (complete)
- [x] `data_processor.py` is permanent (not rewritten each session)
- [x] `geocode_master.csv` exists (16,049+ rows) for coord persistence
- [x] Dynamic BASE path in `data_processor.py` (no hardcoded session paths)
- [x] Salesforce Account ID (`id` field, 18-char) added to all account records
- [x] `src: "bdr"` field added to all account records (multi-team join key)
- [x] `accounts_data.json` served as a standalone file (~2.5 MB); `bdr-map.html` is now ~70 KB
- [x] View config externalized to `view-config-bdr.json` — map engine reads config at runtime
- [x] `push-to-github` updated to push both `bdr-map.html` and `accounts_data.json` in one commit
- [x] Full source repo pushed to GitHub (all source files, not just bdr-map.html)
- [x] `data_processor.py` confirmed in the repo

### Phase 2 — Replace CSV Exports with Salesforce MCP
- Query Salesforce directly via `mcp__claude_ai_Salesforce_MCP_Read_Only__soqlQuery` (read-only, already connected)
- 4 SOQL queries replace 5 manual Excel exports — eliminates Monday morning download ritual
- Claude writes results to `sfdc_raw.json` (gitignored) → `data_processor.py` reads it → same pipeline as today
- **MCP only runs on explicit refresh request** — never ambient

**New files for Phase 2:**
```
sfdc-query-bdr.json     ← SOQL queries + field mappings for BDR view
sfdc_raw.json           ← gitignored intermediate output from MCP queries
```

**Key Salesforce field mappings (BDR):**
| Schema field | Salesforce API name |
|---|---|
| `a` (name) | `Name` |
| `s` (state) | `BillingState` |
| `t` (tier) | `Account_Tier__c` |
| `o` (owner) | `Owner.Name` |
| `pop` | `Population__c` |
| `leg` | `Legacy_Community_Development_Soft_Pick__c` |
| `id` | `Id` |
| `arr` (pipeline) | `ARR_Formula__c` on Opportunity |
| `arr` (customer) | `Current_ARR_Dlrs__c` on Account |

**Multi-team extensibility:** Each future team (AE, CS, Marketing) gets its own `sfdc-query-{team}.json` with different SOQL queries and field mappings. The map engine and `data_processor.py` don't change.

### Phase 3 — Add AE Pipeline Layer
- Create `view-config-ae.json` with AE-specific statuses, roster, and filters
- Add AE account data to the pipeline (new `src: "ae"` records)
- Map engine already supports swappable view configs — no template changes needed
- Leverage `id` field for clean cross-team joins

### Phase 4 — Full GTM Data Model
- Add CS (health, renewal, CSM owner) and Marketing layers via their own view configs
- One map engine, multiple swappable data sources
- Shared JSON schema: every department outputs the same format (`a`, `s`, `t`, `o`, `st`, `src`, `id`)

---

## Technical Stack

- **Map:** Leaflet.js v1.9.4 + D3.js v7 (CDN)
- **Tiles:** CartoDB Dark/Light, Esri Satellite
- **State boundaries:** us-atlas/states-10m.json via topojson
- **Markers:** `L.canvas` for circles, `L.divIcon` with D3 SVG paths for pipeline shapes
- **Data processing:** Python 3 + pandas
- **Password gate:** `window.prompt()` at load, stored in `sessionStorage` key `gw_auth`
- **Build:** Python string replace (no templating framework)
- **Runtime data loading:** `fetch()` + `Promise.all` for parallel config + data loads
