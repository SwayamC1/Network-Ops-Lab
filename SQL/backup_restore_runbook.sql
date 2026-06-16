-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: backup_restore_runbook.sql
-- Description: Backup and restore procedures with documentation
-- Author: Swayam Chopra
-- ============================================================

-- ─────────────────────────────────────────
-- FULL BACKUP
-- Run every Sunday night
-- ─────────────────────────────────────────

BACKUP DATABASE MeridianOps
TO DISK = 'S:\Network Lab\MeridianOps_Full.bak'
WITH FORMAT,
     NAME        = 'MeridianOps Full Backup',
     DESCRIPTION = 'Weekly full backup of MeridianOps database';
GO

-- ─────────────────────────────────────────
-- DIFFERENTIAL BACKUP
-- Run every other night (Mon-Sat)
-- Only backs up changes since last full
-- ─────────────────────────────────────────

BACKUP DATABASE MeridianOps
TO DISK = 'S:\Network Lab\MeridianOps_Diff.bak'
WITH DIFFERENTIAL,
     NAME = 'MeridianOps Differential Backup';
GO

-- ─────────────────────────────────────────
-- RESTORE TEST
-- Run monthly to verify backup is valid
-- Always restore to a test database, never overwrite live
-- ─────────────────────────────────────────

USE master;
GO

RESTORE DATABASE MeridianOps_Test
FROM DISK = 'S:\Network Lab\MeridianOps_Full.bak'
WITH MOVE 'MeridianOps'
     TO 'C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\DATA\MeridianOps_Test.mdf',
MOVE 'MeridianOps_log'
     TO 'C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\DATA\MeridianOps_Test_log.ldf',
REPLACE;
GO

-- Verify row counts match live database
USE MeridianOps_Test;
SELECT 'Hosts'      AS table_name, COUNT(*) AS row_count FROM hosts
UNION ALL
SELECT 'Uptime Log',               COUNT(*)              FROM uptime_log
UNION ALL
SELECT 'Incidents',                COUNT(*)              FROM incidents;
GO

-- Clean up test database after verification
USE master;
DROP DATABASE MeridianOps_Test;
GO