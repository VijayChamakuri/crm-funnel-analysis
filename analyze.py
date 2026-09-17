"""
Runs queries.sql against data/opportunities.csv (loaded into an in-memory
SQLite db), saves each result to output/<name>.csv, builds two charts, and
writes an exec-style summary with numbers pulled straight from the query
results (not hand-typed).
"""

import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def load_named_queries(sql_path: Path) -> dict[str, str]:
    text = sql_path.read_text()
    blocks = re.split(r"-- name:\s*(\w+)\n", text)[1:]
    return {blocks[i]: blocks[i + 1].strip().rstrip(";") for i in range(0, len(blocks), 2)}


def validate(df: pd.DataFrame) -> None:
    """Cheap sanity checks before any query runs against this data."""
    assert len(df) > 0, "opportunities.csv is empty"
    required_cols = ["opp_id", "segment", "lead_source", "owner", "amount", "outcome"]
    assert not df[required_cols].isnull().any().any(), "Null values found in a required column"
    assert (df["amount"] > 0).all(), "Non-positive amount found"
    assert df["opp_id"].is_unique, "Duplicate opp_id found"
    assert set(df["outcome"].unique()) <= {"Won", "Lost", "Open"}, f"Unexpected outcome value(s): {set(df['outcome'].unique())}"
    closed = df[df["outcome"] != "Open"]
    assert closed["cycle_days"].notna().all(), "Closed opportunities missing cycle_days"


def main() -> None:
    df = pd.read_csv(ROOT / "data" / "opportunities.csv")
    validate(df)
    conn = sqlite3.connect(":memory:")
    df.to_sql("opportunities", conn, index=False)

    queries = load_named_queries(ROOT / "queries.sql")
    results = {}
    for name, sql in queries.items():
        result = pd.read_sql_query(sql, conn)
        result.to_csv(OUT / f"{name}.csv", index=False)
        results[name] = result
        print(f"\n== {name} ==")
        print(result.to_string(index=False))

    # --- Chart 1: funnel, with stage-to-stage conversion rates labeled ---
    funnel = results["funnel_by_stage"]
    conversion_pct = [100.0] + [
        round(100 * funnel["reached"].iloc[i] / funnel["reached"].iloc[i - 1], 1)
        for i in range(1, len(funnel))
    ]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(funnel["stage"], funnel["reached"], color="#3b82f6")
    ax.set_title("Pipeline Funnel: Opportunities Reaching Each Stage")
    ax.set_ylabel("Opportunities")
    for i, (v, pct) in enumerate(zip(funnel["reached"], conversion_pct)):
        label = str(v) if i == 0 else f"{v}\n({pct}% of prior stage)"
        ax.text(i, v + 8, label, ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "funnel.png", dpi=150)

    # --- Chart 2: win rate by segment ---
    seg = results["win_rate_by_segment"]
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    ax2.bar(seg["segment"], seg["win_rate_pct"], color="#10b981")
    ax2.set_title("Win Rate by Segment")
    ax2.set_ylabel("Win rate (%)")
    for i, v in enumerate(seg["win_rate_pct"]):
        ax2.text(i, v + 0.5, f"{v}%", ha="center")
    fig2.tight_layout()
    fig2.savefig(OUT / "win_rate_by_segment.png", dpi=150)

    # --- Exec summary ---
    seg_sorted = seg.sort_values("win_rate_pct", ascending=False)
    src = results["win_rate_by_source"].sort_values("win_rate_pct", ascending=False)
    reps = results["rep_performance"].sort_values("won_amount", ascending=False)
    # Only compare drop-offs across the pre-close pipeline stages; "Closed Won"
    # is the outcome, not a stage a deal can bottleneck *at*, so it's excluded
    # from "biggest drop-off" (which should point at a fixable process stage).
    pipeline_stages = funnel[funnel["stage"] != "Closed Won"].copy()
    pipeline_stages["drop_from_prev_pct"] = pipeline_stages["reached"].pct_change().mul(100).round(1)
    biggest_drop = pipeline_stages.loc[pipeline_stages["drop_from_prev_pct"].idxmin()]
    overall_close_rate = round(100 * funnel.loc[funnel["stage"] == "Closed Won", "reached"].iloc[0] / funnel.loc[funnel["stage"] == "Negotiation", "reached"].iloc[0], 1)
    enterprise_losses = results["loss_reasons_by_segment"]
    enterprise_loss_n = int(enterprise_losses[enterprise_losses["segment"] == "Enterprise"]["n"].sum())
    enterprise_top_loss = (
        enterprise_losses[enterprise_losses["segment"] == "Enterprise"]
        .sort_values("n", ascending=False)
        .iloc[0]
    )

    summary = f"""# CRM Sales Pipeline Analysis: Exec Summary

**Data:** {len(df)} synthetic opportunities generated to mirror a typical
B2B SaaS Salesforce export (`data/opportunities.csv`). **This dataset is
synthetic**, built to demonstrate the SQL/analysis approach, not to claim
real findings about any company. See README for the generation logic.

## Key numbers

- **Best-converting segment:** {seg_sorted.iloc[0]['segment']} at {seg_sorted.iloc[0]['win_rate_pct']}% win rate, vs. {seg_sorted.iloc[-1]['segment']} at {seg_sorted.iloc[-1]['win_rate_pct']}%. Segment is a real driver of win probability here, not noise.
- **Best-converting lead source:** {src.iloc[0]['lead_source']} at {src.iloc[0]['win_rate_pct']}% win rate, vs. {src.iloc[-1]['lead_source']} at {src.iloc[-1]['win_rate_pct']}%.
- **Biggest funnel drop-off:** {biggest_drop['stage']}, losing {abs(biggest_drop['drop_from_prev_pct']):.1f}% of opportunities that reached the prior stage, the single stage worth the most process attention. (Of deals that reach Negotiation, {overall_close_rate}% ultimately close-won: that's the overall conversion rate, not a stage bottleneck by itself.)
- **Top rep by closed-won dollars:** {reps.iloc[0]['owner']} (${reps.iloc[0]['won_amount']:,.0f} won, {reps.iloc[0]['win_rate_pct']}% win rate).
- **Enterprise's #1 loss reason:** {enterprise_top_loss['loss_reason']} ({enterprise_top_loss['pct_of_segment_losses']}% of Enterprise losses), a different shape than the smaller segments, worth a segment-specific playbook rather than one generic objection-handling doc. **Caveat:** this is only {enterprise_loss_n} lost Enterprise deals total (Enterprise is ~15% of the dataset by design), so treat the exact percentage as directional, not precise, until the sample grows.

## Recommendations

1. **Fix the {biggest_drop['stage']} stage first.** It's the largest single-stage drop-off in the pre-close funnel; closing that gap by even a few points compounds through every stage after it.
2. **Shift outbound spend toward {src.iloc[0]['lead_source']}-shaped motions** where the win rate data supports it, rather than splitting effort evenly across sources.
3. **Build a segment-specific loss-reason playbook for Enterprise** ({enterprise_top_loss['loss_reason']}-driven) instead of reusing the SMB objection-handling script, noting the small-sample caveat above before over-indexing on the exact split.

## Honest limitations

This is generated data with intentional signal baked in (segment and
source affect win probability by design) so the SQL queries have something
real to surface. It is not evidence about any actual company's pipeline.
The value here is the analysis technique (funnel construction, cohort win
rates, loss-reason breakdown), which carries over unchanged to a real
Salesforce export, with one difference: on real data, none of these
relationships are known ahead of time the way they are here by
construction. The Enterprise segment in particular has a small sample
({enterprise_loss_n} lost deals); read its specific percentages as
directional.
"""
    (OUT / "exec_summary.md").write_text(summary)
    print("\nWrote output/*.csv, output/funnel.png, output/win_rate_by_segment.png, output/exec_summary.md")


if __name__ == "__main__":
    main()
