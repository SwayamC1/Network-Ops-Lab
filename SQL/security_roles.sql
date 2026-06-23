```sql
-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: security_roles.sql
-- Description: Database users, roles, and least-privilege permissions
-- Author: Swayam Chopra | UMBC MIS 2026
-- Note: Credentials are stored in .env and excluded from GitHub
-- ============================================================

USE MeridianOps;
GO

-- ============================================================
-- SERVER-LEVEL LOGINS
-- ============================================================
-- Replace placeholder passwords before running this script.
-- If the logins already exist, they will not be recreated.
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.server_principals
    WHERE name = 'NetworkMonitor'
)
BEGIN
    CREATE LOGIN NetworkMonitor
    WITH PASSWORD = '<REPLACE_WITH_SECURE_PASSWORD>';
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.server_principals
    WHERE name = 'ReadOnlyUser'
)
BEGIN
    CREATE LOGIN ReadOnlyUser
    WITH PASSWORD = '<REPLACE_WITH_SECURE_PASSWORD>';
END;
GO

-- ============================================================
-- DATABASE USERS
-- ============================================================
-- Maps database users to server-level logins.
-- If the users already exist, they will not be recreated.
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_principals
    WHERE name = 'NetworkMonitor'
)
BEGIN
    CREATE USER NetworkMonitor FOR LOGIN NetworkMonitor;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_principals
    WHERE name = 'ReadOnlyUser'
)
BEGIN
    CREATE USER ReadOnlyUser FOR LOGIN ReadOnlyUser;
END;
GO

-- ============================================================
-- PERMISSIONS: NetworkMonitor
-- ============================================================
-- Used by monitor.py.
-- Can read active hosts, insert uptime records, and create/update incidents.
-- ============================================================

GRANT SELECT ON dbo.hosts TO NetworkMonitor;
GRANT INSERT ON dbo.uptime_log TO NetworkMonitor;
GRANT SELECT, INSERT, UPDATE ON dbo.incidents TO NetworkMonitor;

-- Allows monitor.py to check for existing open incidents before creating duplicates.
GRANT SELECT ON dbo.incidents TO NetworkMonitor;
GO

-- ============================================================
-- PERMISSIONS: ReadOnlyUser
-- ============================================================
-- Used for dashboards and reporting.
-- Can only read reporting views, not raw operational tables.
-- ============================================================

GRANT SELECT ON dbo.v_host_uptime TO ReadOnlyUser;
GRANT SELECT ON dbo.v_current_status TO ReadOnlyUser;
GRANT SELECT ON dbo.v_open_incidents TO ReadOnlyUser;
GRANT SELECT ON dbo.v_incident_history TO ReadOnlyUser;
GO

-- ============================================================
-- PERMISSION VALIDATION
-- ============================================================

SELECT
    dp.name AS principal_name,
    dp.type_desc AS principal_type,
    o.name AS object_name,
    p.permission_name,
    p.state_desc
FROM sys.database_permissions p
JOIN sys.database_principals dp
    ON p.grantee_principal_id = dp.principal_id
JOIN sys.objects o
    ON p.major_id = o.object_id
WHERE dp.name IN ('NetworkMonitor', 'ReadOnlyUser')
ORDER BY
    dp.name,
    o.name,
    p.permission_name;
GO
```

