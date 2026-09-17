"""
Generates a synthetic B2B SaaS CRM opportunity dataset shaped like a
Salesforce opportunity export, with realistic patterns baked in on purpose
(segment/source affect win rate and cycle length) so the SQL analysis has
something real to find.

THIS DATA IS SYNTHETIC. Real Salesforce/CRM exports aren't public - this is
built to demonstrate the analysis, not to claim real findings about any
company. Said explicitly here and in the README, not buried.

Writes data/opportunities.csv.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
ROOT = Path(__file__).resolve().parent
N = 650

STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]  # pre-close funnel
SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.5, 0.35, 0.15]
SEGMENT_AMOUNT = {"SMB": (3_000, 1_500), "Mid-Market": (18_000, 7_000), "Enterprise": (85_000, 35_000)}
SEGMENT_CYCLE_DAYS = {"SMB": (18, 8), "Mid-Market": (45, 15), "Enterprise": (95, 30)}
SEGMENT_WIN_RATE = {"SMB": 0.42, "Mid-Market": 0.33, "Enterprise": 0.24}

SOURCES = ["Inbound", "Outbound", "Partner", "Event"]
SOURCE_WEIGHTS = [0.40, 0.30, 0.15, 0.15]
SOURCE_WIN_MULT = {"Inbound": 1.15, "Outbound": 0.75, "Partner": 1.35, "Event": 0.95}

REPS = [f"Rep {c}" for c in "ABCDEFGH"]
REP_SKILL = dict(zip(REPS, RNG.normal(1.0, 0.18, size=len(REPS))))

LOSS_REASONS_STD = ["Price", "Competitor", "No Budget", "Timing", "No Decision"]
LOSS_REASON_WEIGHTS = {
    "SMB": [0.40, 0.20, 0.15, 0.15, 0.10],
    "Mid-Market": [0.30, 0.25, 0.20, 0.15, 0.10],
    "Enterprise": [0.15, 0.20, 0.30, 0.25, 0.10],
}

START_DATE = pd.Timestamp("2025-10-01")
END_DATE = pd.Timestamp("2026-09-01")

rows = []
for i in range(N):
    segment = RNG.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
    source = RNG.choice(SOURCES, p=SOURCE_WEIGHTS)
    owner = RNG.choice(REPS)

    amt_mean, amt_sd = SEGMENT_AMOUNT[segment]
    amount = max(500, RNG.normal(amt_mean, amt_sd))

    cyc_mean, cyc_sd = SEGMENT_CYCLE_DAYS[segment]
    cycle_days = max(3, int(RNG.normal(cyc_mean, cyc_sd)))

    created = START_DATE + pd.Timedelta(days=int(RNG.uniform(0, (END_DATE - START_DATE).days - cycle_days - 30)))

    win_prob = np.clip(SEGMENT_WIN_RATE[segment] * SOURCE_WIN_MULT[source] * REP_SKILL[owner], 0.05, 0.85)

    still_open = RNG.random() < 0.15
    if still_open:
        outcome = "Open"
        furthest_stage_idx = int(RNG.integers(0, len(STAGES)))
        close_date = pd.NaT
        loss_reason = None
    else:
        won = RNG.random() < win_prob
        close_date = created + pd.Timedelta(days=cycle_days)
        if won:
            outcome = "Won"
            furthest_stage_idx = len(STAGES) - 1
            loss_reason = None
        else:
            outcome = "Lost"
            # deals that lose tend to die somewhere in the funnel, weighted later-stage
            furthest_stage_idx = int(RNG.choice(len(STAGES), p=[0.15, 0.25, 0.30, 0.30]))
            loss_reason = RNG.choice(LOSS_REASONS_STD, p=LOSS_REASON_WEIGHTS[segment])

    rows.append(
        {
            "opp_id": f"OPP-{i+1:05d}",
            "segment": segment,
            "lead_source": source,
            "owner": owner,
            "amount": round(amount, 2),
            "created_date": created.date().isoformat(),
            "close_date": close_date.date().isoformat() if pd.notna(close_date) else "",
            "cycle_days": cycle_days if outcome != "Open" else None,
            "furthest_stage": STAGES[furthest_stage_idx],
            "furthest_stage_idx": furthest_stage_idx,
            "outcome": outcome,
            "loss_reason": loss_reason,
        }
    )

df = pd.DataFrame(rows)
(ROOT / "data").mkdir(exist_ok=True)
df.to_csv(ROOT / "data" / "opportunities.csv", index=False)
print(f"Wrote {len(df)} synthetic opportunities -> data/opportunities.csv")
print(df["outcome"].value_counts())
