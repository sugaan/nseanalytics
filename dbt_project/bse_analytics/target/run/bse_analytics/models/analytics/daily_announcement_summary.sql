
  
    
    
    create  table main."daily_announcement_summary"
    as
        

SELECT
    announcement_date,
    category_group,
    COUNT(*) as announcement_count,
    COUNT(DISTINCT symbol) as unique_companies,
    COUNT(CASE WHEN has_attachment = 1 THEN 1 END) as with_attachments
FROM main."stg_announcements"
GROUP BY announcement_date, category_group
ORDER BY announcement_date DESC

  