# GovWell Territory Dashboard — Context Checkpoint
_Last updated: June 1, 2026. Paste this into a fresh session to resume._

---

## Current State

**The map is live and working** at `map.bd-at-govwell.com` (private GitHub repo, GitHub Pro).
Password: `Permitplease`. The repo is `acohenGW/govwell-state-of-territory`, branch `main`.

### What works
- 17,492 ICP accounts render as colored dots on a Leaflet + D3.js map
- Status color-coding (customer, pipeline stages, touched, untouched)
- Filters: BDR owner pills, tier (1/2/3/S), dot type (All/Customers/Pipeline/Touched/Untouched)
- Population filters (County >150k, 50k–150k, etc. and City buckets) — `pop` field now read from ICP export
- Legacy software filters (Tyler, Accela, OpenGov, etc.) — `leg` field now read from ICP export
- S tier filter — works because `pop` is now populated
- ARR shows in tooltips and state panels
- Salesforce Account ID (`id`) in every record for future cross-team joins
- Phase 2 Salesforce MCP refresh path — implemented and validated against live org

### Known issues / fragility
- **1,408 accounts use imprecise coords** — state centroid ±0.6°. These are accounts not in `geocode_master.csv` (mostly newer accounts and Canadian provinces). They appear within ~40 miles of the state center, not their actual location.
- **Canadian province boundaries** not on the map — Quebec, Alberta, BC, Ontario are in the ICP but the map has no province shapes, so clicking those areas doesn't open a state panel.
- The `accounts_data.json` fallback was removed from coord loading to prevent contamination from a prior bad run. Only `geocode_master.csv` is used. Accounts not in the master get state centroid coords.

---

## File Architecture

```
govwell-state-of-territory/
├── bdr-map-template.html    ← EDIT THIS (never bdr-map.html directly)
├── bdr-map.html             ← build artifact; pushed to GitHub Pages
├── build-map.py             ← stamps %%DATA_VERSION%% + %%DATA_REFRESHED%% into template
├── data_processor.py        ← reads sfdc_raw.json OR Excel exports → accounts_data.json
├── sfdc-query-bdr.json      ← 4 validated SOQL queries for Salesforce MCP refresh
├── view-config-bdr.json     ← BDR config: status colors, roster, filter buttons, owner label
├── accounts_data.json       ← ~17.5k account records, fetched at runtime by the map
├── geocode_master.csv       ← 16,003 Google-geocoded lat/lng coords, persists across refreshes
├── smoke-test.js            ← 34-check structural verification (Node + jsdom)
├── runtime-test.js          ← stubbed runtime test (Node only; RAF error is expected/known)
├── CLAUDE.md                ← full project documentation
└── .gitignore               ← blocks: All Data for Map/, sfdc_raw.json, .DS_Store
```

**gitignored (never committed):**
- `All Data for Map/` — raw Salesforce Excel exports
- `sfdc_raw.json` — intermediate Salesforce MCP output

---

## Data Flow

```
SALESFORCE MCP (preferred)          EXCEL EXPORTS (fallback)
4 SOQL queries via MCP tool    OR   5 .xlsx files in All Data for Map/
         ↓                                      ↓
     sfdc_raw.json (gitignored)           [read directly]
              ↓
       data_processor.py        ← auto-detects which source to use
              ↓
       accounts_data.json       ← committed to repo, fetched by map at runtime
              ↓
       build-map.py
              ↓
       bdr-map.html             ← committed + pushed to GitHub Pages
```

**Coord resolution order in data_processor.py:**
1. Exact match in `geocode_master.csv`
2. Case-insensitive match
3. Fuzzy normalized match (strips "City of", "County of", etc.)
4. State centroid ± 0.6° (random but seeded at 42, so deterministic)

---

## Key Decisions Made

| Decision | Why |
|---|---|
| Repo is **private** (GitHub Pro, $4/mo) | ARR and pipeline status are competitively sensitive |
| `arr` and `id` included in `accounts_data.json` | Safe since repo is private; `id` needed for future cross-team joins |
| `sfdc_raw.json` is gitignored | May contain full ARR, raw IDs — intermediate file only |
| Salesforce MCP **never runs unless explicitly asked** | Costs tokens, hits live org. Documented in CLAUDE.md and saved to memory |
| `geocode_master.csv` as primary coord source (not `accounts_data.json`) | `accounts_data.json` was contaminated by a bad run that wrote random coords |
| ICONS built inside `_applyViewConfig()` not at module load | `SYM_TYPE` is empty at module load (view config hasn't fetched yet); building icons before config = `d3.symbol().type(undefined)` crash |
| `pop` and `leg` read from ICP export (auto-detected by column header) | These columns exist in the Salesforce ICP report at cols 8 & 9 but were never read |

---

## Salesforce MCP — Field Mappings

The MCP is connected as Ali Cohen (ali@govwell.com), BD Manager profile.
Queries are in `sfdc-query-bdr.json`. All 4 were validated against the live org today.

| Schema field | Salesforce field | Object |
|---|---|---|
| `a` (name) | `Name` | Account |
| `s` (state) | `BillingState` | Account |
| `t` (tier) | `Account_Tier__c` → strip "Tier " | Account |
| `o` (owner) | `Owner.Name` | Account |
| `pop` | `Population__c` | Account |
| `leg` | `Legacy_Community_Development_Soft_Pick__c` | Account |
| `id` | `Id` | Account |
| `st` = `cu` | `Account_Status__c IN ('Implementation', '1+ Module Live', 'All Modules Live')` | Account |
| `arr` (customer) | `Current_ARR_Dlrs__c` | Account |
| `arr` (pipeline) | `ARR_Formula__c` | Opportunity |
| Pipeline stage | `StageName` (open opps only) | Opportunity |
| Activities | `MAX(CreatedDate) GROUP BY AccountId` | Task |

**Customer count:** 148 accounts match customer statuses (matches our 147 from Excel).
**ICP count:** 25,492 via SOQL (vs 17,492 from Excel report — SOQL is more complete, Excel was filtered to BDR-owned accounts only).

---

## Exact Next Steps

### Immediate (next session)
1. **Test the full Salesforce MCP refresh end-to-end.** Say: _"refresh the data from Salesforce"_. Claude should: run 4 SOQL queries → write `sfdc_raw.json` → run `data_processor.py` → verify output → build → smoke test → push → delete `sfdc_raw.json`.

2. **Geocode the 1,408 missing accounts.** These are in `accounts_data.json` with state-centroid coords. Need to call Google Maps Geocoding API with each account name + state, add results to `geocode_master.csv`, then re-run the processor. This fixes the last inaccurate dots.

3. **Add Salesforce link from tooltip.** The `id` field (Salesforce Account ID) is in every record. One line change in `bdr-map-template.html` turns the account name in the tooltip into a link: `https://govwell.lightning.force.com/lightning/r/Account/{id}/view`. Huge BDR value.

### Near-term
4. **State coverage score** — show each state's % of ICP touched/in pipeline, not just raw counts. Makes this a territory health tool, not just a visualization.
5. **New account badge** — `n: 1` flag exists on 3,129 accounts (added since Mar 1, 2026) but isn't visually surfaced anywhere.
6. **Phase 3: AE layer** — `sfdc-query-ae.json` + `view-config-ae.json`. Map engine already supports swappable configs. AE pipeline uses same Account + Opportunity objects with different stage filters.

### Architecture context for Phase 3+
- Each new team (AE, CS, Marketing) gets its own `sfdc-query-{team}.json` + `view-config-{team}.json`
- `data_processor.py` and the map engine don't change — designed for this
- All output uses the same account JSON schema (`a`, `s`, `t`, `o`, `st`, `src`, `id`, etc.)
- `src` field distinguishes teams: BDR = `"bdr"`, AE = `"ae"`, etc.

---

## Build Commands (reference)

```bash
# Full refresh + deploy (from repo root)
python3 data_processor.py    # → accounts_data.json
python3 build-map.py         # → bdr-map.html
node smoke-test.js           # should say ALL GREEN: 34/34
git add accounts_data.json bdr-map.html
git commit -m "Weekly refresh [date]"
git push origin main
```

GitHub token is stored in the git remote URL. If it expires, regenerate at github.com/settings/tokens (needs `repo` scope) and run:
`git remote set-url origin https://TOKEN@github.com/acohenGW/govwell-state-of-territory.git`
