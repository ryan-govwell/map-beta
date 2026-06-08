#!/usr/bin/env python3
"""
process_activities.py
Processes a Salesforce activity report into a clean per-account activity CSV.

Filters to BDR team only (non-BDR rows excluded — same logic as territory-v2).
Aggregates to one row per account with:
  - Account ID      (join key)
  - Total Calls     (BDR calls only)
  - Last Call Date  (most recent BDR call, YYYY-MM-DD)

This output is joined by merge.py to classify accounts as Touched (t)
when they have BDR activity but no open pipeline.

Usage:
    python3 pipeline/process_activities.py \
        --input   ~/Downloads/<sf-activity-report>.csv \
        --output  pipeline/activities.csv
"""

import argparse
import csv
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from constants import BDR_TEAM

DATE_FORMATS = ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y']


def parse_date(val):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def main():
    parser = argparse.ArgumentParser(description='Process Salesforce activity report.')
    parser.add_argument('--input',  required=True, help='Path to SF activity report CSV')
    parser.add_argument('--output', required=True, help='Output CSV path')
    args = parser.parse_args()

    with open(args.input, newline='', encoding='latin-1') as f:
        all_rows = list(csv.DictReader(f))

    # Auto-detect column names (matches territory-v2 approach)
    sample   = all_rows[0] if all_rows else {}
    col_rep  = 'Created By'    if 'Created By'    in sample else 'Assigned'
    col_date = 'Activity Date' if 'Activity Date' in sample else 'Date'

    bdr_rows = [r for r in all_rows if r[col_rep].strip() in BDR_TEAM]
    excluded = Counter(r[col_rep].strip() for r in all_rows if r[col_rep].strip() not in BDR_TEAM)
    if excluded:
        print(f'Excluded {sum(excluded.values())} non-BDR rows from: {dict(excluded)}')

    # Aggregate per account
    accounts = defaultdict(lambda: {'Account ID': '', 'Account Name': '', 'dates': [], 'calls': 0, 'rep_counts': Counter()})
    for row in bdr_rows:
        key  = row['Account ID'].strip()
        acct = accounts[key]
        acct['Account ID']   = key
        acct['Account Name'] = row['Account Name'].strip()
        acct['calls'] += 1
        acct['rep_counts'][row[col_rep].strip()] += 1
        d = parse_date(row.get(col_date, ''))
        if d:
            acct['dates'].append(d)

    # Determine rep order by total volume (most active first)
    all_reps = [rep for rep, _ in Counter(r[col_rep] for r in bdr_rows).most_common()]

    rows_out = []
    for acct in accounts.values():
        row = {
            'Account ID':    acct['Account ID'],
            'Account Name':  acct['Account Name'],
            'Total Calls':   acct['calls'],
            'Last Call Date': max(acct['dates']).strftime('%Y-%m-%d') if acct['dates'] else '',
        }
        for rep in all_reps:
            row[f'Calls - {rep}'] = acct['rep_counts'].get(rep, '') or ''
        rows_out.append(row)

    rows_out.sort(key=lambda r: -r['Total Calls'])

    FIELDNAMES = (
        ['Account ID', 'Account Name', 'Total Calls', 'Last Call Date'] +
        [f'Calls - {r}' for r in all_reps]
    )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f'Accounts with BDR activity: {len(rows_out)}')
    print(f'BDR call rows processed: {len(bdr_rows)} of {len(all_rows)} total')
    print(f'Reps tracked ({len(all_reps)}): {", ".join(all_reps)}')


if __name__ == '__main__':
    main()
