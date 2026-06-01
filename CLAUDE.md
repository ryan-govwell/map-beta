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

## What This Project Is

A top-of-funnel territory intelligence dashboard for GovWell's BDR team. It visualizes ~16,000 ICP accounts across all 50 US states as dots on a Leaflet + D3.js map, color-coded by pipeline status, filterable by BDR owner, tier, and status. Refreshed weekly from 5 Salesforce exports.

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
├── build-map.py                 ← Injects JSON + timestamps into template → bdr-map.html
├── data_processor.py            ← PERMANENT: reads exports → accounts_data.json
├── smoke-test.js                ← Structural verification (Node + jsdom)
├── runtime-test.js              ← Stubbed runtime verification (Node only)
├── accounts_data.json           ← Processed account data (rebuilt each refresh)
├── geocode_master.csv           ← Coord lookup — persists across refreshes
├── bdr-map.html                 ← Built deliverable, pushed to GitHub
├── push-to-github.skill         ← Browser-injected GitHub pusher
└── CLAUDE.md                    ← This file
```

### Critical rules
- **Never edit `bdr-map.html` directly** — it's a build artifact. Edit the template, then rebuild.
- **`data_processor.py` is permanent** — do not rewrite it from scratch. Update it.
- **`build-map.py` uses relative paths** — always run from inside the Territory Dashboard folder.
- **`build-map.py` validates** — refuses to write if any of the 3 placeholders is missing.
- **`data_processor.py` uses `os.path.dirname(__file__)` for BASE path** — no hardcoded session paths.

---

## Build Pipeline

```
5 Salesforce exports (XLSX)
         ↓
  data_processor.py       ← reads exports + geocode_master.csv for coords
         ↓
  accounts_data.json      ← standardized account records
         ↓
  python3 build-map.py    ← injects JSON + version + timestamp into template
         ↓
  bdr-map.html            ← push to GitHub → live URL
```

### Template placeholders (substituted by build-map.py)
- `%%ACCOUNTS_JSON%%` — full accounts_data.json content
- `%%DATA_VERSION%%` — latest ICP export filename suffix
- `%%DATA_REFRESHED%%` — human-readable build timestamp (e.g. `Jun 1, 2026 · 9:00am`)

---

## The 5 Salesforce Exports

All go in `All Data for Map/`. The processor picks the **latest file matching each glob**.

| Pattern | Contents |
|---|---|
| `ICP Accounts by State_ARC-*.xlsx` | All ICP accounts: name, state, tier, owner, created date |
| `AE Sales Pipeline_ARC-*.xlsx` | Open pipeline: stage, ARR, close date, account name |
| `All Customers by State with*.xlsx` | Customers: name, state, legacy software, ARR |
| `Meetings Booked by Cold Call per State-*.xlsx` | Cold-call meeting history |
| `Activities by Account-*.xlsx` | BDR activity log with account name and date |

---

## Account JSON Schema

Each account in `accounts_data.json`:

```json
{
  "a":   "Account Name",
  "s":   "California",
  "t":   "1",
  "la":  37.4512,
  "lo":  -122.0943,
  "o":   "Lucy Nemerov",
  "st":  "sq",
  "leg": "Accela",
  "arr": 12000,
  "ld":  "2026-02",
  "n":   1
}
```

Fields `leg`, `arr`, `ld`, `n` are omitted if not applicable.

**Phase 1 gap:** Salesforce Account ID (`id` field) is not yet included. Adding it is a Phase 1 priority — it enables joining data across teams without fragile name-matching.

---

## Status Codes

| Code | Label | Color | Priority |
|---|---|---|---|
| `cu` | Customer | gold | 10 |
| `vb` | Verbal | green | 9 |
| `pr` | Proposal | orange | 8 |
| `dm` | Demo | purple | 7 |
| `sq` | SQO | cyan | 6 |
| `mb` | Meeting Booked | blue | 5 |
| `ii` | Initial Interest | yellow | 4 |
| `cl` | Closed Lost | red | 3 |
| `t`  | Touched | chill blue | 2 |
| `u`  | Untouched | slate | 1 |

---

## BDR Roster

Hardcoded in `bdr-map-template.html` as `BDR_ROSTER`. To add/remove a BDR, edit the Set there, then re-run `build-map.py`.

```
Catherine Silvestri, Nick Martino, Ali Cohen, Ryan Minter, Alicia Gopal,
Lucy Nemerov, Hugh Bargeron, Sydney Ireland, Emily Murnane, Ben Laddis
```

---

## Weekly Refresh Workflow

1. Ali downloads 5 new Salesforce exports into `All Data for Map/`
2. Claude runs `data_processor.py` → produces `accounts_data.json`
3. Run `python3 build-map.py` → writes `bdr-map.html`
4. Run `node smoke-test.js` and `node runtime-test.js`
5. Push via the `push-to-github` skill (browser-injected button using GitHub Git Data API)

The `push-to-github` skill is required for pushing — the file is ~2MB which exceeds GitHub's simple Contents API limit.

---

## GitHub Deployment

- **Repo:** https://github.com/acohenGW/govwell-state-of-territory
- **Branch:** `main`
- **Token:** stored locally only — never commit to repo. Needs `repo` scope. Regenerate at github.com/settings/tokens if expired.
- Push uses the Git Data API: blob → tree → commit → ref update

---

## Phase Roadmap

This project is being migrated from Cowork to Claude Code and expanded for org-wide use.

### ✅ Phase 1 — Stabilize Infrastructure (current)
- [x] `data_processor.py` is permanent (not rewritten each session)
- [x] `geocode_master.csv` exists (16,049 rows) for coord persistence
- [x] Dynamic BASE path in `data_processor.py` (no hardcoded session paths)
- [ ] Add Salesforce Account ID to all account records
- [ ] Push full repo to GitHub (all source files, not just bdr-map.html)
- [ ] Confirm `data_processor.py` is in the repo

### Phase 2 — Replace CSV Exports with Salesforce MCP
- Rewrite refresh skill to query Salesforce directly via MCP (read-only)
- Pull Accounts, Opportunities, Activities, Contacts in one session
- Join by Account ID — eliminates manual Monday morning export ritual
- MCP should only activate when explicitly called (not ambient every session)

### Phase 3 — Add AE Pipeline Layer
- Add AE pipeline as a second data layer on the map (new filter/view)
- Leverage Account ID join established in Phase 2

### Phase 4 — Full GTM Data Model
- Add CS (health, renewal, CSM owner) and Marketing layers
- One map engine, multiple swappable data sources
- Shared JSON schema: every department outputs same format, map doesn't care about source

---

## Technical Stack

- **Map:** Leaflet.js v1.9.4 + D3.js v7 (CDN)
- **Tiles:** CartoDB Dark/Light, Esri Satellite
- **State boundaries:** us-atlas/states-10m.json via topojson
- **Markers:** `L.canvas` for circles, `L.divIcon` with D3 SVG paths for pipeline shapes
- **Data processing:** Python 3 + pandas
- **Password gate:** `window.prompt()` at load, stored in `sessionStorage` key `gw_auth`
- **Build:** Python string replace (no templating framework)
