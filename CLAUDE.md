# GovWell Territory Dashboard — CLAUDE.md

**Owner:** Ryan Minter (ryan@govwell.com)
**Repo:** `acohenGW/govwell-state-of-territory`
**Last updated:** June 2026

---

## How to Work With Ryan

Ryan is on the GTM/BD team at GovWell. He manages territory intelligence tooling and is comfortable with technical concepts but not a developer. When working in this project:
- Explain decisions in plain language but don't over-explain basics.
- Ryan approves bash commands via Claude's permission prompt — do not ask him to run them manually.
- Always update `REFACTOR.md` after any change to the project.

---

## Repository & Data Policy

This repo is **private on GitHub**. The privacy boundary is the repo itself.

### Never commit
- API keys, tokens, passwords, or credentials of any kind
- Raw Salesforce export CSV files
- `sfdc_raw.json` — gitignored intermediate Salesforce MCP output

### Safe to commit
All processed account data fields are safe since the repo is private:
- `arr`, `id`, pipeline status, owner names, legacy software, population, coordinates

### Salesforce MCP rule — CRITICAL
**Never query Salesforce unless Ryan explicitly asks for a data refresh.** The MCP tools exist in every session but must stay dormant. Only invoke `mcp__claude_ai_Salesforce_MCP_Read_Only__*` when Ryan says something like "refresh the data from Salesforce."

---

## What This Project Is

A territory intelligence dashboard for GovWell's BDR team. It visualizes ~16,200 ICP accounts across all 50 US states as dots on a Leaflet + D3.js map, color-coded by pipeline Signal (Won/Customer, Mid Funnel, Top Funnel, Closed Lost). Accounts with no pipeline data render as neutral gray dots — no "Untouched" label until activity data is layered in.

The map loads blank. Users opt in to what they see via a **Visibility panel** (top-left): show All accounts, or select one or more specific states.

---

## Live Map

- **URL:** https://acohengw.github.io/govwell-state-of-territory/bdr-map.html
- **Password:** none (removed — Cloudflare handles auth)
- **Local dev:** `python3 -m http.server 8080` from the project root → http://localhost:8080/bdr-map.html

Only `bdr-map.html` gets updated on refreshes. Do not overwrite `index.html`.

---

## File Structure

```
govwell-state-of-territory/
├── pipeline/                    ← data processing (one script per object)
│   ├── constants.py             ← BDR_TEAM, tier points, state codes, stage priority
│   ├── process_accounts.py      ✓ SF accounts CSV → pipeline/accounts.csv
│   ├── process_pipeline.py      ✓ SF opportunities CSV → pipeline/pipeline.csv
│   ├── process_activities.py    ✓ SF activity CSV → pipeline/activities.csv
│   ├── process_contacts.py      ✓ SF contacts CSV → pipeline/contacts.csv
│   ├── process_customers.py     ✗ NOT BUILT YET
│   ├── merge.py                 ✓ joins all four → accounts_data.json (5.3 MB)
│   ├── accounts.csv             ← generated, not committed
│   ├── pipeline.csv             ← generated, not committed
│   ├── activities.csv           ← generated, not committed
│   ├── contacts.csv             ← generated, not committed
│   └── geo/
│       └── geo_lookup.json      ← 17,460-entry coordinate lookup by account name
├── bdr-map-template.html        ← UI source of truth — EDIT THIS, not bdr-map.html
├── view-config-bdr.json         ← status codes, colors, symbols, roster
├── build-map.py                 ← stamps version + timestamp into template → bdr-map.html
├── accounts_data.json           ← built by merge.py, pushed to GitHub
├── bdr-map.html                 ← build artifact — never edit directly
├── geocode_master.csv           ← legacy coord cache (superseded by geo_lookup.json)
├── sfdc-query-bdr.json          ← SOQL queries for future Salesforce MCP refresh
├── smoke-test.js                ← structural verification
├── REFACTOR.md                  ← living changelog — update after every change
└── CLAUDE.md                    ← this file
```

### Critical rules
- **Never edit `bdr-map.html` directly** — it's a build artifact. Edit the template, then run `python3 build-map.py`.
- **Never edit `view-config-bdr.json` without rebuilding** — the map reads it at runtime but the build validates structure.
- **`build-map.py` uses relative paths** — always run from the project root.
- **Always update `REFACTOR.md`** after any change.

---

## Data Pipeline

```
SF accounts CSV  ──→  process_accounts.py  ──→  pipeline/accounts.csv
SF opps CSV      ──→  process_pipeline.py  ──→  pipeline/pipeline.csv
                                                         │
                                               merge.py (joins on Account ID)
                                                         │
                                               accounts_data.json
                                                         │
                                               build-map.py
                                                         │
                                               bdr-map.html  →  push to GitHub
```

### Step-by-step refresh

```bash
# 1. Process accounts (SF accounts report)
python3 pipeline/process_accounts.py \
    --accounts ~/Downloads/<accounts-report>.csv \
    --geo      pipeline/geo/geo_lookup.json \
    --output   pipeline/accounts.csv

# 2. Process pipeline (SF opportunities report)
python3 pipeline/process_pipeline.py \
    --input  ~/Downloads/<opps-report>.csv \
    --output pipeline/pipeline.csv

# 3. Merge into accounts_data.json
python3 pipeline/merge.py \
    --accounts pipeline/accounts.csv \
    --pipeline pipeline/pipeline.csv \
    --output   accounts_data.json

# 4. Build the map
python3 build-map.py

# 5. Push to GitHub
```

### Salesforce report formats

**Accounts report** — columns required:
`Account ID, Account Name, Billing State/Province, Account Owner, Entity Type, Population, Account Tier, Account Status, Legacy Community Development Software, Starbridge Buyer ID`

**Opportunities report** — columns required:
`Account ID, Account Name, Opportunity Owner, Discovery Call Booked By, Discovery Call Date, Created Date, Stage, Annual Recurring Revenue (ARR), Closed Lost Stage Date, Closed Won Stage Date`

Both reports export as CSV with latin-1 encoding (standard Salesforce export format).

---

## Status Codes

Defined in `view-config-bdr.json`. The map builds its marker colors, labels, and shapes from this file at runtime — no template changes needed to adjust a color or label.

| Code | Label | Color | Meaning |
|---|---|---|---|
| `cu` | Won / Customer | gold `#fbbf24` | Closed Won opp or active customer status |
| `mf` | Mid Funnel | orange `#f97316` | Open opp — SQ, Demo, Proposal, or Verbal stage |
| `tf` | Top Funnel | blue `#3b82f6` | Open opp — Initial Interest or Meeting Booked |
| `cl` | Closed Lost | red `#ef4444` | Closed Lost opp, no open opp |
| `u`  | *(no label)* | gray `#94a3b8` | No pipeline data — renders as neutral dot, no status shown in tooltip |

`u` is a silent fallback — it is **not** in `view-config-bdr.json`. It is hardcoded in the template JS after config loads. It means "no pipeline and no BDR activity on record."

Signal → status code mapping (in `merge.py`):
- `Won` → `cu`
- `Mid Funnel` → `mf`
- `Top Funnel` → `tf`
- `Lost` → `cl`
- No opp → `u`

---

## Account JSON Schema

Each account in `accounts_data.json`:

```json
{
  "a":   "City Of Cayce, SC",
  "s":   "South Carolina",
  "t":   "2",
  "o":   "Hugh Bargeron",
  "st":  "tf",
  "src": "bdr",
  "id":  "001Hr000028ZbWl",
  "la":  33.9657,
  "lo":  -81.074,
  "pop": 13739,
  "leg": "CentralSquare - eTRAKIT",
  "arr": 45000,
  "pl":  1
}
```

| Field | Description |
|---|---|
| `a` | Account name |
| `s` | State (full name) |
| `t` | Tier ("S", "1", "2", "3") — read from Salesforce `Account_Tier__c`, not derived from population |
| `o` | Owner (Salesforce account owner name) |
| `st` | Status code (`cu`/`mf`/`tf`/`cl`/`u`) |
| `src` | Data source team — `"bdr"` for all BDR records |
| `id` | Salesforce Account ID (18-char) — primary join key |
| `la` | Latitude |
| `lo` | Longitude |
| `pop` | Population (integer, omitted if blank) |
| `leg` | Legacy software (omitted if none or "None Visible") |
| `arr` | ARR in dollars as integer (omitted if none or placeholder $23k) |
| `pl` | `1` if account has a Previously Lost flag (open opp + lost opp coexist) |

---

## View Config (view-config-bdr.json)

Externalizes all BDR-specific config from the map engine.

```json
{
  "viewId":   "bdr",
  "ownerLabel": "BDR",
  "statuses": {
    "cu": { "label": "Won / Customer", "color": "#fbbf24", "symbol": "star",   "priority": 5 },
    "mf": { "label": "Mid Funnel",     "color": "#f97316", "symbol": "circle", "priority": 4 },
    "tf": { "label": "Top Funnel",     "color": "#3b82f6", "symbol": "circle", "priority": 3 },
    "cl": { "label": "Closed Lost",    "color": "#ef4444", "symbol": "circle", "priority": 2 }
  },
  "roster": [ "Catherine Silvestri", "Nick Martino", ... ]
}
```

`symbol: "star"` renders as a D3 shaped `L.divIcon` marker. `symbol: "circle"` uses Leaflet's `circleMarker` (canvas renderer). Shapes are built dynamically from config — no template changes needed to add a new symbol.

---

## UI State (current)

The map has been rebuilt from first principles. Things removed (will be rebuilt):
- BDR rep pills / owner filter
- Population filter bar
- Legacy software filter bar
- Tier filter
- Sidebar panel (national + state views)
- Account Status legend

Things currently working:
- **Visibility panel** (top-left): "All" toggle + multi-select state dropdown with search
- **Table panel** (right-hand, toggleable via header button): Account, St, Owner, Tier, Pop
- **Dot tooltip**: name, status badge (omitted for `u`), tier, state, population, legacy software, ARR
- **Light/dark mode** toggle (header right), persists to localStorage
- **Basemap toggle**: Dark / Light / Satellite / Off
- **Search box**: free-text search over account names, flies to matched account
- **Map click**: clicking a state selects it in the Visibility panel

---

## BDR Roster

Lives in `view-config-bdr.json` under `"roster"`. Edit there and rebuild.

```
Catherine Silvestri, Nick Martino, Ali Cohen, Ryan Minter, Alicia Gopal,
Lucy Nemerov, Hugh Bargeron, Sydney Ireland, Emily Murnane, Ben Laddis,
Blake Anderson, Mihir Shah, Maia Golub
```

---

## GitHub Deployment

- **Repo:** https://github.com/acohenGW/govwell-state-of-territory
- **Branch:** `main`
- **Files to deploy together:** `bdr-map.html` + `accounts_data.json` + `view-config-bdr.json` (if changed)

---

## What's Not Built Yet

| Item | Notes |
|---|---|
| `process_customers.py` | Customer ARR from Salesforce customer records |
| BDR rep owner filter | Removed — rebuilding |
| Tier / population / legacy filters | Removed — rebuilding |
| GitHub push | `accounts_data.json` + `bdr-map.html` + `view-config-bdr.json` need deploying |

---

## Technical Stack

- **Map:** Leaflet.js v1.9.4 + D3.js v7 (CDN)
- **Tiles:** CartoDB Dark/Light, Esri Satellite
- **State boundaries:** us-atlas/states-10m.json via topojson
- **Markers:** `L.circleMarker` (canvas) for circles; `L.divIcon` with D3 SVG paths for star (cu)
- **Data processing:** Python 3 stdlib only (csv, json, pathlib) — no pandas
- **Build:** Python string replace (no templating framework)
- **Runtime data loading:** `fetch()` + `Promise.all` for parallel config + data loads
