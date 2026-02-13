{{
  config(
    materialized='table'
  )
}}

SELECT
    symbol,
    MAX(company_name) as company_name,
    COUNT(*) as total_announcements,
    COUNT(DISTINCT category_group) as category_types,
    MAX(broadcast_datetime) as last_announcement,
    MIN(broadcast_datetime) as first_announcement
FROM {{ ref('stg_announcements') }}
GROUP BY symbol
HAVING COUNT(*) >= 1
ORDER BY total_announcements DESC
