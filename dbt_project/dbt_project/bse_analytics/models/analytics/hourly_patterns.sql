-- Analytics: When do announcements happen?
-- Find peak hours

{{
  config(
    materialized='table',
    tags=['analytics', 'timing']
  )
}}

SELECT
    hour_of_day,
    
    -- Counts by hour
    COUNT(*) as announcement_count,
    COUNT(DISTINCT symbol) as unique_companies,
    COUNT(DISTINCT announcement_date) as days_observed,
    
    -- Category breakdown
    COUNT(CASE WHEN category_group = 'Financial' THEN 1 END) as financial_count,
    COUNT(CASE WHEN category_group = 'Corporate Governance' THEN 1 END) as governance_count,
    
    -- Average per day
    ROUND(
        CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT announcement_date),
        2
    ) as avg_per_day

FROM {{ ref('stg_announcements') }}
GROUP BY hour_of_day
ORDER BY CAST(hour_of_day AS INTEGER)
