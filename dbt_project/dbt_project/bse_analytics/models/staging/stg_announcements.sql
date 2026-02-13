-- Staging Model: Clean and standardize raw announcements
-- This creates a VIEW (no data duplication, always fresh)

{{
  config(
    materialized='view',
    tags=['staging', 'raw']
  )
}}

WITH source_data AS (
    -- Get data from raw table
    SELECT * FROM announcements
    WHERE broadcast_datetime IS NOT NULL  -- Remove bad records
)

SELECT
    -- Primary Key
    id,
    
    -- Company Info (cleaned)
    UPPER(TRIM(symbol)) as symbol,
    TRIM(company_name) as company_name,
    
    -- Announcement Details
    TRIM(subject) as subject,
    TRIM(description) as description,
    TRIM(category) as category,
    
    -- Timestamps
    broadcast_datetime,
    created_at,
    
    -- Date Parts (for easy filtering)
    DATE(broadcast_datetime) as announcement_date,
    strftime('%Y-%m', broadcast_datetime) as announcement_month,
    strftime('%Y', broadcast_datetime) as announcement_year,
    strftime('%w', broadcast_datetime) as day_of_week,  -- 0=Sunday
    strftime('%H', broadcast_datetime) as hour_of_day,
    
    -- Category Grouping (simplify categories)
    CASE 
        WHEN category LIKE '%Board Meeting%' THEN 'Corporate Governance'
        WHEN category LIKE '%Financial%' OR category LIKE '%Results%' THEN 'Financial'
        WHEN category LIKE '%Company Update%' THEN 'Corporate'
        WHEN category LIKE '%Announcement%' THEN 'General'
        ELSE 'Other'
    END as category_group,
    
    -- Metadata
    feed_source,
    attachment_url,
    local_attachment_path,
    
    -- Flags (useful for filtering)
    CASE WHEN attachment_url IS NOT NULL THEN 1 ELSE 0 END as has_attachment

FROM source_data
