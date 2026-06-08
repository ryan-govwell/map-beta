#!/usr/bin/env python3
"""
process_accounts.py
Processes the combined Salesforce accounts report into a clean accounts CSV.

Account Tier is read directly from the report (not derived from population).
Geo coordinates are looked up by account name + state code from geo_lookup.json.

Usage:
    python3 pipeline/process_accounts.py \
        --accounts  <path to SF accounts CSV> \
        --geo       <path to geo_lookup.json> \
        --output    <output CSV path>
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import SQO_POINTS, STATE_CODES


FIELDNAMES = [
    'Account ID', 'Account Name', 'State', 'Entity Type', 'Owner',
    'Population', 'Account Status', 'Account Tier', 'SQO Points',
    'Legacy Community Development Software',
    'Lat', 'Lng', 'Starbridge Buyer ID',
]


def load_geo(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Process Salesforce accounts report.')
    parser.add_argument('--accounts', required=True, help='Path to SF accounts CSV')
    parser.add_argument('--geo',      required=True, help='Path to geo_lookup.json')
    parser.add_argument('--output',   required=True, help='Output CSV path')
    args = parser.parse_args()

    geo = load_geo(args.geo)
    rows_out      = []
    unmatched_geo = []

    with open(args.accounts, newline='', encoding='latin-1') as f:
        for row in csv.DictReader(f):
            acct_id = row.get('Account ID', '').strip()
            name    = row.get('Account Name', '').strip()
            if not acct_id or not name:
                continue

            state_name  = row.get('Billing State/Province', '').strip()
            state_code  = STATE_CODES.get(state_name, '')
            tier        = row.get('Account Tier', '').strip()

            key          = name.lower()
            state_suffix = f', {state_code.lower()}' if state_code else ''
            coords       = geo.get(key + state_suffix, geo.get(key, {}))

            if not coords:
                unmatched_geo.append(name)

            rows_out.append({
                'Account ID':   acct_id,
                'Account Name': name,
                'State':        state_name,
                'Entity Type':  row.get('Entity Type', '').strip(),
                'Owner':        row.get('Account Owner', '').strip(),
                'Population':   row.get('Population', '').strip(),
                'Account Status': row.get('Account Status', '').strip(),
                'Account Tier': tier,
                'SQO Points':   SQO_POINTS.get(tier, ''),
                'Legacy Community Development Software': row.get('Legacy Community Development Software', '').strip(),
                'Lat':          coords.get('lat', ''),
                'Lng':          coords.get('lng', ''),
                'Starbridge Buyer ID': row.get('Starbridge Buyer ID', '').strip(),
            })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f'Accounts written: {len(rows_out)}')
    if unmatched_geo:
        print(f'WARNING — No coordinates for {len(unmatched_geo)} accounts:')
        for n in unmatched_geo[:20]:
            print(f'  {n}')
        if len(unmatched_geo) > 20:
            print(f'  ... and {len(unmatched_geo) - 20} more')


if __name__ == '__main__':
    main()
