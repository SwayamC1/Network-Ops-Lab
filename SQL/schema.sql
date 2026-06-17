-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: schema.sql
-- Description: Creates database, tables, indexes, and views
-- Author: Swayam Chopra | UMBC MIS 2026
-- ============================================================

USE master;
GO

CREATE DATABASE MeridianOps;
GO

USE MeridianOps;
GO

-- ─────────────────────────────────────────
-- TABLES
-- ─────────────────────────────────────────

-- hosts: every monitored device on the network
CREATE TABLE hosts (
    host_id       INT IDENTITY(1,1) PRIMARY KEY,
    hostname      VARCHAR(50)  NOT NULL,
    ip_address    VARCHAR(15)  NOT NULL UNIQUE,
    department    VARCHAR(30)  NOT NULL,
    vlan          INT          NOT NULL,
    is_active     BIT          NOT NULL DEFAULT 1,
    added_at      DATETIME     NOT NULL DEFAULT GETDATE()
);

-- uptime_log: one row per ping check per host
CREATE TABLE uptime_log (
    log_id        INT IDENTITY(1,1) PRIMARY KEY,
    host_id       INT          NOT NULL,
    checked_at    DATETIME     NOT NULL DEFAULT GETDATE(),
    is_online     BIT          NOT NULL,
    response_ms   INT,
    notes         VARCHAR(200),
    CONSTRAINT fk_uptime_host FOREIGN KEY (host_id) REFERENCES hosts(host_id)
);

-- incidents: outage records with resolution notes
CREATE TABLE incidents (
    incident_id   INT IDENTITY(1,1) PRIMARY KEY,
    host_id       INT          NOT NULL,
    started_at    DATETIME     NOT NULL,
    resolved_at   DATETIME,
    description   VARCHAR(500) NOT NULL,
    resolution    VARCHAR(500),
    CONSTRAINT fk_incident_host FOREIGN KEY (host_id) REFERENCES hosts(host_id)
);
GO

-- ─────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────

-- Speed up uptime queries by host and time
CREATE INDEX ix_uptime_host_time
    ON uptime_log (host_id, checked_at DESC);

-- Speed up open incident lookups
CREATE INDEX ix_incidents_open
    ON incidents (host_id, resolved_at)
    WHERE resolved_at IS NULL;
GO

-- ─────────────────────────────────────────
-- VIEWS
-- ─────────────────────────────────────────

-- Uptime percentage and average response time per host
CREATE VIEW v_host_uptime AS
SELECT
    h.hostname,
    h.ip_address,
    h.department,
    h.vlan,
    COUNT(*)                                                    AS total_checks,
    SUM(CAST(u.is_online AS INT))                               AS online_count,
    CAST(SUM(CAST(u.is_online AS INT)) * 100.0
         / COUNT(*) AS DECIMAL(5,2))                            AS uptime_pct,
    AVG(CASE WHEN u.is_online = 1 THEN u.response_ms END)       AS avg_response_ms
FROM hosts h
JOIN uptime_log u ON u.host_id = h.host_id
GROUP BY h.hostname, h.ip_address, h.department, h.vlan;
GO

-- Most recent status of every host
CREATE VIEW v_current_status AS
SELECT
    h.hostname,
    h.ip_address,
    h.department,
    u.checked_at,
    CASE WHEN u.is_online = 1 THEN 'Online' ELSE 'Offline' END  AS status,
    u.response_ms
FROM hosts h
JOIN uptime_log u ON u.log_id = (
    SELECT TOP 1 log_id
    FROM uptime_log
    WHERE host_id = h.host_id
    ORDER BY checked_at DESC
);
GO

-- All unresolved incidents
CREATE VIEW v_open_incidents AS
SELECT
    h.hostname,
    h.department,
    i.started_at,
    i.description
FROM incidents i
JOIN hosts h ON h.host_id = i.host_id
WHERE i.resolved_at IS NULL;
GO

-- ─────────────────────────────────────────
--- SEED DATA
-- ─────────────────────────────────────────

INSERT INTO hosts (hostname, ip_address, department, vlan) VALUES
('Meridian-Router', '192.168.10.1',  'IT Administration', 10),
('IT-Admin-PC',     '192.168.10.10', 'IT Administration', 10),
('Finance-PC',      '192.168.20.10', 'Finance',           20),
('Ops-PC',          '192.168.30.10', 'Operations',        30),
('Server',          '192.168.40.10', 'Servers',           40),
('Guest-PC',        '192.168.50.10', 'Guest',             50);
GO
