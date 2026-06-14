-- ============================================================
-- Trino Analytics Queries — Open Lakehouse with Apache Iceberg
-- Target catalog: lakehouse  (Iceberg via Nessie + MinIO)
-- Run against Trino UI at http://localhost:8080
-- ============================================================

-- ── 0. Catalog exploration ───────────────────────────────────────────────────
SHOW SCHEMAS FROM lakehouse;
SHOW TABLES FROM lakehouse.gold;
SHOW TABLES FROM lakehouse.silver;
SHOW TABLES FROM lakehouse.monitoring;

-- ── 1. Full gold table (most recent data first) ──────────────────────────────
SELECT
  order_date,
  category,
  sales_channel,
  currency,
  order_count,
  gross_sales,
  avg_order_value,
  unique_customers
FROM lakehouse.gold.daily_sales
ORDER BY order_date DESC, gross_sales DESC;

-- ── 2. Category revenue ranking ──────────────────────────────────────────────
SELECT
  category,
  SUM(gross_sales)        AS total_sales,
  SUM(order_count)        AS total_orders,
  ROUND(AVG(avg_order_value), 2) AS blended_aov,
  SUM(unique_customers)   AS total_customers
FROM lakehouse.gold.daily_sales
GROUP BY category
ORDER BY total_sales DESC;

-- ── 3. Daily top-selling category (window function) ──────────────────────────
-- Shows which category led each day — useful for trend analysis
SELECT
  order_date,
  category,
  gross_sales,
  RANK() OVER (PARTITION BY order_date ORDER BY gross_sales DESC) AS daily_rank
FROM lakehouse.gold.daily_sales
ORDER BY order_date DESC, daily_rank;

-- ── 4. Sales channel mix ─────────────────────────────────────────────────────
SELECT
  sales_channel,
  SUM(gross_sales)                                          AS channel_sales,
  SUM(order_count)                                          AS channel_orders,
  ROUND(
    100.0 * SUM(gross_sales) / SUM(SUM(gross_sales)) OVER (),
    2
  )                                                         AS pct_of_total
FROM lakehouse.gold.daily_sales
GROUP BY sales_channel
ORDER BY channel_sales DESC;

-- ── 5. Currency breakdown ────────────────────────────────────────────────────
SELECT
  currency,
  SUM(gross_sales)   AS total_sales,
  SUM(order_count)   AS total_orders,
  ROUND(
    100.0 * SUM(order_count) / SUM(SUM(order_count)) OVER (),
    2
  )                  AS pct_of_orders
FROM lakehouse.gold.daily_sales
GROUP BY currency
ORDER BY total_sales DESC;

-- ── 6. Month-over-month gross sales growth ───────────────────────────────────
WITH monthly AS (
  SELECT
    DATE_TRUNC('month', order_date)  AS month,
    SUM(gross_sales)                 AS monthly_sales
  FROM lakehouse.gold.daily_sales
  GROUP BY 1
)
SELECT
  month,
  monthly_sales,
  LAG(monthly_sales) OVER (ORDER BY month)      AS prev_month_sales,
  ROUND(
    100.0 * (monthly_sales - LAG(monthly_sales) OVER (ORDER BY month))
          / NULLIF(LAG(monthly_sales) OVER (ORDER BY month), 0),
    2
  )                                             AS mom_growth_pct
FROM monthly
ORDER BY month DESC;

-- ── 7. Rolling 7-day gross sales ─────────────────────────────────────────────
SELECT
  order_date,
  SUM(gross_sales) AS daily_sales,
  ROUND(
    AVG(SUM(gross_sales)) OVER (
      ORDER BY order_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ),
    2
  ) AS rolling_7d_avg
FROM lakehouse.gold.daily_sales
GROUP BY order_date
ORDER BY order_date DESC;

-- ── 8. Data quality quarantine rate ─────────────────────────────────────────
-- Compares valid silver rows to quarantined rows per pipeline run
SELECT
  run_at,
  silver_rows,
  quarantined_rows,
  bronze_rows,
  gold_rows,
  ROUND(
    100.0 * quarantined_rows / NULLIF(bronze_rows, 0),
    2
  ) AS quarantine_rate_pct,
  run_status
FROM lakehouse.monitoring.pipeline_runs
ORDER BY run_at DESC;

-- ── 9. Pipeline audit history ────────────────────────────────────────────────
SELECT *
FROM lakehouse.monitoring.pipeline_runs
ORDER BY run_at DESC;

-- ── 10. Iceberg snapshot history (silver.orders) ────────────────────────────
-- Demonstrates time-travel capability — each pipeline run adds a snapshot
SELECT
  snapshot_id,
  committed_at,
  operation,
  summary
FROM lakehouse.silver."orders$snapshots"
ORDER BY committed_at DESC;

-- ── 11. Time travel — query an older snapshot ────────────────────────────────
-- Replace <snapshot_id> with an older snapshot_id from query 10 above
-- SELECT COUNT(*) AS historical_row_count
-- FROM lakehouse.silver.orders FOR VERSION AS OF <snapshot_id>;

-- ── 12. Top customers by lifetime spend (silver layer) ───────────────────────
SELECT
  customer_id,
  COUNT(DISTINCT order_id)       AS order_count,
  ROUND(SUM(order_amount), 2)    AS lifetime_value,
  MIN(event_timestamp)           AS first_order,
  MAX(event_timestamp)           AS last_order
FROM lakehouse.silver.orders
WHERE status = 'completed'
GROUP BY customer_id
ORDER BY lifetime_value DESC
LIMIT 20;

-- ── 13. Schema inspection ────────────────────────────────────────────────────
-- Verify schema evolution (e.g. loyalty_tier column added by schema_evolution_demo)
DESCRIBE lakehouse.silver.orders;
