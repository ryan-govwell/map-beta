#!/usr/bin/env python3
"""
build-map.py — GovWell Territory Dashboard assembler.

Takes the template + a processed accounts JSON and writes the final bdr-map.html
with all three placeholders substituted. Uses paths relative to this script so
it works from any session without path fixups.

Inputs  (must exist in the same folder as this script):
  - bdr-map-template.html   The template with %%ACCOUNTS_JSON%%,
                            %%DATA_VERSION%%, %%DATA_REFRESHED%% placeholders.
  - accounts_data.json      Compact account list produced by data_processor.py.
  - All Data for Map/       Folder; most recent ICP export's stem-suffix is used
                            as the data version string.

Output:
  - bdr-map.html            Ready to push to GitHub.

Usage:
  python3 build-map.py
"""
import json, pathlib, sys
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
TEMPL_PATH = HERE / 'bdr-map-template.html'
JSON_PATH  = HERE / 'accounts_data.json'
OUT_PATH   = HERE / 'bdr-map.html'
DATA_DIR   = HERE / 'All Data for Map'

if not TEMPL_PATH.exists():
    sys.exit(f'❌ Missing template: {TEMPL_PATH}')
if not JSON_PATH.exists():
    sys.exit(f'❌ Missing accounts JSON: {JSON_PATH}\n'
             f'   Run data_processor.py first to generate accounts_data.json.')

templ = TEMPL_PATH.read_text()
accts = JSON_PATH.read_text().strip()

# Validate JSON before injecting (catches truncated or corrupt files).
try:
    parsed = json.loads(accts)
    if not isinstance(parsed, list) or len(parsed) < 100:
        sys.exit(f'❌ accounts_data.json looks wrong ({len(parsed)} items). Expected >10k.')
except Exception as e:
    sys.exit(f'❌ accounts_data.json is not valid JSON: {e}')

# Data version: use the latest ICP export's filename suffix (e.g., "37" from
# "ICP Accounts by State_ARC-37.xlsx"). Falls back to "latest" if no exports.
ver = 'latest'
if DATA_DIR.is_dir():
    icp = sorted(DATA_DIR.glob('ICP Accounts by State_ARC-*.xlsx'))
    if icp:
        ver = icp[-1].stem.split('-')[-1]

# Human-readable refresh timestamp, e.g. "Apr 23, 2026 · 11:55pm".
now = datetime.now()
h = now.hour % 12 or 12
ampm = 'am' if now.hour < 12 else 'pm'
refreshed = now.strftime('%b ') + str(now.day) + now.strftime(', %Y') + f' · {h}:{now.minute:02d}{ampm}'

# Assemble: three template placeholders, string-replace (NOT regex — the JSON
# contains characters that would be interpreted as regex metacharacters).
out = (templ
       .replace('%%ACCOUNTS_JSON%%', accts)
       .replace('%%DATA_VERSION%%',  ver)
       .replace('%%DATA_REFRESHED%%', refreshed))

# Sanity: no placeholders should remain.
for ph in ('%%ACCOUNTS_JSON%%', '%%DATA_VERSION%%', '%%DATA_REFRESHED%%'):
    if ph in out:
        sys.exit(f'❌ Placeholder {ph} was not substituted — template mismatch.')

OUT_PATH.write_text(out)
print(f'✅ wrote {len(out):,} bytes to {OUT_PATH.name}')
print(f'   version: {ver}')
print(f'   refreshed: {refreshed}')
print(f'   accounts: {len(parsed):,}')
