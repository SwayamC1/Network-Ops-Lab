```sql
-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: validation_checks.sql
-- Description: Quick validation checks for database, views,
--              incidents, monitoring data, and permissions
-- Author: Swayam Chopra | UMBC MIS 2026
-- ============================================================

USE MeridianOps;
GO

PRINT '============================================================';
PRINT 'MeridianOps Validation Checks';
PRINT '============================================================';


-- ============================================================
-- CHECK 1: HOST INVENTORY
-- Expected: 6 active hosts
-- ============================================================

PRINT 'CHECK 1: Host inventory';

SELECT
    host_id,
    hostname,
    ip_address,
    department,
    vlan,
    is_active,
    added_at
FROM dbo.hosts
ORDER BY vlan, hostname;
GO


-- ============================================================
-- CHECK 2: UPTIME LOG COUNT
-- Expected: Count should increase while monitor.py is running
-- ============================================================

PRINT 'CHECK 2: Uptime log count';

SELECT
    COUNT(*) AS total_uptime_records,
    MIN(checked_at) AS first_check,
    MAX(checked_at) AS latest_check
FROM dbo.uptime_log;
GO


-- ============================================================
-- CHECK 3: LATEST STATUS VIEW
-- Expected: One latest status row per monitored host
-- ============================================================

PRINT 'CHECK 3: Current host status view';

SELECT
    hostname,
    ip_address,
    department,
    vlan,
    checked_at,
    status,
    response_ms,
    notes
FROM dbo.v_current_status
ORDER BY vlan, hostname;
GO


-- ============================================================
-- CHECK 4: UPTIME SUMMARY VIEW
-- Expected: Uptime percentage and average response time by host
-- ============================================================

PRINT 'CHECK 4: Host uptime summary view';

SELECT
    hostname,
    ip_address,
    department,
    vlan,
    total_checks,
    online_count,
    uptime_pct,
    avg_response_ms
FROM dbo.v_host_uptime
ORDER BY vlan, hostname;
GO


-- ============================================================
-- CHECK 5: OPEN INCIDENTS
-- Expected: Shows unresolved host/service incidents, if any
-- ============================================================

PRINT 'CHECK 5: Open incidents view';

SELECT
    incident_id,
    hostname,
    department,
    incident_type,
    service_name,
    port_number,
    started_at,
    description
FROM dbo.v_open_incidents
ORDER BY started_at DESC;
GO


-- ============================================================
-- CHECK 6: INCIDENT HISTORY
-- Expected: Shows both open and resolved incidents
-- ============================================================

PRINT 'CHECK 6: Incident history view';

SELECT
    incident_id,
    hostname,
    department,
    incident_type,
    service_name,
    port_number,
    started_at,
    resolved_at,
    status,
    description,
    resolution
FROM dbo.v_incident_history
ORDER BY started_at DESC;
GO


-- ============================================================
-- CHECK 7: RESPONSE TIME HISTORY VIEW
-- Expected: Response-time rows for dashboard charting
-- ============================================================

PRINT 'CHECK 7: Response time history view';

SELECT TOP 25
    hostname,
    department,
    vlan,
    checked_at,
    is_online,
    response_ms
FROM dbo.v_response_time_history
ORDER BY checked_at DESC;
GO


-- ============================================================
-- CHECK 8: SERVICE INCIDENT COUNTS
-- Expected: Shows service-level monitoring activity
-- ============================================================

PRINT 'CHECK 8: Service incident counts';

SELECT
    incident_type,
    service_name,
    port_number,
    COUNT(*) AS incident_count,
    SUM(CASE WHEN resolved_at IS NULL THEN 1 ELSE 0 END) AS open_count,
    SUM(CASE WHEN resolved_at IS NOT NULL THEN 1 ELSE 0 END) AS resolved_count
FROM dbo.incidents
GROUP BY
    incident_type,
    service_name,
    port_number
ORDER BY
    incident_type,
    service_name,
    port_number;
GO


-- ============================================================
-- CHECK 9: PERMISSIONS ASSIGNED
-- Expected:
-- NetworkMonitor should have access to hosts, uptime_log, incidents
-- ReadOnlyUser should have access to reporting views
-- ============================================================

PRINT 'CHECK 9: Database permissions';

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


-- ============================================================
-- CHECK 10: BASIC HEALTH SUMMARY
-- Expected: Simple pass/fail style dashboard for database setup
-- ============================================================

PRINT 'CHECK 10: Basic health summary';

SELECT
    'Hosts configured' AS check_name,
    COUNT(*) AS value,
    CASE
        WHEN COUNT(*) = 6 THEN 'PASS'
        ELSE 'REVIEW'
    END AS result
FROM dbo.hosts

UNION ALL

SELECT
    'Uptime records logged' AS check_name,
    COUNT(*) AS value,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS'
        ELSE 'START MONITOR'
    END AS result
FROM dbo.uptime_log

UNION ALL

SELECT
    'Incident records available' AS check_name,
    COUNT(*) AS value,
    CASE
        WHEN COUNT(*) >= 0 THEN 'PASS'
        ELSE 'REVIEW'
    END AS result
FROM dbo.incidents

UNION ALL

SELECT
    'Current status rows' AS check_name,
    COUNT(*) AS value,
    CASE
        WHEN COUNT(*) = 6 THEN 'PASS'
        ELSE 'START MONITOR'
    END AS result
FROM dbo.v_current_status

UNION ALL

SELECT
    'Uptime summary rows' AS check_name,
    COUNT(*) AS value,
    CASE
        WHEN COUNT(*) = 6 THEN 'PASS'
        ELSE 'START MONITOR'
    END AS result
FROM dbo.v_host_uptime;
GO


PRINT '============================================================';
PRINT 'Validation checks completed.';
PRINT 'Review result sets above for PASS/REVIEW/START MONITOR notes.';
PRINT '============================================================';
GO
```
