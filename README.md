# GovWell Territory Dashboard

An interactive map showing GovWell's ~17,500 ICP accounts across all 50 states — color-coded by pipeline status, filterable by BDR, tier, and account type. Used by the BDR team to track territory coverage and prioritize outreach.

**Live map:** https://acohengw.github.io/govwell-state-of-territory/bdr-map.html
**Password:** `Permitplease`

---

## For collaborators using Claude Code

This project is designed to be worked on with Claude Code. When you open this repo in Claude Code, Claude automatically reads `CLAUDE.md` and has full context about the project — what everything does, how the build pipeline works, and what's planned next.

**You don't need to be technical.** Just describe what you want to change and Claude will handle the code.

### Getting started

1. Install [Claude Code](https://claude.ai/code) if you haven't already
2. Clone this repo or open it directly in Claude Code
3. Claude will read `CLAUDE.md` on startup — no setup needed
4. Ask Claude to do things in plain English

### Things you can ask Claude to do

- *"Run the weekly data refresh with these new Salesforce exports"*
- *"Add [Name] to the BDR roster"*
- *"Change the color for Verbal from green to teal"*
- *"Build and push the updated map to GitHub"*
- *"Explain what the build pipeline does"*

---

## Project overview

| File | What it is |
|---|---|
| `CLAUDE.md` | Full project documentation — start here |
| `bdr-map-template.html` | The map UI — edit this, never `bdr-map.html` directly |
| `view-config-bdr.json` | BDR-specific config: status colors, roster, filter buttons |
| `data_processor.py` | Reads 5 Salesforce exports → `accounts_data.json` |
| `build-map.py` | Stamps version + timestamp into template → `bdr-map.html` |
| `accounts_data.json` | The ~17,500 account records loaded by the map at runtime |
| `smoke-test.js` | Automated checks to confirm nothing broke after a build |
| `geocode_master.csv` | Lat/lng coordinates for accounts — persists across refreshes |

## Weekly refresh (high level)

1. Download 5 Salesforce exports into `All Data for Map/`
2. Ask Claude to run `data_processor.py`
3. Ask Claude to run `build-map.py`
4. Ask Claude to run the smoke tests
5. Ask Claude to push to GitHub

The full workflow with exact details is in `CLAUDE.md`.

---

## What's planned next

- **Phase 2** — Replace manual CSV exports with a direct Salesforce connection
- **Phase 3** — Add an AE pipeline layer to the same map
- **Phase 4** — Full GTM view: BDR + AE + CS + Marketing on one map engine

See `CLAUDE.md` for the complete phase roadmap.

---

*Questions? Contact Ali Cohen — ali@govwell.com*
