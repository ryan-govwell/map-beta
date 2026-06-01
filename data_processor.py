#!/usr/bin/env python3
"""
Weekly data processor for the GovWell Territory Dashboard.
Version A: full ICP refresh (uses new ICP export as ground-truth account list).

Reads:
  - 5 Salesforce exports in All Data for Map/
  - Previous bdr-map.html for geocoord carryover (regex-extract)

Writes:
  - accounts_data.json (NOT bdr-map.html — build-map.py does that)
"""
import os, re, json, glob, random, warnings
from datetime import datetime
import pandas as pd

warnings.filterwarnings("ignore")
random.seed(42)

# ---------------- Paths ----------------
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f"{BASE}/All Data for Map"
HTML_SRC     = f"{BASE}/bdr-map.html"       # legacy — no longer used for coords
OUT_JSON     = f"{BASE}/accounts_data.json"
GEOCODE_CSV  = f"{BASE}/geocode_master.csv"

# Pick the latest file matching each glob pattern
def latest(pat):
    files = sorted(glob.glob(os.path.join(DATA_DIR, pat)))
    if not files:
        raise FileNotFoundError(f"No files match {pat} in {DATA_DIR}")
    return files[-1]

ICP_FILE     = latest("ICP Accounts by State_ARC-*.xlsx")
PIPE_FILE    = latest("AE Sales Pipeline_ARC-*.xlsx")
# Note: matches both "All Customers by State with Comp-*" (new) and "All Customers by State with Competitor-*" (legacy);
# pick the most recent by file mtime / lexical order, but prefer ones containing the latest date
def latest_customer():
    cands = sorted(glob.glob(os.path.join(DATA_DIR, "All Customers by State with*.xlsx")),
                   key=os.path.getmtime)
    if not cands:
        raise FileNotFoundError("No customers file found")
    return cands[-1]
CUST_FILE    = latest_customer()
MEET_FILE    = latest("Meetings Booked by Cold Call per State-*.xlsx")
ACT_FILE     = latest("Activities by Account-*.xlsx")

print("Using exports:")
for n, p in [("ICP", ICP_FILE), ("PIPE", PIPE_FILE), ("CUST", CUST_FILE),
             ("MEET", MEET_FILE), ("ACT", ACT_FILE)]:
    print(f"  {n:5s} {os.path.basename(p)}")

# ---------------- Status priority ----------------
PRIORITY = {"cu":10, "vb":9, "pr":8, "dm":7, "sq":6, "mb":5, "ii":4, "cl":3, "t":2, "u":1}
STAGE_TO_CODE = {
    "Initial Interest": "ii",
    "Meeting Booked":   "mb",
    "Sales Qualified":  "sq",
    "Demo":             "dm",
    "Proposal":         "pr",
    "Verbal":           "vb",
    "Closed Lost":      "cl",
}

GARBAGE = {"subtotal","count","grand total","sum","total"}

# ---------------- Step 1: ICP master list ----------------
def load_icp(path):
    raw = pd.read_excel(path, header=None)
    # find header row containing "Account Name"
    header_row = None
    for i in range(20):
        row = raw.iloc[i].astype(str).tolist()
        if any("Account Name" in v for v in row):
            header_row = i
            break
    assert header_row is not None, "ICP: could not find header row"
    # use raw column indices: 1=state, 2=tier, 4=account name, 6=created, 7=owner
    df = raw.iloc[header_row+1:].copy()
    df.columns = list(range(raw.shape[1]))
    rename_map = {1:"state", 2:"tier", 4:"account", 6:"created", 7:"owner"}
    hdr = raw.iloc[header_row].astype(str).tolist()
    # auto-detect optional columns by header name
    for j, v in enumerate(hdr):
        vl = v.lower()
        if "account id (18)" in vl:
            rename_map[j] = "sf_id"
            print(f"  ICP: found Account ID (18) column at col {j} ({hdr[j]!r})")
        elif "population" in vl:
            rename_map[j] = "pop"
        elif "legacy" in vl:
            rename_map[j] = "icp_leg"
    if "sf_id" not in rename_map.values():
        print("  ICP: no 'Account ID (18)' column — 'id' field will be omitted from output")
    df = df.rename(columns=rename_map)
    # ffill state and tier (grouped rows)
    df["state"] = df["state"].ffill()
    df["tier"]  = df["tier"].ffill()
    # filter garbage rows (subtotal, total, count etc.)
    df = df[df["state"].notna()]
    df = df[~df["state"].astype(str).str.lower().isin(GARBAGE)]
    df = df[~df["tier"].astype(str).str.lower().isin(GARBAGE)]
    df = df[df["account"].notna()]
    df = df[df["account"].astype(str).str.lower() != "subtotal"]
    df = df[df["account"].astype(str).str.lower() != "total"]
    # Drop rows where account is the literal "Count" subtotal artifact (col 4 is account, col 3 is "Count")
    # Already handled above by checking state is not "subtotal"
    # tier: "Tier 1" -> "1"
    df["tier"] = df["tier"].astype(str).str.replace("Tier ", "", regex=False).str.strip()
    df["account"] = df["account"].astype(str).str.strip()
    df["state"] = df["state"].astype(str).str.strip()
    df["owner"] = df["owner"].astype(str).str.strip()
    if "sf_id" not in df.columns:
        df["sf_id"] = None
    return df.reset_index(drop=True)

icp = load_icp(ICP_FILE)
print(f"\nICP accounts after cleaning: {len(icp)}")
print("State distribution top 10:")
print(icp["state"].value_counts().head(10).to_string())

# Deduplicate by (account, state) — keep first
icp = icp.drop_duplicates(subset=["account","state"], keep="first").reset_index(drop=True)
print(f"After dedup: {len(icp)}")

# ---------------- Step 2: Pipeline ----------------
pipe = pd.read_excel(PIPE_FILE, header=11, usecols=[1,3,5,8,9,10],
                    names=["stage","opp","arr","owner","account","legacy"])
# Stage is grouped (only first row per stage has stage value) — ffill
pipe["stage"] = pipe["stage"].ffill()
# Then drop subtotal/total rows (account is NaN or "Subtotal"/"Total" appears in opp)
pipe = pipe[pipe["account"].notna()]
pipe = pipe[~pipe["stage"].astype(str).str.lower().isin(GARBAGE)]
pipe = pipe[~pipe["account"].astype(str).str.lower().isin(GARBAGE)]
pipe["account"] = pipe["account"].astype(str).str.strip()
pipe["stage"]   = pipe["stage"].astype(str).str.strip()
print(f"\nPipeline rows: {len(pipe)}")
print(pipe["stage"].value_counts().to_string())

# Map stages -> code
pipe["code"] = pipe["stage"].map(STAGE_TO_CODE)
# For accounts in pipeline, take HIGHEST priority code
pipe["prio"] = pipe["code"].map(PRIORITY).fillna(0)
pipe_sorted  = pipe.sort_values("prio", ascending=False)
pipe_best    = pipe_sorted.drop_duplicates(subset=["account"], keep="first")

# ---------------- Step 3: Customers ----------------
cust = pd.read_excel(CUST_FILE, header=10, usecols=[1,3,4,5,6],
                    names=["state","account","legacy","pop","arr"])
cust["state"] = cust["state"].ffill()
cust = cust[cust["account"].notna()]
cust = cust[~cust["state"].astype(str).str.lower().isin(GARBAGE)]
cust = cust[~cust["account"].astype(str).str.lower().isin(GARBAGE)]
cust["account"] = cust["account"].astype(str).str.strip()
print(f"\nCustomers: {len(cust)}")

# ---------------- Step 4: Meetings Booked ----------------
meet = pd.read_excel(MEET_FILE, header=12, usecols=[1,3,4,5],
                    names=["state","stage","owner","opp"])
meet["state"] = meet["state"].ffill()
meet = meet[meet["opp"].notna()]
meet = meet[~meet["state"].astype(str).str.lower().isin(GARBAGE)]
# Extract account name from opp name (opps have format "ACCOUNT NAME New Business Opportunity ...")
def acct_from_opp(opp):
    s = str(opp)
    # remove trailing " New Business Opportunity ..." or " New Business Opportunity 2025-..."
    s = re.sub(r"\s+New Business Opportunity.*$", "", s)
    s = re.sub(r"\s+Renewal.*$", "", s)
    s = re.sub(r"\s+Expansion.*$", "", s)
    return s.strip()
meet["account"] = meet["opp"].apply(acct_from_opp)
meet["code"]    = meet["stage"].map(STAGE_TO_CODE)
print(f"Meetings Booked rows: {len(meet)}")

# ---------------- Step 5: Activities ----------------
act = pd.read_excel(ACT_FILE, header=11, usecols=[1,3,4,5],
                   names=["state","atype","account","date"])
act["state"] = act["state"].ffill()
act = act[act["account"].apply(lambda x: isinstance(x, str))]
act = act[~act["state"].astype(str).str.lower().isin(GARBAGE)]
act["account"] = act["account"].astype(str).str.strip()
# parse date -> month YYYY-MM
def parse_month(d):
    if pd.isna(d): return None
    try:
        dt = pd.to_datetime(d, errors="coerce")
        if pd.isna(dt): return None
        return dt.strftime("%Y-%m")
    except Exception:
        return None
act["month"] = act["date"].apply(parse_month)
print(f"Activities rows: {len(act)}")

# Per-account latest month
act_latest = act.dropna(subset=["month"]).sort_values("month", ascending=False)\
                .drop_duplicates(subset=["account"], keep="first")[["account","month"]]
touched_accts = set(act_latest["account"].astype(str))
latest_month_by_acct = dict(zip(act_latest["account"], act_latest["month"]))
print(f"Distinct touched accounts (any time): {len(touched_accts)}")

# ---------------- Step 6: Load geocoords from geocode_master.csv (primary)
#                          with accounts_data.json as fallback ----------------
def load_prev_coords():
    coords = {}
    # Primary: geocode_master.csv — Google-geocoded, authoritative
    if os.path.exists(GEOCODE_CSV):
        try:
            gc = pd.read_csv(GEOCODE_CSV, dtype=str)
            for _, row in gc.iterrows():
                name = str(row.get("name", "")).strip()
                try:
                    la, lo = float(row["lat"]), float(row["lon"])
                except (ValueError, KeyError):
                    continue
                if name:
                    coords[name] = (la, lo, str(row.get("state", "")))
            print(f"  Geocode master loaded: {len(coords)} coords")
        except Exception as e:
            print(f"  Could not read geocode_master.csv: {e}")
    else:
        print("  No geocode_master.csv found")
    return coords

prev_coords = load_prev_coords()
print(f"\nPrev coords loaded: {len(prev_coords)}")

# fuzzy-match helpers
def norm(s):
    s = str(s).lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    # normalize "city of x" / "town of x" / "county of x" / "x city" / "x county" / "x town"
    s = re.sub(r"^(city|town|village|county|township) of\s+", "", s)
    s = re.sub(r"\s+(city|town|village|county|township)$", "", s)
    return s.strip()

prev_norm = {}
for k, v in prev_coords.items():
    prev_norm.setdefault(norm(k), []).append((k, v))

# State centroid fallback (rough)
STATE_CENTROIDS = {
    "Alabama":(32.7,-86.7),"Alaska":(64.0,-152.0),"Arizona":(34.0,-112.0),"Arkansas":(34.7,-92.4),
    "California":(36.7,-119.4),"Colorado":(39.0,-105.5),"Connecticut":(41.6,-72.7),"Delaware":(38.9,-75.5),
    "District of Columbia":(38.9,-77.0),"Florida":(28.0,-82.0),"Georgia":(32.6,-83.4),"Hawaii":(20.7,-156.5),
    "Idaho":(44.0,-114.7),"Illinois":(40.0,-89.0),"Indiana":(40.0,-86.3),"Iowa":(42.0,-93.5),"Kansas":(38.5,-98.4),
    "Kentucky":(37.6,-85.0),"Louisiana":(31.0,-92.0),"Maine":(45.4,-69.2),"Maryland":(39.0,-76.7),
    "Massachusetts":(42.3,-71.8),"Michigan":(44.3,-85.4),"Minnesota":(46.4,-94.6),"Mississippi":(33.0,-89.7),
    "Missouri":(38.5,-92.5),"Montana":(47.0,-110.0),"Nebraska":(41.5,-99.8),"Nevada":(39.0,-117.0),
    "New Hampshire":(43.7,-71.6),"New Jersey":(40.2,-74.7),"New Mexico":(34.5,-106.0),"New York":(43.0,-75.5),
    "North Carolina":(35.5,-79.4),"North Dakota":(47.5,-100.5),"Ohio":(40.3,-82.8),"Oklahoma":(35.5,-97.5),
    "Oregon":(44.0,-120.5),"Pennsylvania":(40.9,-77.7),"Rhode Island":(41.7,-71.5),"South Carolina":(33.9,-80.9),
    "South Dakota":(44.4,-100.2),"Tennessee":(35.8,-86.4),"Texas":(31.0,-99.0),"Utah":(39.5,-111.7),
    "Vermont":(44.0,-72.7),"Virginia":(37.8,-78.2),"Washington":(47.4,-120.5),"West Virginia":(38.5,-80.6),
    "Wisconsin":(44.5,-89.5),"Wyoming":(43.0,-107.5),
    # Canadian provinces (approximate)
    "Alberta":(54.0,-115.0),"British Columbia":(54.0,-125.0),"Manitoba":(54.0,-98.0),
    "New Brunswick":(46.5,-66.5),"Newfoundland and Labrador":(53.0,-60.0),"Nova Scotia":(45.0,-63.0),
    "Ontario":(50.0,-85.0),"Prince Edward Island":(46.5,-63.0),"Quebec":(53.0,-71.0),"Saskatchewan":(54.0,-106.0),
    "Northwest Territories":(64.5,-119.0),"Nunavut":(65.0,-90.0),"Yukon":(63.0,-135.0),
}

# ---------------- Step 7: Build accounts ----------------
NEW_THRESHOLD = "2026-03-01"  # accounts created on/after Mar 1 2026 = "new"

# index pipeline / customer / meeting by account name
pipe_by_acct = dict(zip(pipe_best["account"], pipe_best.to_dict("records")))
cust_by_acct = {}
for _, r in cust.iterrows():
    cust_by_acct[str(r["account"]).strip()] = r.to_dict()

meet_best = meet.dropna(subset=["code"]).sort_values("code", key=lambda c: c.map(PRIORITY).fillna(0), ascending=False)\
                 .drop_duplicates(subset=["account"], keep="first")
meet_by_acct = dict(zip(meet_best["account"], meet_best["code"]))

def lookup_coords(name, state):
    # exact name
    if name in prev_coords:
        la, lo, _ = prev_coords[name]
        return la, lo
    # case-insensitive
    for k, v in prev_coords.items():
        if k.lower() == name.lower():
            return v[0], v[1]
    # fuzzy norm
    key = norm(name)
    if key in prev_norm:
        for prev_name, (la, lo, prev_state) in prev_norm[key]:
            if prev_state and state and prev_state.lower() == state.lower():
                return la, lo
        # take first if state not matched
        prev_name, (la, lo, _) = prev_norm[key][0]
        return la, lo
    return None

new_count = 0
random_count = 0
out = []
for _, row in icp.iterrows():
    name = row["account"]
    state = row["state"]
    tier = row["tier"]
    owner = row["owner"]
    created = str(row.get("created","") or "")
    sf_id = str(row.get("sf_id","") or "").strip()
    # determine status
    code = "u"
    legacy = str(row.get("icp_leg","") or "").strip() or None
    arr_val = None
    pop_val = row.get("pop")
    # 1) customer
    if name in cust_by_acct:
        code = "cu"
        legacy = cust_by_acct[name].get("legacy")
        arr_val = cust_by_acct[name].get("arr")
    # 2) pipeline (overrides only if higher priority)
    if name in pipe_by_acct:
        pcode = pipe_by_acct[name].get("code")
        if pcode and PRIORITY.get(pcode,0) > PRIORITY.get(code,0):
            code = pcode
            legacy = pipe_by_acct[name].get("legacy") or legacy
            arr_val = pipe_by_acct[name].get("arr") or arr_val
        elif pcode == "cl" and code == "u":
            code = "cl"
    # 3) meeting booked from cold call (mb tier or higher)
    if name in meet_by_acct:
        mcode = meet_by_acct[name]
        if PRIORITY.get(mcode,0) > PRIORITY.get(code,0):
            code = mcode
    # 4) touched
    if code in ("u","cl") and name in touched_accts:
        # if cl and touched, keep cl as it has higher priority? cl=3, t=2 -> cl wins
        if code == "u":
            code = "t"
    # build account dict
    o = {"a": name, "s": state, "t": str(tier), "o": owner, "st": code, "src": "bdr"}
    if sf_id and sf_id.lower() not in ("nan", "none", ""):
        o["id"] = sf_id
    coords = lookup_coords(name, state)
    if coords:
        la, lo = coords
    else:
        # random within state
        c = STATE_CENTROIDS.get(state)
        if c:
            la = c[0] + random.uniform(-0.6, 0.6)
            lo = c[1] + random.uniform(-0.6, 0.6)
            random_count += 1
        else:
            la, lo = 39.5, -98.0
            random_count += 1
    o["la"] = round(la, 4)
    o["lo"] = round(lo, 4)
    if pop_val is not None and not (isinstance(pop_val, float) and pd.isna(pop_val)):
        try:
            o["pop"] = int(float(pop_val))
        except (ValueError, TypeError):
            pass
    if legacy and str(legacy) != "nan":
        o["leg"] = str(legacy)
    if arr_val is not None and not (isinstance(arr_val, float) and pd.isna(arr_val)):
        try:
            o["arr"] = int(float(arr_val))
        except Exception:
            pass
    if code == "t" and name in latest_month_by_acct:
        o["ld"] = latest_month_by_acct[name]
    # new flag
    try:
        cdt = pd.to_datetime(created, errors="coerce")
        if pd.notna(cdt) and cdt.strftime("%Y-%m-%d") >= NEW_THRESHOLD:
            o["n"] = 1
            new_count += 1
    except Exception:
        pass
    out.append(o)

print(f"\nBuilt {len(out)} accounts. Random coords (new accts): {random_count}. New flag: {new_count}.")

# ---------------- Step 8: Status distribution ----------------
from collections import Counter
status_counts = Counter(a["st"] for a in out)
labels = {"cu":"Customer","vb":"Verbal","pr":"Proposal","dm":"Demo","sq":"SQO","mb":"Meeting Booked",
          "ii":"Initial Interest","cl":"Closed Lost","t":"Touched","u":"Untouched"}
print("\nStatus distribution:")
for k in ["cu","vb","pr","dm","sq","mb","ii","cl","t","u"]:
    print(f"  {labels[k]:18s} {status_counts.get(k,0):>6}")
print(f"  {'TOTAL':18s} {len(out):>6}")

# ---------------- Step 9: Write JSON ----------------
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
print(f"\nWrote {OUT_JSON} ({os.path.getsize(OUT_JSON):,} bytes)")
