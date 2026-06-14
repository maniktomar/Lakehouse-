{{ config(materialized='table', schema='silver') }}

/*
  Staging table: validated Silver orders.
  Only includes quality_status = 'valid' rows.
  This is the single source of truth for all mart models.
*/

SELECT
    event_id,
    order_id,
    event_timestamp,
    customer_id,
    customer_email,
    product_id,
    category,
    quantity,
    unit_price,
    order_amount,
    currency,
    sales_channel,
    country,
    status,
    quality_status
FROM lakehouse.silver.orders
WHERE quality_status = 'valid'
