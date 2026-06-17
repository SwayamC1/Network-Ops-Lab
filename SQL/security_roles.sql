-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: security_roles.sql
-- Description: Database users, roles, and least-privilege permissions
-- Author: Swayam Chopra
-- ============================================================

USE MeridianOps;
GO

-- ─────────────────────────────────────────
-- LOGINS & USERS
-- ─────────────────────────────────────────

-- NetworkMonitor: used by the Python monitoring script
CREATE LOGIN NetworkMonitor WITH PASSWORD = '<SECREAT_PASSWORD>';
CREATE LOGIN ReadOnlyUser   WITH PASSWORD = '<SECREAT_PASSWORD>';

-- ReadOnlyUser: used by dashboard viewers and reporting
CREATE LOGIN ReadOnlyUser WITH PASSWORD = 'Readonly@2026!';
CREATE USER  ReadOnlyUser FOR LOGIN ReadOnlyUser;
GO

-- ─────────────────────────────────────────
-- PERMISSIONS  (least privilege)
-- ─────────────────────────────────────────

-- NetworkMonitor can read hosts and write ping results and incidents
GRANT SELECT, INSERT ON uptime_log TO NetworkMonitor;
GRANT SELECT         ON hosts      TO NetworkMonitor;
GRANT SELECT, INSERT ON incidents  TO NetworkMonitor;

-- ReadOnlyUser can only read the three reporting views
GRANT SELECT ON v_host_uptime    TO ReadOnlyUser;
GRANT SELECT ON v_current_status TO ReadOnlyUser;
GRANT SELECT ON v_open_incidents TO ReadOnlyUser;
GO
