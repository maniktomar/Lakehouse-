{{ config(materialized='table', schema='gold') }}

/*
  Mart: Sales channel performance with revenue share %.
  Useful for identifying the most profitable acquisition channels.
*/

SELECT
    sales_channel,
    COUNT(DISTINCT order_id)                                          AS total_orders,
    COUNT(DISTINCT customer_id)                                       AS unique_customers,
    ROUND(SUM(order_amount), 2)                                       AS total_revenue,
    ROUND(AVG(order_amount), 2)                                       AS avg_order_value,
    ROUND(MIN(order_amount), 2)                                       AS min_order_value,
    ROUND(MAX(order_amount), 2)                                       AS max_order_value,
    ROUND(
        100.0 * SUM(order_amount)
        / SUM(SUM(order_amount)) OVER (),
        2
    )                                                                 AS revenue_share_pct,
    ROUND(
        100.0 * COUNT(DISTINCT order_id)
        / SUM(COUNT(DISTINCT order_id)) OVER (),
        2
    )                                                                 AS order_share_pct
FROM {{ ref('stg_orders') }}
WHERE status = 'completed'
GROUP BY 1
ORDER BY total_revenue DESC
