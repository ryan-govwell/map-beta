# Pipeline Refactor — In Progress

**Owner:** Ryan Minter
**Started:** June 2026
**Status:** Accounts + Pipeline complete — customers/activities TBD

---

## Change Log

| Date | Change |
|---|---|
| Jun 3, 2026 | New pipeline scaffolding created (`pipeline/`) |
| Jun 3, 2026 | `process_accounts.py` built and validated against new SF report |
| Jun 3, 2026 | `merge.py` built to convert accounts CSV → `accounts_data.json` |
| Jun 3, 2026 | Map now served from new pipeline data (16,213 accounts) |
| Jun 3, 2026 | Password gate removed (Cloudflare handles auth) |
| Jun 3, 2026 | GovWell SVG logo added to header |
| Jun 3, 2026 | DM Sans font adopted (matches Territory V2) |
| Jun 3, 2026 | GovWell gold (`#FEAF0E`) applied to active rep pill and "new account" badge |
| Jun 3, 2026 | Light/dark mode toggle added with localStorage persistence |
| Jun 3, 2026 | `data_processor.py` removed — fully replaced by new `pipeline/` architecture |
| Jun 3, 2026 | `constants.py` updated with `ARR_PLACEHOLDER`, `TOP_OF_FUNNEL_STAGES`, `STAGE_PRIORITY` |
| Jun 3, 2026 | First attempt at `process_pipeline.py` removed — rebuilding fresh |
| Jun 3, 2026 | UI stripped of all pipeline/activity elements — dot filters, panel sections, tooltips, choropleth all cleaned up |
| Jun 3, 2026 | `view-config-bdr.json` stripped to `cu` + `u` status codes only |
| Jun 3, 2026 | Population filter bar, legacy software filter bar, tier toggle, and panel tab buttons removed — rebuilding later |
| Jun 3, 2026 | Sidebar panel removed entirely (national + state views) — rebuilding later |
| Jun 3, 2026 | All/Customers center bar removed; replaced with top-left Visibility panel (All + State dropdown) |
| Jun 3, 2026 | No dots on load — user must opt in via Visibility panel |
| Jun 3, 2026 | State dropdown replaced with custom multi-select (searchable, toggle per state, stays in viewport) |
| Jun 3, 2026 | BDR rep pills row removed from header — rebuilding later |
| Jun 3, 2026 | Account Status legend removed from bottom-right — rebuilding later |
| Jun 3, 2026 | Right-hand table panel added — Account, St, Owner, Tier, Pop — toggleable via header button |
| Jun 3, 2026 | `pop` field added to merge.py output and accounts_data.json regenerated |
| Jun 3, 2026 | `process_pipeline.py` built — Signal field (Won/Mid Funnel/Top Funnel/Lost), ARR as numeric |
| Jun 3, 2026 | `merge.py` extended to join pipeline by Account ID; stage-priority dedup; numeric ARR |
| Jun 3, 2026 | `view-config-bdr.json` restored with all 9 status codes (cu/vb/pr/dm/sq/mb/ii/cl/u) |
| Jun 3, 2026 | `_applyViewConfig` now builds shaped icons dynamically from view-config symbols |
| Jun 3, 2026 | Pipeline statuses simplified to Signal-level: Won/Customer, Mid Funnel, Top Funnel, Closed Lost |
| Jun 3, 2026 | Untouched removed — activity not yet layered in; no-pipeline accounts render as neutral gray with no label |
| Jun 5, 2026 | Table panel moved to left third; toggled via "Show Table" bar below Visibility panel; header toggle removed |
| Jun 5, 2026 | `process_activities.py` built — BDR team filter, aggregates to one row per account (Total Calls, Last Call Date) |
| Jun 5, 2026 | `merge.py` extended with activity join — adds `t` (Touched), `tc`, `lcd` fields; `u` now means truly no data |
| Jun 5, 2026 | `view-config-bdr.json` updated with `t` (Touched, sky blue) status |
| Jun 5, 2026 | `process_activities.py` extended with per-rep call columns (same as territory-v2) |
| Jun 5, 2026 | `merge.py` stores per-rep data as `reps: [[name, count], ...]` in JSON |
| Jun 5, 2026 | `process_contacts.py` built — classifies contacts by function (bp/pz/ce/ot), 38,523 contacts across 12,457 accounts |
| Jun 5, 2026 | `merge.py` extended with contact join — stores `contacts: [[name, title, fn, last_act], ...]` per account |
| Jun 5, 2026 | Table expand row now shows call breakdown + contacts grouped by function |
| Jun 5, 2026 | Tooltip: Last Touched, Total Calls, Functions (colored chips per contact function) added |
| Jun 5, 2026 | Status filter dropdown added to Visibility panel — multi-select, opens right, filters map dots by pipeline stage |
| Jun 5, 2026 | "Clear filters" button added to Visibility panel — appears when any filter is active, resets all to blank state |
| Jun 5, 2026 | Table: Calls + Last Call columns added; expand button (▶) shows per-rep call breakdown |
| Jun 5, 2026 | BDM Pages: "BDM Pages" dropdown added below Show Table; each name links to `bdr-map.html?rep=<name>` |
| Jun 5, 2026 | Rep-filtered view: `?rep=<name>` in URL scopes map + table to that rep's owned + called-in accounts; auto-shows all; header shows rep name + back link |
| Jun 5, 2026 | Called-in accounts distinguished on map with white ring outline; tooltip shows Owned/Called-In; table splits into Owned / Called-In sections |
| Jun 5, 2026 | Table pagination added — 500 rows per page, Prev/Next bar at bottom of panel, resets to page 1 on filter change |
| Jun 5, 2026 | State Pages: searchable dropdown added to map controls; each state links to `bdr-map.html?state=<name>`; state view scopes all data to that state, hides state filter + both page dropdowns, shows state name in header |
| Jun 5, 2026 | `state-dashboard.html` created — chart hub for state views; 4 charts (rep call volume, pipeline status donut, tier donut, owner breakdown); linked via "Dashboard" button in state map header |
| Jun 5, 2026 | `rep-dashboard.html` created — BDM personal hub; activity coverage, quarterly progress stat+bar, tier distribution, my calls by state, accounts needing attention table, called-in activity by owner; linked via "Dashboard" button in rep map header |
| Jun 8, 2026 | State Pages dropdown removed; replaced with BDM filter panel (pod + rep pills) and color mode toggle (Stage/Owner/Pod) in left controls |
| Jun 8, 2026 | Pod/owner color coding: view-config extended with pods (GovPod/PodWell) and ownerColors (12 rep colors); dots re-render by owner or pod color with floating legend |
| Jun 8, 2026 | Visibility panel and BDM Pages bar removed from left controls; map now defaults to showing all dots on load |
| Jun 8, 2026 | "Show Table" button restyled — bolder, larger, gold highlight when active |
| Jun 8, 2026 | `rep-dashboard.html`: expand/contact/Salesforce functionality added to both tables (All Accounts + Customers in My Territory) — expand button (▶), call breakdown chips, contacts grouped by function, Salesforce link |
| Jun 8, 2026 | `rep-dashboard.html`: All Accounts table gains Owner + Calls columns, sort support for both; expand pane built via `buildExpandPane()` shared by both tables |

---

## What's Changing and Why

The original data processing for this map lived in a single script (`data_processor.py`) that handled everything at once: accounts, pipeline, customers, and activity — all joined together and written to one large output file (`accounts_data.json`, ~2.8 MB). This worked but was hard to maintain and debug because all the logic was tangled together.

We're rebuilding the processing layer using the same architecture as the Territory V2 dashboard — one script per data object, a shared constants file, and clean outputs that can be verified at each step before moving to the next. The map itself and the GitHub deployment process are not changing yet.

---

## Current Pipeline Structure

```
pipeline/
├── constants.py              ← BDR_TEAM, tier points, state codes, stage priority
├── process_accounts.py       ✓ accounts → pipeline/accounts.csv
├── process_pipeline.py       ✓ opportunities → pipeline/pipeline.csv
├── process_activities.py     ✓ activity log → pipeline/activities.csv
├── process_contacts.py       ✓ contacts → pipeline/contacts.csv
├── process_customers.py      ✗ not built yet
├── merge.py                  ✓ joins all four → accounts_data.json
├── geo/
│   └── geo_lookup.json       ← 17,460-entry coordinate lookup
├── accounts.csv              ← generated, not committed
├── pipeline.csv              ← generated, not committed
├── activities.csv            ← generated, not committed
└── contacts.csv              ← generated, not committed
```

---

## Salesforce Report Change

The accounts report used for Territory V2 has been updated with two new columns:

| New column | What it contains |
|---|---|
| `Account Tier` | Tier S / 1 / 2 / 3 — pulled directly from Salesforce |
| `Legacy Community Development Software` | The incumbent software the account currently uses |

**Report used:** `report1780518311277.csv` (downloaded June 2026)

Previously, tier was derived by comparing population against thresholds (e.g. population ≥ 50,000 = Tier S). Going forward, we read the tier Salesforce already assigns. This keeps our data consistent with what the rest of the org sees in Salesforce.

---

## What `process_accounts.py` Produces

Running this script against the accounts report produces `pipeline/accounts.csv` with one row per account and these fields:

| Field | Source |
|---|---|
| Account ID | Salesforce (18-char ID, primary join key) |
| Account Name | Salesforce |
| State | Salesforce (`Billing State/Province`) |
| Entity Type | Salesforce (e.g. Municipality, County) |
| Owner | Salesforce account owner name |
| Population | Salesforce |
| Account Status | Salesforce (e.g. Open Opportunity, Nurture) |
| Account Tier | Salesforce (Tier S / 1 / 2 / 3) |
| SQO Points | Derived from tier (S=2.0, 1=1.5, 2=1.0, 3=0.75) |
| Legacy Community Development Software | Salesforce |
| Lat / Lng | Looked up from `geo_lookup.json` by account name |
| Starbridge Buyer ID | Salesforce |

**Last run result:** 16,240 accounts, 27 without coordinates (see Known Issues below).

---

## How to Run a Full Refresh

From the `govwell-state-of-territory/` folder:

```bash
# 1. Accounts
python3 pipeline/process_accounts.py \
    --accounts ~/Downloads/<accounts-report>.csv \
    --geo      pipeline/geo/geo_lookup.json \
    --output   pipeline/accounts.csv

# 2. Pipeline (opportunities)
python3 pipeline/process_pipeline.py \
    --input  ~/Downloads/<opps-report>.csv \
    --output pipeline/pipeline.csv

# 3. Activity
python3 pipeline/process_activities.py \
    --input  ~/Downloads/<activity-report>.csv \
    --output pipeline/activities.csv

# 4. Contacts
python3 pipeline/process_contacts.py \
    --input  ~/Downloads/<contacts-report>.csv \
    --output pipeline/contacts.csv

# 5. Merge everything → accounts_data.json
python3 pipeline/merge.py \
    --accounts   pipeline/accounts.csv \
    --pipeline   pipeline/pipeline.csv \
    --activities pipeline/activities.csv \
    --contacts   pipeline/contacts.csv \
    --output     accounts_data.json

# 6. Build the map
python3 build-map.py
```

### Salesforce reports used (June 2026)

| Report | File |
|---|---|
| Accounts | `report1780518311277.csv` |
| Opportunities | `report1780522493381.csv` |
| Activity | `report1780667670914.csv` |
| Contacts | `report1780668631115.csv` |

---

## Known Issues

**27 accounts have no coordinates.** These are mostly Ohio townships whose Salesforce names include a county suffix in parentheses (e.g. "Township Of Penn, PA (Lancaster County)"), which doesn't match any key in the geo lookup. A few others are large cities that may have been added to Salesforce after the geo lookup was last built. These accounts will appear on the map without a dot until resolved. Fix is deferred.

---

## What's Not Built Yet

| Item | Notes |
|---|---|
| `process_customers.py` | Customer ARR from Salesforce customer records |
| BDR rep owner filter | Removed from header — rebuilding with new architecture |
| Tier / population / legacy software filters | Removed — rebuilding with new architecture |
| GitHub push | `accounts_data.json` + `bdr-map.html` + `view-config-bdr.json` need deploying |
