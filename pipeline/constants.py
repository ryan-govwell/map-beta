"""Shared constants for the GovWell territory map pipeline."""

# Current BDR roster + former team members — used to filter activity rows.
# Non-BDR names (AEs, CS, etc.) are excluded from activity processing.
BDR_TEAM = {
    'Ryan Minter', 'Nick Martino', 'Ali Cohen', 'Alicia Gopal',
    'Lucy Nemerov', 'Hugh Bargeron', 'Sydney Ireland', 'Emily Murnane',
    'Ben Laddis', 'Blake Anderson', 'Mihir Shah', 'Maia Golub',
    'Catherine Silvestri',
    # Former / adjacent BDR team members
    'Jenny Allison', 'Leila Assil', 'Joe del Rosario', 'Quinzel Perry',
    'Granger West', 'Shane Lieberman', 'Andy Blakely',
}

ARR_PLACEHOLDER = 23_000.0

TOP_OF_FUNNEL_STAGES = {'Initial Interest', 'Meeting Booked'}

STAGE_PRIORITY = {
    'Verbal':           6,
    'Proposal':         5,
    'Demo':             4,
    'Sales Qualified':  3,
    'Meeting Booked':   2,
    'Initial Interest': 1,
}

SQO_POINTS = {
    'Tier S': 2.0,
    'Tier 1': 1.5,
    'Tier 2': 1.0,
    'Tier 3': 0.75,
}

STATE_CODES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY',
}
