# Data Dictionary: `opportunities.csv`

| Column | Type | Description |
|---|---|---|
| `opp_id` | string | Unique opportunity identifier (`OPP-00001` ...). |
| `segment` | string | Account segment: `SMB`, `Mid-Market`, or `Enterprise`. |
| `lead_source` | string | How the opportunity originated: `Inbound`, `Outbound`, `Partner`, `Event`. |
| `owner` | string | Sales rep owning the opportunity (`Rep A`...`Rep H`). |
| `amount` | float | Deal size in USD. |
| `created_date` | date | Opportunity creation date. |
| `close_date` | date | Actual close date. Blank if `outcome` is `Open`. |
| `cycle_days` | int | Days from `created_date` to `close_date`. Null if `outcome` is `Open`. |
| `furthest_stage` | string | The last pre-close stage this opportunity reached: `Prospecting`, `Qualification`, `Proposal`, or `Negotiation`. For `Won` deals this is always `Negotiation` (they passed through it before closing). |
| `furthest_stage_idx` | int | 0-3 index matching `furthest_stage`, used to build the funnel (`reached at least this stage`). |
| `outcome` | string | `Won`, `Lost`, or `Open`. |
| `loss_reason` | string | Only set when `outcome` is `Lost`: `Price`, `Competitor`, `No Budget`, `Timing`, `No Decision`. |

## Mapping to a real Salesforce opportunity export

This schema is deliberately close to what a Salesforce `Opportunity` report export looks like, so the SQL in `queries.sql` should run against a real export with only column renames, not a rewrite:

| This dataset | Salesforce object.field |
|---|---|
| `segment` | Custom field, or derived from `Account.Type` / a segmentation field |
| `lead_source` | `Opportunity.LeadSource` |
| `owner` | `Opportunity.OwnerId` (join to `User.Name`) |
| `amount` | `Opportunity.Amount` |
| `created_date` | `Opportunity.CreatedDate` |
| `close_date` | `Opportunity.CloseDate` |
| `furthest_stage` / `outcome` | Derived from `Opportunity.StageName` and `Opportunity.IsWon` / `IsClosed` |
| `loss_reason` | `Opportunity.LossReason` (a standard field in current Salesforce orgs) |

The one thing that wouldn't carry over as-is: `furthest_stage_idx` here is reconstructed at generation time because this is a point-in-time synthetic snapshot. On a real org, a proper stage-history table (`OpportunityHistory` or `OpportunityFieldHistory`) would need to be used to reconstruct "furthest stage reached" per deal, since `StageName` alone only shows the *current* stage, not the path a lost deal took to get there.
