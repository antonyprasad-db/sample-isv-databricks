-- Genie example query for the "Which SKUs have a demand surge?" question.
-- Add this in the Genie Agent under Configure -> Examples, paired with the sample question
-- "Which SKUs have a demand surge?", to steer Genie toward this SQL instead of its own.
-- It has no parameters, so per the Databricks docs it is an example query, not a trusted asset
-- with a verified answer: validate the surge answer (runbook STEP 5) before relying on the Flow.
--
-- Returns one row per surging SKU with the clean matching keys the downstream Flow steps need:
--   unique_id, retailer_product_id, city_id, region, city_name, forecast_7d_total, surge_ratio
-- CRITICAL: retailer_product_id is the part AFTER the underscore; city_id comes from the data
-- (demand_train -> location_dim), NEVER from the store prefix before the underscore.
WITH forecast_stats AS (
  SELECT unique_id,
         AVG(forecast_value) AS avg_forecast,
         SUM(forecast_value) AS forecast_7d_total
  FROM mmf.fresh_retail_net.scoring_output_mv
  WHERE forecast_date >= '2024-06-26' AND forecast_date <= '2024-07-02'
  GROUP BY unique_id),
actual_stats AS (
  SELECT unique_id,
         AVG(y)        AS avg_actual,
         MAX(city_id)  AS city_id
  FROM mmf.fresh_retail_net.demand_train
  WHERE ds >= '2024-06-12' AND ds <= '2024-06-25'
  GROUP BY unique_id)
SELECT f.unique_id,
       CAST(split_part(f.unique_id, '_', 2) AS INT) AS retailer_product_id,
       a.city_id,
       l.region,
       l.city_name,
       f.forecast_7d_total,
       try_divide(f.avg_forecast, a.avg_actual)       AS surge_ratio
FROM forecast_stats f
JOIN actual_stats   a ON f.unique_id = a.unique_id
JOIN mmf.fresh_retail_net.location_dim l ON a.city_id = l.city_id
WHERE f.avg_forecast >= 1.5 * a.avg_actual
  AND a.avg_actual   >= 1
ORDER BY surge_ratio DESC;
