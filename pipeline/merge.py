#!/usr/bin/env python3
"""
merge.py
Joins accounts + pipeline + activities into accounts_data.json for the map.

Status code priority:
  1. Customer (Account Status = Implementation/1+ Module Live/All Modules Live) → cu
  2. Signal = 'Won'        → cu
  3. Signal = 'Mid Funnel' → mf
  4. Signal = 'Top Funnel' → tf
  5. Signal = 'Lost'       → cl
  6. No pipeline + has BDR activity → t  (Touched)
  7. No pipeline + no activity       → u  (silent — no label on map)

Usage:
    python3 pipeline/merge.py \
        --accounts    pipeline/accounts.csv \
        --pipeline    pipeline/pipeline.csv \
        --activities  pipeline/activities.csv \
        --output      accounts_data.json

--pipeline and --activities are optional; missing files degrade gracefully.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import STAGE_PRIORITY


TIER_MAP = {
    'Tier S': 'S',
    'Tier 1': '1',
    'Tier 2': '2',
    'Tier 3': '3',
}

CUSTOMER_STATUSES = {'All Modules Live', '1+ Module Live', 'Implementation'}

SIGNAL_TO_STATUS = {
    'Won':        'cu',
    'Mid Funnel': 'mf',
    'Top Funnel': 'tf',
    'Lost':       'cl',
}

ACCT_STATUS_FALLBACK = {
    'Recent Competitor Purchase': 'cl',
    'Churned Customer':           'cl',
    'Nurture':                    'u',
    'Unviable':                   'u',
    'Cold':                       'u',
    '':                           'u',
}

NO_LEGACY = {'', 'None Visible', 'None'}


def load_pipeline(path):
    """Returns dict of Account ID → best opp row.

    Priority: Open (sorted by stage priority, highest wins) > Closed Won > Closed Lost.
    Adds 'Previously Lost' key when an open opp coexists with a lost opp.
    """
    raw = defaultdict(list)
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            acct_id = row.get('Account ID', '').strip()
            if acct_id:
                raw[acct_id].append(row)

    result = {}
    for acct_id, opps in raw.items():
        open_opps = [o for o in opps if o['Opp Status'] == 'Open']
        won_opps  = [o for o in opps if o['Opp Status'] == 'Closed Won']
        lost_opps = [o for o in opps if o['Opp Status'] == 'Closed Lost']

        if open_opps:
            open_opps.sort(key=lambda o: STAGE_PRIORITY.get(o['Stage'], 0), reverse=True)
            primary = dict(open_opps[0])
            primary['Previously Lost'] = 'Yes' if lost_opps else ''
            result[acct_id] = primary
        elif won_opps:
            result[acct_id] = dict(won_opps[0])
        elif lost_opps:
            result[acct_id] = dict(lost_opps[0])

    return result


def load_activities(path):
    """Returns dict of Account ID → activity data including per-rep counts."""
    result = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            acct_id = row.get('Account ID', '').strip()
            if not acct_id:
                continue
            reps = {}
            for key, val in row.items():
                if key.startswith('Calls - ') and val:
                    try:
                        n = int(val)
                        if n > 0:
                            reps[key[8:]] = n  # strip "Calls - " prefix
                    except ValueError:
                        pass
            result[acct_id] = {
                'Total Calls':   int(row.get('Total Calls', 0) or 0),
                'Last Call Date': row.get('Last Call Date', '').strip(),
                'reps':          reps,
            }
    return result


FN_ORDER = ['bp', 'pz', 'ce', 'ot']

def load_contacts(path):
    """Returns dict of Account ID → list of [name, title, fn_code, last_activity]."""
    from collections import defaultdict
    raw = defaultdict(list)
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            acct_id = row.get('Account ID', '').strip()
            if acct_id:
                raw[acct_id].append([
                    row.get('Full Name', '').strip(),
                    row.get('Title',     '').strip(),
                    row.get('Function',  'ot'),
                    row.get('Last Activity', '').strip(),
                ])
    # Sort each account's contacts by function priority then name
    fn_rank = {fn: i for i, fn in enumerate(FN_ORDER)}
    for acct_id in raw:
        raw[acct_id].sort(key=lambda c: (fn_rank.get(c[2], 9), c[0]))
    return dict(raw)


def resolve_status(acct_status, opp, activity):
    if acct_status in CUSTOMER_STATUSES:
        return 'cu'
    if opp:
        return SIGNAL_TO_STATUS.get(opp.get('Signal', ''), 'u')
    if activity:
        return 't'
    return ACCT_STATUS_FALLBACK.get(acct_status, 'u')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--accounts',   required=True)
    parser.add_argument('--pipeline',   default='')
    parser.add_argument('--activities', default='')
    parser.add_argument('--contacts',   default='')
    parser.add_argument('--output',     required=True)
    args = parser.parse_args()

    pipeline_path   = args.pipeline   or str(Path(__file__).parent / 'pipeline.csv')
    activities_path = args.activities or str(Path(__file__).parent / 'activities.csv')
    contacts_path   = args.contacts   or str(Path(__file__).parent / 'contacts.csv')

    opps = load_pipeline(pipeline_path) if Path(pipeline_path).exists() else {}
    if not opps:
        print('WARNING — no pipeline data; status will use Account Status fallback')

    acts = load_activities(activities_path) if Path(activities_path).exists() else {}
    if not acts:
        print('WARNING — no activity data; Touched classification unavailable')

    contacts = load_contacts(contacts_path) if Path(contacts_path).exists() else {}
    if not contacts:
        print('WARNING — no contact data')

    records       = []
    skipped       = 0
    status_counts = defaultdict(int)

    with open(args.accounts, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            lat = row.get('Lat', '').strip()
            lng = row.get('Lng', '').strip()
            if not lat or not lng:
                skipped += 1
                continue

            acct_id    = row['Account ID']
            acct_st    = row.get('Account Status', '').strip()
            opp        = opps.get(acct_id)
            activity   = acts.get(acct_id)
            acct_contacts = contacts.get(acct_id)
            status_code = resolve_status(acct_st, opp, activity)
            legacy     = row.get('Legacy Community Development Software', '').strip()

            status_counts[status_code] += 1

            rec = {
                'a':   row['Account Name'],
                's':   row['State'],
                't':   TIER_MAP.get(row.get('Account Tier', ''), ''),
                'o':   row['Owner'],
                'st':  status_code,
                'src': 'bdr',
                'id':  acct_id,
                'la':  float(lat),
                'lo':  float(lng),
            }

            et = row.get('Entity Type', '').strip()
            if et:
                rec['et'] = et

            pop_raw = row.get('Population', '').strip()
            if pop_raw:
                try:
                    rec['pop'] = int(pop_raw)
                except ValueError:
                    pass

            if legacy and legacy not in NO_LEGACY:
                rec['leg'] = legacy

            if opp:
                arr_raw = opp.get('ARR', '').strip()
                if arr_raw:
                    try:
                        rec['arr'] = int(arr_raw)
                    except ValueError:
                        pass
                if opp.get('Previously Lost') == 'Yes':
                    rec['pl'] = 1

            if activity:
                rec['tc'] = activity['Total Calls']
                if activity['Last Call Date']:
                    rec['lcd'] = activity['Last Call Date']
                if activity['reps']:
                    rec['reps'] = sorted(activity['reps'].items(), key=lambda x: -x[1])

            if acct_contacts:
                rec['contacts'] = acct_contacts

            sb = row.get('Starbridge Buyer ID', '').strip()
            if sb:
                rec['sb'] = sb

            records.append(rec)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(records, f, separators=(',', ':'))

    print(f'Records written: {len(records)}')
    if skipped:
        print(f'Skipped (no coordinates): {skipped}')
    print('Status breakdown:')
    for code, n in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f'  {code}: {n}')


if __name__ == '__main__':
    main()
