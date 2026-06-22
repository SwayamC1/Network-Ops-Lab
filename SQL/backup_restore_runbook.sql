-- ============================================================
-- Meridian Solutions | Network Operations Database
-- File: backup_restore_runbook.sql
-- Description: Backup, restore, and validation procedure
-- Author: Swayam Chopra
-- ============================================================

/*
Purpose:
This runbook demonstrates a basic SQL Server backup and restore workflow
for the MeridianOps network monitoring database.

What this script covers:

1. Full database backup
2. Differential database backup
3. Backup verification
4. Restore to a test database
5. Row-count validation between live and restored databases
6. Optional cleanup of the test restore database

Important:

* Update @BackupDir before running.
* The backup folder must already exist.
* The SQL Server service account must have permission to write to the folder.
* This script restores to MeridianOps_Test and does NOT overwrite MeridianOps.
  */

USE master;

DECLARE @BackupDir NVARCHAR(260);
DECLARE @FullBackupFile NVARCHAR(400);
DECLARE @DiffBackupFile NVARCHAR(400);
DECLARE @DataFile NVARCHAR(400);
DECLARE @LogFile NVARCHAR(400);

-- Change this path if needed.
-- Example: C:\SQLBackups\MeridianOps
SET @BackupDir = N'C:\SQLBackups\MeridianOps';

SET @FullBackupFile = @BackupDir + N'MeridianOps_Full.bak';
SET @DiffBackupFile = @BackupDir + N'MeridianOps_Diff.bak';
SET @DataFile = @BackupDir + N'MeridianOps_Test.mdf';
SET @LogFile = @BackupDir + N'MeridianOps_Test_log.ldf';

PRINT '============================================================';
PRINT 'MeridianOps Backup and Restore Runbook';
PRINT '============================================================';
PRINT 'Backup folder: ' + @BackupDir;
PRINT 'Full backup file: ' + @FullBackupFile;
PRINT 'Differential backup file: ' + @DiffBackupFile;
PRINT '============================================================';

-- ============================================================
-- STEP 1: FULL BACKUP
-- ============================================================

PRINT 'Starting full backup...';

BACKUP DATABASE MeridianOps
TO DISK = @FullBackupFile
WITH INIT,
CHECKSUM,
NAME = 'MeridianOps Full Backup',
DESCRIPTION = 'Full backup of MeridianOps network monitoring database',
STATS = 10;

PRINT 'Full backup completed.';

-- ============================================================
-- STEP 2: DIFFERENTIAL BACKUP
-- ============================================================

PRINT 'Starting differential backup...';

BACKUP DATABASE MeridianOps
TO DISK = @DiffBackupFile
WITH DIFFERENTIAL,
INIT,
CHECKSUM,
NAME = 'MeridianOps Differential Backup',
DESCRIPTION = 'Differential backup of MeridianOps network monitoring database',
STATS = 10;

PRINT 'Differential backup completed.';

-- ============================================================
-- STEP 3: VERIFY BACKUP FILES
-- ============================================================

PRINT 'Verifying full backup file...';

RESTORE VERIFYONLY
FROM DISK = @FullBackupFile
WITH CHECKSUM;

PRINT 'Full backup verification completed.';

PRINT 'Verifying differential backup file...';

RESTORE VERIFYONLY
FROM DISK = @DiffBackupFile
WITH CHECKSUM;

PRINT 'Differential backup verification completed.';

-- ============================================================
-- STEP 4: DROP OLD TEST RESTORE DATABASE IF IT EXISTS
-- ============================================================

IF DB_ID('MeridianOps_Test') IS NOT NULL
BEGIN
PRINT 'Existing MeridianOps_Test database found. Dropping old test database...';

```
ALTER DATABASE MeridianOps_Test
SET SINGLE_USER
WITH ROLLBACK IMMEDIATE;

DROP DATABASE MeridianOps_Test;

PRINT 'Old MeridianOps_Test database dropped.';
```

END;

-- ============================================================
-- STEP 5: RESTORE FULL BACKUP TO TEST DATABASE
-- ============================================================

PRINT 'Restoring full backup to MeridianOps_Test...';

RESTORE DATABASE MeridianOps_Test
FROM DISK = @FullBackupFile
WITH MOVE 'MeridianOps' TO @DataFile,
MOVE 'MeridianOps_log' TO @LogFile,
NORECOVERY,
REPLACE,
STATS = 10;

PRINT 'Full backup restored to test database with NORECOVERY.';

-- ============================================================
-- STEP 6: RESTORE DIFFERENTIAL BACKUP TO TEST DATABASE
-- ============================================================

PRINT 'Restoring differential backup to MeridianOps_Test...';

RESTORE DATABASE MeridianOps_Test
FROM DISK = @DiffBackupFile
WITH RECOVERY,
STATS = 10;

PRINT 'Differential backup restored. MeridianOps_Test is online.';

-- ============================================================
-- STEP 7: VALIDATE LIVE VS RESTORED ROW COUNTS
-- ============================================================

PRINT 'Validating row counts between MeridianOps and MeridianOps_Test...';

SELECT
'hosts' AS table_name,
(SELECT COUNT(*) FROM MeridianOps.dbo.hosts) AS live_database_count,
(SELECT COUNT(*) FROM MeridianOps_Test.dbo.hosts) AS restored_database_count,
CASE
WHEN (SELECT COUNT(*) FROM MeridianOps.dbo.hosts)
= (SELECT COUNT(*) FROM MeridianOps_Test.dbo.hosts)
THEN 'MATCH'
ELSE 'MISMATCH'
END AS validation_result

UNION ALL

SELECT
'uptime_log' AS table_name,
(SELECT COUNT(*) FROM MeridianOps.dbo.uptime_log) AS live_database_count,
(SELECT COUNT(*) FROM MeridianOps_Test.dbo.uptime_log) AS restored_database_count,
CASE
WHEN (SELECT COUNT(*) FROM MeridianOps.dbo.uptime_log)
= (SELECT COUNT(*) FROM MeridianOps_Test.dbo.uptime_log)
THEN 'MATCH'
ELSE 'MISMATCH'
END AS validation_result

UNION ALL

SELECT
'incidents' AS table_name,
(SELECT COUNT(*) FROM MeridianOps.dbo.incidents) AS live_database_count,
(SELECT COUNT(*) FROM MeridianOps_Test.dbo.incidents) AS restored_database_count,
CASE
WHEN (SELECT COUNT(*) FROM MeridianOps.dbo.incidents)
= (SELECT COUNT(*) FROM MeridianOps_Test.dbo.incidents)
THEN 'MATCH'
ELSE 'MISMATCH'
END AS validation_result;

-- ============================================================
-- STEP 8: OPTIONAL TEST DATABASE CLEANUP
-- ============================================================

/*
Uncomment this section if you want to remove the test restore database
after validation.

USE master;

ALTER DATABASE MeridianOps_Test
SET SINGLE_USER
WITH ROLLBACK IMMEDIATE;

DROP DATABASE MeridianOps_Test;

PRINT 'MeridianOps_Test database dropped after validation.';
*/

PRINT '============================================================';
PRINT 'Backup and restore runbook completed successfully.';
PRINT 'Review validation_result values above to confirm row counts match.';
PRINT '============================================================';
