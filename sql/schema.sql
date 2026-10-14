-- Service desk ticket table (SQLite)
-- One row per ticket. Timestamps are stored as ISO text: 'YYYY-MM-DD HH:MM:SS'.

DROP TABLE IF EXISTS tickets;

CREATE TABLE tickets (
    ticket_id               TEXT PRIMARY KEY,
    created_at              TEXT NOT NULL,
    first_response_at       TEXT NOT NULL,
    resolved_at             TEXT,            -- NULL while the ticket is open
    status                  TEXT NOT NULL,   -- 'Closed' or 'Open'
    priority                TEXT NOT NULL,   -- 'P1 - Critical' .. 'P4 - Low'
    category                TEXT NOT NULL,
    subcategory             TEXT NOT NULL,
    site                    TEXT NOT NULL,
    channel                 TEXT NOT NULL,
    assigned_group          TEXT NOT NULL,
    assigned_agent          TEXT NOT NULL,
    response_target_min     INTEGER NOT NULL,
    resolution_target_hours INTEGER NOT NULL,
    reopened                INTEGER NOT NULL, -- 1 = ticket was re-opened
    csat_score              INTEGER           -- 1-5, NULL if no survey response
);

-- A view that adds the calculated fields most queries need
DROP VIEW IF EXISTS tickets_enriched;

CREATE VIEW tickets_enriched AS
SELECT
    t.*,
    strftime('%Y-%m', created_at)                                        AS month,
    CAST(strftime('%w', created_at) AS INTEGER)                          AS weekday_num, -- 0 = Sunday
    (julianday(first_response_at) - julianday(created_at)) * 24 * 60     AS response_minutes,
    CASE WHEN resolved_at IS NOT NULL
         THEN (julianday(resolved_at) - julianday(created_at)) * 24 END  AS resolution_hours,
    CASE WHEN resolved_at IS NULL THEN NULL
         WHEN (julianday(resolved_at) - julianday(created_at)) * 24 <= resolution_target_hours
         THEN 1 ELSE 0 END                                               AS resolution_sla_met,
    -- ROUND guards against floating-point error when a response lands exactly on the target
    CASE WHEN ROUND((julianday(first_response_at) - julianday(created_at)) * 24 * 60, 3) <= response_target_min
         THEN 1 ELSE 0 END                                               AS response_sla_met
FROM tickets t;
