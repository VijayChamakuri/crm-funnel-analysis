-- Sales pipeline analysis queries, run against the SQLite table `opportunities`
-- (loaded from data/opportunities.csv by analyze.py).

-- 1. Win rate by segment (closed deals only)
-- name: win_rate_by_segment
SELECT
  segment,
  COUNT(*) AS closed_opps,
  SUM(CASE WHEN outcome = 'Won' THEN 1 ELSE 0 END) AS won_opps,
  ROUND(100.0 * SUM(CASE WHEN outcome = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate_pct,
  ROUND(SUM(CASE WHEN outcome = 'Won' THEN amount ELSE 0 END), 0) AS won_amount
FROM opportunities
WHERE outcome IN ('Won', 'Lost')
GROUP BY segment
ORDER BY win_rate_pct DESC;

-- 2. Win rate by lead source
-- name: win_rate_by_source
SELECT
  lead_source,
  COUNT(*) AS closed_opps,
  ROUND(100.0 * SUM(CASE WHEN outcome = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate_pct
FROM opportunities
WHERE outcome IN ('Won', 'Lost')
GROUP BY lead_source
ORDER BY win_rate_pct DESC;

-- 3. Average sales cycle length by segment (closed only)
-- name: cycle_length_by_segment
SELECT
  segment,
  outcome,
  ROUND(AVG(cycle_days), 1) AS avg_cycle_days,
  COUNT(*) AS n
FROM opportunities
WHERE outcome IN ('Won', 'Lost')
GROUP BY segment, outcome
ORDER BY segment, outcome;

-- 4. Funnel: how many opportunities reached each stage (any outcome)
-- name: funnel_by_stage
SELECT 'Prospecting' AS stage, SUM(CASE WHEN furthest_stage_idx >= 0 THEN 1 ELSE 0 END) AS reached FROM opportunities
UNION ALL
SELECT 'Qualification', SUM(CASE WHEN furthest_stage_idx >= 1 THEN 1 ELSE 0 END) FROM opportunities
UNION ALL
SELECT 'Proposal', SUM(CASE WHEN furthest_stage_idx >= 2 THEN 1 ELSE 0 END) FROM opportunities
UNION ALL
SELECT 'Negotiation', SUM(CASE WHEN furthest_stage_idx >= 3 THEN 1 ELSE 0 END) FROM opportunities
UNION ALL
SELECT 'Closed Won', COUNT(*) FROM opportunities WHERE outcome = 'Won';

-- 5. Rep performance leaderboard
-- name: rep_performance
SELECT
  owner,
  COUNT(*) AS closed_opps,
  ROUND(100.0 * SUM(CASE WHEN outcome = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate_pct,
  ROUND(SUM(CASE WHEN outcome = 'Won' THEN amount ELSE 0 END), 0) AS won_amount
FROM opportunities
WHERE outcome IN ('Won', 'Lost')
GROUP BY owner
ORDER BY won_amount DESC;

-- 6. Loss reasons by segment (where are we losing, and why)
-- name: loss_reasons_by_segment
SELECT
  segment,
  loss_reason,
  COUNT(*) AS n,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY segment), 1) AS pct_of_segment_losses
FROM opportunities
WHERE outcome = 'Lost'
GROUP BY segment, loss_reason
ORDER BY segment, n DESC;

-- 7. Open pipeline by stage and segment (what's currently in flight)
-- name: open_pipeline
SELECT
  segment,
  furthest_stage AS current_stage,
  COUNT(*) AS open_opps,
  ROUND(SUM(amount), 0) AS open_amount
FROM opportunities
WHERE outcome = 'Open'
GROUP BY segment, furthest_stage
ORDER BY segment, open_amount DESC;
