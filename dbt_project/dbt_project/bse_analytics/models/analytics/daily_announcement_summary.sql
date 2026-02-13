-- Analytics: Daily announcement trends
-- This creates a TABLE (stores aggregated data)

{{
  config(
    materialized='table',
    tags=['analytics', 'daily']
  )
}}

SELECT
    announcement_date,
    category_group,
    
    -- Counts
    COUNT(*) as announcement_count,
    COUNT(DISTINCT symbol) as unique_companies,
    COUNT(CASE WHEN has_attachment = 1 THEN 1 END) as announcements_with_attachments,
    
    -- Percentages
    ROUND(
        COUNT(CASE WHEN has_attachment = 1 THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as pct_with_attachments

FROM {{ ref('stg_announcements') }}  -- 👈 Reference staging model
GROUP BY announcement_date, category_group
ORDER BY announcement_date DESC, category_group
