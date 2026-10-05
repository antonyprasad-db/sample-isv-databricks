# Databricks Genie Agent — Creation Runbook

Creates the **Fresh Retail Sales Forecasting** Genie Agent that Amazon Quick queries over MCP.
Do this AFTER the upstream MMF forecast notebooks (`01 → 02`) and this repo's notebooks (`04 → 03`)
have run (the Agent's tables/views must exist).
Console steps are in the Databricks workspace UI.

## Prerequisites
- Run order: upstream MMF `01` (data prep) → `02` (forecast), then this repo's `04` (Genie views) →
  `03` (dims). The `01`/`02` notebooks live in the [MMF accelerator](https://github.com/databricks-industry-solutions/many-model-forecasting/tree/main/examples/fresh_retail_net),
  not this repo. The tables/views below must already exist in catalog `mmf`, schema `fresh_retail_net`.
- A **Serverless SQL Warehouse** the Agent will run on. This repo uses one named `supply-chain-genie`.
  Create one via **SQL → SQL Warehouses → Create** (Serverless), or reuse an existing serverless
  warehouse. Note its **warehouse id** (`<WAREHOUSE_ID>`) — you'll need it for the connector.
- **CAN USE** on that warehouse and **SELECT** on `mmf.fresh_retail_net`.

## STEP 1 — Create the Agent
In the Databricks workspace, click **Genie Agents** in the sidebar, then **New** in the upper-right
corner, and create the Agent with these values:

| Field | Value |
|---|---|
| Agent name | `Fresh Retail Sales Forecasting` |
| SQL warehouse | `supply-chain-genie` (your serverless warehouse) |
| Default catalog / schema | `mmf` / `fresh_retail_net` |

Save, then record the id as `<GENIE_SPACE_ID>` in `.supply-chain-automation-env`: `cleanup/cleanup.sh`
reads it, and the connector runbook needs it for the MCP endpoint. If you created the Agent with
`scripts/setup_databricks.sh` instead, the id is already saved in `scripts/.env.generated`, which is
loaded after your env file and takes precedence.

Get the id from the Agent's **Configure → About** panel, where the UI labels it **Agent ID**. Or from
the CLI, with your env file sourced:

```bash
databricks genie list-spaces --profile "${DBX_PROFILE:?source .supply-chain-automation-env first}" \
  --output json \
  | jq -r --arg t "${GENIE_SPACE_TITLE:-Fresh Retail Sales Forecasting}" \
      '.spaces[]? | select(.title==$t) | .space_id'
```

This should print exactly one id. It reads only the first page of results, so in a workspace with many
Genie Agents it can print nothing even though yours exists; use the Configure panel then. Two ids mean
two Agents share the title. `scripts/setup_databricks.sh` titles the Agent
`Supply Chain Demand Forecasting (Chronos-2)` rather than the name above, so set `GENIE_SPACE_TITLE` to
that to look up a scripted Agent. `cleanup/cleanup.sh` discovers by the same variable when
`GENIE_SPACE_ID` is unset, which is why recording the id matters on the console path.

The id also appears in the Agent's URL, but not necessarily as the last path segment, and the prefix
changed with the Spaces-to-Agents rename, so prefer the two routes above. The UI says Agent ID, the API
returns `space_id`, and `<GENIE_SPACE_ID>` keeps its original name.

## STEP 2 — Add the six tables/views
In the Agent, go to **Configure → Data** and click **Add** (the tuning docs label this tab **Sources**),
then add exactly these **6** objects from `mmf.fresh_retail_net`:

| # | Object | Created by | Purpose |
|---|---|---|---|
| 1 | `daily_sales_raw` | upstream MMF nb 01 | raw daily sales (actuals) |
| 2 | `demand_train` | upstream MMF nb 01 | training history (per-SKU daily) |
| 3 | `scoring_output_mv` | notebook 04 | exploded Chronos-2 forecasts (one row per SKU per forecast date) |
| 4 | `evaluation_metrics_mv` | notebook 04 | backtest accuracy metrics |
| 5 | `product_dim` | notebook 03 | product_id → name / category / brand |
| 6 | `location_dim` | notebook 03 | city_id → city name / region / state |

(These are the 6 objects the connector runbook and end-to-end tests refer to as "the 6 tables.")

## STEP 3 — Paste the Agent instructions
**Configure → Text** → paste the full contents of `genie/genie_instructions.md` as the general
instructions. These define what a SKU is, how to resolve product/region names, and the surge output
contract.

## STEP 4 — Pin the trusted surge query (determinism)
**Configure → Examples** → **Add** an example query → paste `genie/genie_surge_trusted_query.sql`.
Mark it **trusted**. This is what makes unattended surge detection reproducible: Genie reuses this
exact SQL instead of generating (and drifting) its own each run.

## STEP 5 — Validate the Agent directly (before wiring Quick)
In the Genie Agent chat:
- *"How many SKUs do we have?"* → **1,000**
- *"Which products are surging in the Northeast?"* → returns the surging SKUs with
  `unique_id, retailer_product_id, city_id, region, city_name, forecast_7d_total, surge_ratio`
- *"Is Skim Milk demand spiking in the Northeast?"* → surge answer, ratio ~1.69, ~50 units/7d

Once these work, proceed to `QUICK_DATABRICKS_CONNECTOR_RUNBOOK.md` to connect the Agent to Amazon Quick.
