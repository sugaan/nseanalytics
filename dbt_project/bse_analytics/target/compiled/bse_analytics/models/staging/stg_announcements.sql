

SELECT
    id,
    UPPER(TRIM(symbol)) as symbol,
    TRIM(company_name) as company_name,
    TRIM(subject) as subject,
    TRIM(description) as description,
    TRIM(category) as category,
    broadcast_datetime,
    created_at,
    DATE(broadcast_datetime) as announcement_date,
    strftime('%Y-%m', broadcast_datetime) as announcement_month,
    strftime('%Y', broadcast_datetime) as announcement_year,
    strftime('%H', broadcast_datetime) as hour_of_day,
    CASE 
        WHEN category LIKE '%Board Meeting%' THEN 'Corporate Governance'
        WHEN category LIKE '%Financial%' OR category LIKE '%Results%' THEN 'Financial'
        WHEN category LIKE '%Company Update%' THEN 'Corporate'
        WHEN category LIKE '%Announcement%' THEN 'General'
        ELSE 'Other'
    END as category_group,
    feed_source,
    attachment_url,
    CASE WHEN attachment_url IS NOT NULL THEN 1 ELSE 0 END as has_attachment
FROM announcements
WHERE broadcast_datetime IS NOT NULL