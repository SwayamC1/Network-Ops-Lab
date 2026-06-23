-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: schema.sql
-- Description: Creates database, tables, indexes, views, and seed data
-- Author: Swayam Chopra | UMBC MIS 2026
-- ============================================================

USE master;
GO

-- ============================================================
-- CREATE DATABASE IF IT DOES NOT EXIST
-- ============================================================

IF DB_ID('MeridianOps') IS NULL
BEGIN
    CREATE DATABASE MeridianOps;
END;
GO

USE MeridianOps;
GO

-- ============================================================
-- TABLE: hosts
-- Stores every monitored network device
-- ============================================================

IF OBJECT_ID('dbo.hosts', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.hosts (
        host_id       INT IDENTITY(1,1) PRIMARY KEY,
        hostname      VARCHAR(50)  NOT NULL,
        ip_address    VARCHAR(15)  NOT NULL UNIQUE,
        department    VARCHAR(30)  NOT NULL,
        vlan          INT          NOT NULL,
        is_active     BIT          NOT NULL DEFAULT 1,
        added_at      DATETIME     NOT NULL DEFAULT GETDATE()
    );
END;
GO

-- ============================================================
-- TABLE: uptime_log
-- Stores one monitoring result per host per check cycle
-- ============================================================

IF OBJECT_ID('dbo.uptime_log', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.uptime_log (
        log_id        INT IDENTITY(1,1) PRIMARY KEY,
        host_id       INT          NOT NULL,
        checked_at    DATETIME     NOT NULL DEFAULT GETDATE(),
        is_online     BIT          NOT NULL,
        response_ms   INT          NULL,
        notes         VARCHAR(200) NULL,

        CONSTRAINT fk_uptime_host
            FOREIGN KEY (host_id)
            REFERENCES dbo.hosts(host_id)
    );
END;
GO

-- ============================================================
-- TABLE: incidents
-- Stores host outage and service availability incidents
-- ============================================================

IF OBJECT_ID('dbo.incidents', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.incidents (
        incident_id   INT IDENTITY(1,1) PRIMARY KEY,
        host_id       INT          NOT NULL,
        incident_type VARCHAR(30)  NOT NULL DEFAULT 'HOST',
        service_name  VARCHAR(50)  NULL,
        port_number   INT          NULL,
        started_at    DATETIME     NOT NULL DEFAULT GETDATE(),
        resolved_at   DATETIME     NULL,
        description   VARCHAR(500) NOT NULL,
        resolution    VARCHAR(500) NULL,

        CONSTRAINT fk_incident_host
            FOREIGN KEY (host_id)
            REFERENCES dbo.hosts(host_id)
    );
END;
GO

-- ============================================================
-- ADD INCIDENT COLUMNS IF TABLE ALREADY EXISTED FROM OLD VERSION
-- ============================================================

IF COL_LENGTH('dbo.incidents', 'incident_type') IS NULL
BEGIN
    ALTER TABLE dbo.incidents
    ADD incident_type VARCHAR(30) NOT NULL
        CONSTRAINT df_incidents_incident_type DEFAULT 'HOST'
        WITH VALUES;
END;
GO

IF COL_LENGTH('dbo.incidents', 'service_name') IS NULL
BEGIN
    ALTER TABLE dbo.incidents
    ADD service_name VARCHAR(50) NULL;
END;
GO

IF COL_LENGTH('dbo.incidents', 'port_number') IS NULL
BEGIN
    ALTER TABLE dbo.incidents
    ADD port_number INT NULL;
END;
GO

-- ============================================================
-- INDEXES
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ix_uptime_host_time'
      AND object_id = OBJECT_ID('dbo.uptime_log')
)
BEGIN
    CREATE INDEX ix_uptime_host_time
        ON dbo.uptime_log (host_id, checked_at DESC);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ix_incidents_open'
      AND object_id = OBJECT_ID('dbo.incidents')
)
BEGIN
    CREATE INDEX ix_incidents_open
        ON dbo.incidents (host_id, resolved_at)
        WHERE resolved_at IS NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ix_incidents_type_service'
      AND object_id = OBJECT_ID('dbo.incidents')
)
BEGIN
    CREATE INDEX ix_incidents_type_service
        ON dbo.incidents (host_id, incident_type, service_name, port_number, resolved_at);
END;
GO

-- ============================================================
-- VIEWS
-- ============================================================

CREATE OR ALTER VIEW dbo.v_host_uptime AS
SELECT
    h.hostname,
    h.ip_address,
    h.department,
    h.vlan,
    COUNT(*) AS total_checks,
    SUM(CAST(u.is_online AS INT)) AS online_count,
    CAST(
        SUM(CAST(u.is_online AS INT)) * 100.0 / COUNT(*)
        AS DECIMAL(5,2)
    ) AS uptime_pct,
    AVG(CASE WHEN u.is_online = 1 THEN u.response_ms END) AS avg_response_ms
FROM dbo.hosts h
JOIN dbo.uptime_log u
    ON u.host_id = h.host_id
GROUP BY
    h.hostname,
    h.ip_address,
    h.department,
    h.vlan;
GO

CREATE OR ALTER VIEW dbo.v_current_status AS
SELECT
    h.hostname,
    h.ip_address,
    h.department,
    h.vlan,
    u.checked_at,
    CASE
        WHEN u.is_online = 1 THEN 'Online'
        ELSE 'Offline'
    END AS status,
    u.response_ms,
    u.notes
FROM dbo.hosts h
JOIN dbo.uptime_log u
    ON u.log_id = (
        SELECT TOP 1 log_id
        FROM dbo.uptime_log
        WHERE host_id = h.host_id
        ORDER BY checked_at DESC, log_id DESC
    );
GO

CREATE OR ALTER VIEW dbo.v_open_incidents AS
SELECT
    i.incident_id,
    h.hostname,
    h.department,
    i.incident_type,
    i.service_name,
    i.port_number,
    i.started_at,
    i.description
FROM dbo.incidents i
JOIN dbo.hosts h
    ON h.host_id = i.host_id
WHERE i.resolved_at IS NULL;
GO

CREATE OR ALTER VIEW dbo.v_incident_history AS
SELECT
    i.incident_id,
    h.hostname,
    h.department,
    i.incident_type,
    i.service_name,
    i.port_number,
    i.started_at,
    i.resolved_at,
    CASE
        WHEN i.resolved_at IS NULL THEN 'Open'
        ELSE 'Resolved'
    END AS status,
    i.description,
    i.resolution
FROM dbo.incidents i
JOIN dbo.hosts h
    ON h.host_id = i.host_id;
GO

CREATE OR ALTER VIEW dbo.v_response_time_history AS
SELECT
    h.hostname,
    h.department,
    h.vlan,
    u.checked_at,
    u.is_online,
    u.response_ms
FROM dbo.uptime_log u
JOIN dbo.hosts h
    ON h.host_id = u.host_id;
GO

-- ============================================================
-- SEED DATA
-- Inserts hosts only if they do not already exist
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM dbo.hosts WHERE hostname = 'Meridian-Router')
BEGIN
    INSERT INTO dbo.hosts (hostname, ip_address, department, vlan)
    VALUES ('Meridian-Router', '192.168.10.1', 'IT Administration', 10);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.hosts WHERE hostname = 'IT-Admin-PC')
BEGIN
    INSERT INTO dbo.hosts (hostname, ip_address, department, vlan)
    VALUES ('IT-Admin-PC', '192.168.10.10', 'IT Administration', 10);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.hosts WHERE hostname = 'Finance-PC')
BEGIN
    INSERT INTO dbo.hosts (hostname, ip_address, department, vlan)
    VALUES ('Finance-PC', '192.168.20.10', 'Finance', 20);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.hosts WHERE hostname = 'Ops-PC')
BEGIN
    INSERT INTO dbo.hosts (hostname, ip_address, department, vlan)
    VALUES ('Ops-PC', '192.168.30.10', 'Operations', 30);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.hosts WHERE hostname = 'Server')
BEGIN
    INSERT INTO dbo.hosts (hostname, ip_address, department, vlan)
    VALUES ('Server', '192.168.40.10', 'Servers', 40);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.hosts WHERE hostname = 'Guest-PC')
BEGIN
    INSERT INTO dbo.hosts (hostname, ip_address, department, vlan)
    VALUES ('Guest-PC', '192.168.50.10', 'Guest', 50);
END;
GO

-- ============================================================
-- VALIDATION QUERIES
-- ============================================================

SELECT * FROM dbo.hosts;
SELECT * FROM dbo.v_open_incidents;
GO
