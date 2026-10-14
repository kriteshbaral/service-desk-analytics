-- Service desk analysis queries (SQLite).
-- Each query starts with a "-- name:" line so analysis/run_analysis.py can
-- run them one by one and save the results for the dashboard.

-- name: kpis
-- Headline numbers for the whole year
SELECT
    COUNT(*)                                             AS total_tickets,
    ROUND(AVG(resolution_sla_met) * 100, 1)              AS resolution_sla_pct,
    ROUND(AVG(response_sla_met) * 100, 1)                AS response_sla_pct,
    ROUND(AVG(resolution_hours), 1)                      AS avg_resolution_hours,
    ROUND(AVG(reopened) * 100, 1)                        AS reopen_rate_pct,
    ROUND(AVG(csat_score), 2)                            AS avg_csat,
    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END)     AS open_tickets
FROM tickets_enriched;

-- name: monthly_volume
-- Tickets raised and SLA performance per month (trend)
SELECT
    month,
    COUNT(*)                                  AS tickets,
    ROUND(AVG(resolution_sla_met) * 100, 1)   AS resolution_sla_pct,
    ROUND(AVG(response_sla_met) * 100, 1)     AS response_sla_pct
FROM tickets_enriched
GROUP BY month
ORDER BY month;

-- name: by_category
-- Which kinds of problems drive the workload
SELECT
    category,
    COUNT(*)                                                   AS tickets,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tickets), 1) AS share_pct,
    ROUND(AVG(resolution_hours), 1)                            AS avg_resolution_hours,
    ROUND(AVG(resolution_sla_met) * 100, 1)                    AS resolution_sla_pct,
    ROUND(AVG(reopened) * 100, 1)                              AS reopen_rate_pct
FROM tickets_enriched
GROUP BY category
ORDER BY tickets DESC;

-- name: sla_by_priority
-- SLA compliance against each priority's targets
SELECT
    priority,
    COUNT(*)                                  AS tickets,
    MAX(response_target_min)                  AS response_target_min,
    MAX(resolution_target_hours)              AS resolution_target_hours,
    ROUND(AVG(response_sla_met) * 100, 1)     AS response_sla_pct,
    ROUND(AVG(resolution_sla_met) * 100, 1)   AS resolution_sla_pct
FROM tickets_enriched
GROUP BY priority
ORDER BY priority;

-- name: hardware_by_site
-- On-site hardware work: are remote sites waiting longer?
SELECT
    site,
    COUNT(*)                                  AS hardware_tickets,
    ROUND(AVG(resolution_hours), 1)           AS avg_resolution_hours,
    ROUND(AVG(resolution_sla_met) * 100, 1)   AS resolution_sla_pct
FROM tickets_enriched
WHERE category = 'Hardware'
GROUP BY site
ORDER BY resolution_sla_pct;

-- name: weekday_load
-- Demand by day of week (staffing)
SELECT
    CASE weekday_num WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed'
                     WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat' ELSE 'Sun' END AS weekday,
    COUNT(*)                                                        AS tickets,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT date(created_at)), 1)     AS avg_per_day,
    ROUND(AVG(response_minutes), 0)                                 AS avg_response_minutes
FROM tickets_enriched
GROUP BY weekday_num
ORDER BY CASE weekday_num WHEN 0 THEN 7 ELSE weekday_num END;

-- name: top_subcategories
-- The ten most common specific issues
SELECT category, subcategory, COUNT(*) AS tickets
FROM tickets_enriched
GROUP BY category, subcategory
ORDER BY tickets DESC
LIMIT 10;

-- name: repeat_issues
-- Where tickets come back: re-open rate by category and site (min 30 tickets)
SELECT category, site, COUNT(*) AS tickets, SUM(reopened) AS reopened,
       ROUND(AVG(reopened) * 100, 1) AS reopen_rate_pct
FROM tickets_enriched
GROUP BY category, site
HAVING COUNT(*) >= 30
ORDER BY reopen_rate_pct DESC
LIMIT 5;

-- name: agent_workload
-- Workload and quality per agent
SELECT
    assigned_group, assigned_agent,
    COUNT(*)                                  AS tickets,
    ROUND(AVG(resolution_hours), 1)           AS avg_resolution_hours,
    ROUND(AVG(resolution_sla_met) * 100, 1)   AS resolution_sla_pct,
    ROUND(AVG(csat_score), 2)                 AS avg_csat
FROM tickets_enriched
GROUP BY assigned_group, assigned_agent
ORDER BY tickets DESC;

-- name: csat_vs_sla
-- Does missing the SLA hurt customer satisfaction?
SELECT
    CASE resolution_sla_met WHEN 1 THEN 'SLA met' ELSE 'SLA breached' END AS outcome,
    COUNT(csat_score)            AS survey_responses,
    ROUND(AVG(csat_score), 2)    AS avg_csat
FROM tickets_enriched
WHERE resolution_sla_met IS NOT NULL
GROUP BY resolution_sla_met;

-- name: self_service_opportunity
-- Password/account tickets that a self-service reset tool could remove
SELECT
    COUNT(*)                                                     AS tickets,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tickets), 1)  AS share_pct,
    ROUND(SUM(resolution_hours), 0)                              AS total_hours_open,
    SUM(CASE WHEN channel = 'Phone' THEN 1 ELSE 0 END)           AS phone_calls
FROM tickets_enriched
WHERE subcategory IN ('Password reset', 'Account locked', 'MFA reset');
