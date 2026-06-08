#!/usr/bin/env python3
"""
process_contacts.py
Cleans a Salesforce contacts export and classifies each contact by function.

Uses the same classification logic as territory-v2. Contacts are stored
per account and loaded by merge.py into accounts_data.json.

Function codes (compact keys used in JSON output):
  bp — Building / Permitting / Inspections
  pz — Planning & Zoning
  ce — Code Enforcement
  ot — Other

Usage:
    python3 pipeline/process_contacts.py \
        --input   ~/Downloads/<sf-contacts-report>.csv \
        --output  pipeline/contacts.csv
"""

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


FN_ORDER = ['bp', 'pz', 'ce', 'ot']

FN_LABELS = {
    'bp': 'Building / Permitting / Inspections',
    'pz': 'Planning & Zoning',
    'ce': 'Code Enforcement',
    'ot': 'Other',
}


def classify(title: str) -> str:
    t = title.lower().strip()
    if ('code enforcement' in t or 'code compliance' in t) and 'building code' not in t:
        return 'ce'
    if any(k in t for k in [
        'building', 'permit', 'inspect', 'plans examiner', 'plan review',
        'plan examiner', 'floodplain', 'construction code', 'cbo',
    ]):
        return 'bp'
    if any(k in t for k in [
        'planning', 'planner', 'zoning', 'growth management',
        'community development', 'development services',
        'land use', 'land development', 'neighborhood development',
        'gis ', ' gis', 'geographic information',
    ]):
        return 'pz'
    return 'ot'


def parse_date(val: str) -> str:
    val = val.strip()
    if not val:
        return ''
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y'):
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return ''


def main():
    parser = argparse.ArgumentParser(description='Process Salesforce contacts report.')
    parser.add_argument('--input',  required=True, help='Path to SF contacts CSV')
    parser.add_argument('--output', required=True, help='Output CSV path')
    args = parser.parse_args()

    rows_out = []
    skipped  = 0

    with open(args.input, newline='', encoding='latin-1') as f:
        for row in csv.DictReader(f):
            acct_id = row.get('Account ID', '').strip()
            first   = row.get('First Name', '').strip()
            last    = row.get('Last Name',  '').strip()
            name    = f'{first} {last}'.strip()
            if not acct_id or not name:
                skipped += 1
                continue

            rows_out.append({
                'Account ID':    acct_id,
                'Full Name':     name,
                'Title':         row.get('Title', '').strip(),
                'Function':      classify(row.get('Title', '')),
                'Last Activity': parse_date(row.get('Last Activity', '')),
            })

    # Sort by function priority then by name
    fn_rank = {fn: i for i, fn in enumerate(FN_ORDER)}
    rows_out.sort(key=lambda r: (fn_rank[r['Function']], r['Full Name']))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Account ID', 'Full Name', 'Title', 'Function', 'Last Activity'])
        writer.writeheader()
        writer.writerows(rows_out)

    funcs = Counter(r['Function'] for r in rows_out)
    has_act = sum(1 for r in rows_out if r['Last Activity'])
    print(f'Contacts written:    {len(rows_out)}')
    print(f'Skipped (no ID/name): {skipped}')
    print(f'With last activity:  {has_act}')
    print('By function:')
    for fn in FN_ORDER:
        print(f'  {fn}: {FN_LABELS[fn]:40s} {funcs[fn]}')


if __name__ == '__main__':
    main()
