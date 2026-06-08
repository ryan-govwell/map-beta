#!/usr/bin/env python3
"""
process_pipeline.py
Cleans and classifies the Salesforce opportunities report.

One row per opportunity — deduplication to one opp per account happens in merge.py.
ARR is stored as a raw number (no $ formatting) so merge.py can write it
as a numeric JSON field without string-conversion issues.

Signal labels (used in merge.py to set map status codes):
  Won        — Closed Won
  Mid Funnel — Open, stage not in TOP_OF_FUNNEL_STAGES (SQ, Demo, Proposal, Verbal)
  Top Funnel — Open, stage in TOP_OF_FUNNEL_STAGES (Initial Interest, Meeting Booked)
  Lost       — Closed Lost

Usage:
    python3 pipeline/process_pipeline.py \
        --input   ~/Downloads/<sf-opps-report>.csv \
        --output  pipeline/pipeline.csv
"""

import argparse
import csv
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from constants import ARR_PLACEHOLDER, TOP_OF_FUNNEL_STAGES


FIELDNAMES = [
    'Account ID', 'Account Name',
    'Opp Status', 'Stage', 'Signal', 'Funnel Position',
    'Sourced By', 'Discovery Call Date', 'Created Date',
    'ARR',
]


def opp_status(row):
    if row['Closed Won Stage Date'].strip():
        return 'Closed Won'
    if row['Closed Lost Stage Date'].strip():
        return 'Closed Lost'
    return 'Open'


def signal(status, stage):
    if status == 'Closed Won':
        return 'Won'
    if status == 'Closed Lost':
        return 'Lost'
    return 'Top Funnel' if stage in TOP_OF_FUNNEL_STAGES else 'Mid Funnel'


def funnel_position(status, stage):
    if status != 'Open':
        return ''
    return 'Top of Funnel' if stage in TOP_OF_FUNNEL_STAGES else 'Mid Funnel'


def parse_arr(val):
    """Returns numeric ARR or empty string. Strips placeholder value."""
    try:
        f = float(val)
        return '' if f == ARR_PLACEHOLDER else str(int(f))
    except (ValueError, TypeError):
        return ''


def main():
    parser = argparse.ArgumentParser(description='Process Salesforce opportunities report.')
    parser.add_argument('--input',  required=True, help='Path to SF opportunities CSV')
    parser.add_argument('--output', required=True, help='Output CSV path')
    args = parser.parse_args()

    rows_out = []

    with open(args.input, newline='', encoding='latin-1') as f:
        for row in csv.DictReader(f):
            acct_id = row.get('Account ID', '').strip()
            if not acct_id:
                continue

            status = opp_status(row)
            stage  = row['Stage'].strip() if status == 'Open' else ''

            rows_out.append({
                'Account ID':          acct_id,
                'Account Name':        row.get('Account Name', '').strip(),
                'Opp Status':          status,
                'Stage':               stage,
                'Signal':              signal(status, stage),
                'Funnel Position':     funnel_position(status, stage),
                'Sourced By':          row.get('Discovery Call Booked By', '').strip(),
                'Discovery Call Date': row.get('Discovery Call Date', '').strip(),
                'Created Date':        row.get('Created Date', '').strip(),
                'ARR':                 parse_arr(row.get('Annual Recurring Revenue (ARR)', '')),
            })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_out)

    signals = Counter(r['Signal'] for r in rows_out)
    print(f'Opportunities written: {len(rows_out)}')
    for s, n in signals.most_common():
        print(f'  {s}: {n}')


if __name__ == '__main__':
    main()
