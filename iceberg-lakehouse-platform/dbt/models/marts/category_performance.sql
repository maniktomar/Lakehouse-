{{ config(materialized='table', schema='gold') }}

/*
  Mart: Category performance with month-over-month revenue growth.
  Showcases window functions, CTEs, and analytical SQL patterns.
*/

WITH monthly AS (
    SELECT
        category,
        DATE_TRUNC('month', event_timestamp)  AS month,
        ROUND(SUM(order_amount), 2)           AS monthly_revenue,
        COUNT(DISTINCT order_id)              AS monthly_orders,
        COUNT(DISTINCT customer_id)           AS monthly_customers
    FROM {{ ref('stg_orders') }}
    WHERE status = 'completed'
    GROUP BY 1, 2
),

with_growth AS (
    SELECT
        category,
        month,
        monthly_revenue,
        monthly_orders,
        monthly_customers,
        LAG(monthly_revenue)
            OVER (PARTITION BY category ORDER BY month)  AS prev_month_revenue,
        LAG(monthly_orders)
            OVER (PARTITION BY category ORDER BY month)  AS prev_month_orders
    FROM monthly
)

SELECT
    category,
    month,
    monthly_revenue,
    monthly_orders,
    monthly_customers,
    prev_month_revenue,
    ROUND(
        100.0 * (monthly_revenue - prev_month_revenue)
        / NULLIF(prev_month_revenue, 0),
        2
    )                                                     AS revenue_mom_growth_pct,
    ROUND(
        100.0 * (monthly_orders - prev_month_orders)
        / NULLIF(prev_month_orders, 0),
        2
    )                                                     AS orders_mom_growth_pct
FROM with_growth
ORDER BY category, month DESC
