# CRM Sales Pipeline Analysis: Exec Summary

**Data:** 650 synthetic opportunities generated to mirror a typical
B2B SaaS Salesforce export (`data/opportunities.csv`). **This dataset is
synthetic**, built to demonstrate the SQL/analysis approach, not to claim
real findings about any company. See README for the generation logic.

## Key numbers

- **Best-converting segment:** SMB at 40.5% win rate, vs. Enterprise at 31.0%. Segment is a real driver of win probability here, not noise.
- **Best-converting lead source:** Inbound at 41.9% win rate, vs. Outbound at 25.0%.
- **Biggest funnel drop-off:** Negotiation, losing 28.7% of opportunities that reached the prior stage, the single stage worth the most process attention. (Of deals that reach Negotiation, 62.9% ultimately close-won: that's the overall conversion rate, not a stage bottleneck by itself.)
- **Top rep by closed-won dollars:** Rep A ($854,797 won, 44.8% win rate).
- **Enterprise's #1 loss reason:** No Budget (38.3% of Enterprise losses), a different shape than the smaller segments, worth a segment-specific playbook rather than one generic objection-handling doc. **Caveat:** this is only 60 lost Enterprise deals total (Enterprise is ~15% of the dataset by design), so treat the exact percentage as directional, not precise, until the sample grows.

## Recommendations

1. **Fix the Negotiation stage first.** It's the largest single-stage drop-off in the pre-close funnel; closing that gap by even a few points compounds through every stage after it.
2. **Shift outbound spend toward Inbound-shaped motions** where the win rate data supports it, rather than splitting effort evenly across sources.
3. **Build a segment-specific loss-reason playbook for Enterprise** (No Budget-driven) instead of reusing the SMB objection-handling script, noting the small-sample caveat above before over-indexing on the exact split.

## Honest limitations

This is generated data with intentional signal baked in (segment and
source affect win probability by design) so the SQL queries have something
real to surface. It is not evidence about any actual company's pipeline.
The value here is the analysis technique (funnel construction, cohort win
rates, loss-reason breakdown), which carries over unchanged to a real
Salesforce export, with one difference: on real data, none of these
relationships are known ahead of time the way they are here by
construction. The Enterprise segment in particular has a small sample
(60 lost deals); read its specific percentages as
directional.
