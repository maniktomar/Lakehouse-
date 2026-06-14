{{ config(materialized='table', schema='gold') }}

/*
  Mart: Daily sales aggregated by date, category, channel, and currency.
  Replaces the hardcoded Spark SQL gold aggregation with a dbt model,
  enabling full lineage tracking and automated testing.
*/

SELECT
    CAST(event_timestamp AS DATE)            AS order_date,
    category,
    sales_channel,
    currency,
    COUNT(DISTINCT order_id)                 AS order_count,
    COUNT(DISTINCT customer_id)              AS unique_customers,
    ROUND(SUM(order_amount), 2)              AS gross_sales,
    ROUND(AVG(order_amount), 2)              AS avg_order_value,
    ROUND(MIN(order_amount), 2)              AS min_order_value,
    ROUND(MAX(order_amount), 2)              AS max_order_value
FROM {{ ref('stg_orders') }}
WHERE status = 'completed'
GROUP BY 1, 2, 3, 4
ORDER BY 1 DESC, gross_sales DESC
