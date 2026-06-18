-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: security_roles.sql
-- Description: Database users, roles, and least-privilege permissions
-- Author: Swayam Chopra | UMBC MIS 2026
-- Note: Credentials are stored in .env and excluded from GitHub
-- ============================================================

USE MeridianOps;
GO

-- ─────────────────────────────────────────
-- LOGINS (server-level)
-- ─────────────────────────────────────────

CREATE LOGIN NetworkMonitor WITH PASSWORD = '<REPLACE_WITH_SECURE_PASSWORD>';
CREATE LOGIN ReadOnlyUser   WITH PASSWORD = '<REPLACE_WITH_SECURE_PASSWORD>';
GO

-- ─────────────────────────────────────────
-- DATABASE USERS (mapped to logins)
-- ─────────────────────────────────────────

CREATE USER NetworkMonitor FOR LOGIN NetworkMonitor;
CREATE USER ReadOnlyUser   FOR LOGIN ReadOnlyUser;
GO

-- ─────────────────────────────────────────
-- PERMISSIONS (least privilege)
-- ─────────────────────────────────────────

-- NetworkMonitor: used by monitor.py
-- Can read hosts and write ping results and incidents
GRANT SELECT         ON hosts      TO NetworkMonitor;
GRANT SELECT, INSERT ON uptime_log TO NetworkMonitor;
GRANT SELECT, INSERT, UPDATE ON incidents TO NetworkMonitor;

-- ReadOnlyUser: used by dashboard and reporting
-- Can only read the three views — no access to raw tables
GRANT SELECT ON v_host_uptime    TO ReadOnlyUser;
GRANT SELECT ON v_current_status TO ReadOnlyUser;
GRANT SELECT ON v_open_incidents TO ReadOnlyUser;
GO
