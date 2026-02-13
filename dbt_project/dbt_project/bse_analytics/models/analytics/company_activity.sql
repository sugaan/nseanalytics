-- Analytics: Company-level metrics
-- Which companies are most active?

{{
  config(
    materialized='table',
    tags=['analytics', 'company']
  )
}}

SELECT
    symbol,
    MAX(company_name) as company_name,  -- Get company name
    
    -- Activity metrics
    COUNT(*) as total_announcements,
    COUNT(DISTINCT category_group) as category_types,
    COUNT(DISTINCT announcement_date) as active_days,
    
    -- Time range
    MIN(broadcast_datetime) as first_announcement,
    MAX(broadcast_datetime) as last_announcement,
    
    -- Days since last announcement
    CAST(
        (julianday('now') - julianday(MAX(broadcast_datetime))) AS INTEGER
    ) as days_since_last_announcement,
    
    -- Average announcements per day
    ROUND(
        CAST(COUNT(*) AS FLOAT) / 
        COUNT(DISTINCT announcement_date),
        2
    ) as avg_announcements_per_day

FROM {{ ref('stg_announcements') }}
GROUP BY symbol
HAVING COUNT(*) >= 2  -- Only companies with 2+ announcements
ORDER BY total_announcements DESC
