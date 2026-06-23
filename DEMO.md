# Meridian Solutions — Project Demo Guide

This guide explains how to verify the Network Operations & Monitoring Lab end to end.

The project demonstrates:

* VLAN-based network segmentation in Cisco Packet Tracer
* Inter-VLAN routing using router-on-a-stick
* Guest VLAN access control using an ACL
* Python-based host and service monitoring
* SQL Server uptime logging and incident tracking
* Streamlit dashboard reporting
* SQL Server backup and restore validation

---

## Prerequisites

Before running the demo, make sure the following are installed:

* Cisco Packet Tracer
* Python 3.12+
* SQL Server Developer Edition
* SQL Server Management Studio (SSMS)
* ODBC Driver 17 for SQL Server
* Python dependencies from `requirements.txt`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file in the project root:

```env
DB_SERVER=localhost
DB_NAME=MeridianOps
DB_USER=NetworkMonitor
DB_PASSWORD=<your_password>
```

The `.env` file is excluded from GitHub by `.gitignore` so database credentials are not committed publicly.

---

## Step 1 — Verify the Packet Tracer Network

Open the Packet Tracer topology file.

Confirm the network includes:

* 1 Cisco ISR 4331 router
* 2 Cisco 2960 switches
* VLAN 10: IT-Admin
* VLAN 20: Finance
* VLAN 30: Operations
* VLAN 40: Servers
* VLAN 50: Guest

Expected VLAN/subnet layout:

| VLAN | Name       | Subnet          | Gateway      |
| ---- | ---------- | --------------- | ------------ |
| 10   | IT-Admin   | 192.168.10.0/24 | 192.168.10.1 |
| 20   | Finance    | 192.168.20.0/24 | 192.168.20.1 |
| 30   | Operations | 192.168.30.0/24 | 192.168.30.1 |
| 40   | Servers    | 192.168.40.0/24 | 192.168.40.1 |
| 50   | Guest      | 192.168.50.0/24 | 192.168.50.1 |

---

## Step 2 — Verify Router Configuration

On Meridian-Router, run:

```bash
show ip interface brief
```

Expected result:

* `GigabitEthernet0/0/0.10` is up with IP `192.168.10.1`
* `GigabitEthernet0/0/0.20` is up with IP `192.168.20.1`
* `GigabitEthernet0/0/0.30` is up with IP `192.168.30.1`
* `GigabitEthernet0/0/0.50` is up with IP `192.168.50.1`
* `GigabitEthernet0/0/1` is up with IP `192.168.40.1`

Run:

```bash
show running-config | section interface
```

Expected result:

* Router subinterfaces use `encapsulation dot1Q`
* Each VLAN has the correct default gateway
* ACL `BLOCK-GUEST` is applied inbound on `GigabitEthernet0/0/0.50`

Run:

```bash
show running-config | section ip access
```

Expected ACL:

```text
ip access-list extended BLOCK-GUEST
 deny ip 192.168.50.0 0.0.0.255 192.168.40.0 0.0.0.255
 permit ip any any
```

---

## Step 3 — Verify Switch Configuration

On Dept-Switch, run:

```bash
show vlan brief
```

Expected result:

* `Fa0/2` is assigned to VLAN 10
* `Fa0/3` is assigned to VLAN 20
* `Fa0/4` is assigned to VLAN 30
* `Fa0/5` is assigned to VLAN 50

Run:

```bash
show interfaces trunk
```

Expected result:

* `Gig0/1` is trunking
* VLANs 10, 20, 30, and 50 are allowed and active on the trunk

On Server-Switch, run:

```bash
show vlan brief
```

Expected result:

* `Fa0/2` is assigned to VLAN 40

Run:

```bash
show interfaces trunk
```

Expected result:

* `Gig0/1` is trunking
* VLAN 40 is allowed and active on the trunk

---

## Step 4 — Verify ACL Behavior

From Guest-PC, run:

```bash
ping 192.168.40.10
```

Expected result:

```text
Pinging 192.168.40.10 with 32 bytes of data:
Reply from 192.168.50.1: Destination host unreachable.
Reply from 192.168.50.1: Destination host unreachable.
Reply from 192.168.50.1: Destination host unreachable.
Reply from 192.168.50.1: Destination host unreachable.

Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
```

This confirms Guest-PC is blocked from reaching the Server VLAN.

From Guest-PC, run:

```bash
ping 192.168.20.10
```

Expected result:

```text
Pinging 192.168.20.10 with 32 bytes of data:
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127

Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
```

This confirms the ACL only blocks Guest-to-Server traffic while allowing other permitted traffic.

---

## Step 5 — Create the SQL Server Database

Open SSMS and run:

```text
SQL/schema.sql
```

This creates:

* `MeridianOps` database
* `hosts` table
* `uptime_log` table
* `incidents` table
* `v_host_uptime` view
* `v_current_status` view
* `v_open_incidents` view
* Indexes for uptime and incident lookups
* Seed host records

Verify the database:

```sql
USE MeridianOps;

SELECT * FROM hosts;
SELECT * FROM v_current_status;
SELECT * FROM v_host_uptime;
SELECT * FROM v_open_incidents;
```

Expected result:

* `hosts` returns 6 monitored devices
* `v_current_status` displays latest status after monitor data exists
* `v_host_uptime` displays uptime percentages after monitor data exists
* `v_open_incidents` displays unresolved incidents, if any exist

---

## Step 6 — Configure SQL Server Security Roles

Open SSMS and run:

```text
SQL/security_roles.sql
```

Before running the script, replace placeholder passwords:

```sql
CREATE LOGIN NetworkMonitor WITH PASSWORD = '<REPLACE_WITH_SECURE_PASSWORD>';
CREATE LOGIN ReadOnlyUser   WITH PASSWORD = '<REPLACE_WITH_SECURE_PASSWORD>';
```

Expected permissions:

| User           | Purpose                             | Permission Level                                                |
| -------------- | ----------------------------------- | --------------------------------------------------------------- |
| NetworkMonitor | Used by `monitor.py`                | Can read hosts, insert uptime logs, and create/update incidents |
| ReadOnlyUser   | Used for reporting/dashboard access | Can only read reporting views                                   |

This demonstrates least-privilege database access.

---

## Step 7 — Start the Python Network Monitor

From the project root, run:

```bash
python monitor.py
```

Expected terminal output:

```text
=======================================================
  Meridian Solutions — Network Operations Monitor
  Polling every 60 seconds | Ctrl+C to stop
=======================================================

[2026-06-16 14:30:00] Checking 6 hosts...

  Hostname             IP                 Ping       ms       Ports
  -------------------- ------------------ ---------- -------- ------------------------------
  Meridian-Router      192.168.10.1       Online     1ms      SSH(22):❌
  IT-Admin-PC          192.168.10.10      Online     1ms      RDP(3389):❌
  Finance-PC           192.168.20.10      Online     1ms      RDP(3389):❌
  Ops-PC               192.168.30.10      Online     1ms      RDP(3389):❌
  Server               192.168.40.10      Online     1ms      HTTP(80):✅  HTTPS(443):✅  SQL Server(1433):✅
  Guest-PC             192.168.50.10      Online     1ms      HTTP(80):❌
```

Expected behavior:

* Monitor checks each active host every 60 seconds
* ICMP ping result is logged to SQL Server
* TCP service port checks are displayed in the terminal
* Offline hosts trigger new incident records
* Recovered hosts automatically resolve open incidents

---

## Step 8 — Verify Monitor Data in SQL Server

In SSMS, run:

```sql
USE MeridianOps;

SELECT TOP 20 *
FROM uptime_log
ORDER BY checked_at DESC;
```

Expected result:

* New uptime records are inserted every monitor cycle
* Each record includes host ID, timestamp, online status, response time, and notes if applicable

Check incidents:

```sql
SELECT *
FROM incidents
ORDER BY started_at DESC;
```

Expected result:

* Offline hosts create incident records
* Resolved outages have a populated `resolved_at` timestamp and resolution note

Check dashboard views:

```sql
SELECT * FROM v_current_status;
SELECT * FROM v_host_uptime;
SELECT * FROM v_open_incidents;
```

Expected result:

* Current status view shows each host’s latest known state
* Uptime view calculates uptime percentage per host
* Open incidents view shows only unresolved incidents

---

## Step 9 — Run the Local Streamlit Dashboard

From the project root, run:

```bash
streamlit run streamlit/dashboard.py
```

Expected result:

* Dashboard opens in the browser
* Total hosts displays as 6
* Online/offline counts match the latest monitor results
* Open incidents count matches SQL Server
* Uptime percentages are shown by host
* Incident table displays open and resolved incidents
* Response time history chart displays monitor data

The local Streamlit dashboard reads from SQL Server.

---

## Step 10 — Verify Public Demo Data

The public demo uses SQLite-generated sample data and exported JSON so the project can be viewed without requiring access to the local SQL Server database.

To regenerate the SQLite demo database:

```bash
cd streamlit
python seed_sqlite.py
```

Expected result:

```text
✅ meridian_ops.db created with sample data.
```

To regenerate the JSON file used for public dashboard/demo data:

```bash
python generate_json.py
```

Expected result:

```text
✅ dashboard_data.json created.
```

Expected generated demo data:

* 6 monitored hosts
* 24 hours of sample uptime records
* Resolved incidents showing troubleshooting examples
* Response-time history for dashboard visualization

---

## Step 11 — Verify Backup and Restore Runbook

The SQL Server backup/restore runbook demonstrates a basic database recovery workflow for the `MeridianOps` monitoring database.

Before running the script, create the backup folder on your computer:

C:\SQLBackups\MeridianOps\
```

If you want to use a different folder, update this line in `SQL/backup_restore_runbook.sql`:

```sql
SET @BackupDir = N'C:\SQLBackups\MeridianOps\';
```

Open SSMS and run:

SQL/backup_restore_runbook.sql
```

The runbook performs the following steps:

1. Creates a full backup of `MeridianOps`
2. Creates a differential backup of `MeridianOps`
3. Verifies both backup files using `RESTORE VERIFYONLY`
4. Drops any old `MeridianOps_Test` database if it already exists
5. Restores the full backup into `MeridianOps_Test`
6. Restores the differential backup into `MeridianOps_Test`
7. Compares row counts between the live and restored databases

Expected validation result:


table_name     live_database_count     restored_database_count     validation_result
hosts          6                       6                           MATCH
uptime_log     <count>                 <count>                     MATCH
incidents      <count>                 <count>                     MATCH
```

This confirms the backup files can be restored successfully without overwriting the live `MeridianOps` database.

The cleanup section at the bottom of the runbook is commented out by default. Uncomment it only if you want to remove the `MeridianOps_Test` database after validation.

```

Expected result:

* Full backup file is created successfully
* Differential backup file is created successfully

Run the restore test section.

Expected result:

* `MeridianOps_Test` database is created
* Backup restores successfully into the test database
* Row counts are checked for `hosts`, `uptime_log`, and `incidents`
* Test database is dropped after validation

Example validation query:

```sql
USE MeridianOps_Test;

SELECT 'Hosts' AS table_name, COUNT(*) AS row_count FROM hosts
UNION ALL
SELECT 'Uptime Log', COUNT(*) FROM uptime_log
UNION ALL
SELECT 'Incidents', COUNT(*) FROM incidents;
```

This confirms the backup can be restored and verified without overwriting the production lab database.

---

## Demo Completion Checklist

Use this checklist to confirm the project is fully working:

* [ ] Packet Tracer topology opens successfully
* [ ] VLANs are assigned correctly
* [ ] Router subinterfaces are configured correctly
* [ ] Trunk ports are active
* [ ] Guest VLAN is blocked from Server VLAN
* [ ] Guest VLAN can still reach allowed department VLANs
* [ ] SQL Server database is created
* [ ] SQL Server roles and permissions are configured
* [ ] Python monitor runs without errors
* [ ] Uptime logs are inserted into SQL Server
* [ ] Incidents are created when hosts go offline
* [ ] Incidents are resolved when hosts come back online
* [ ] Streamlit dashboard displays current host status
* [ ] Uptime percentages populate correctly
* [ ] Backup and restore runbook completes successfully

---

## Recruiter Review Notes

This demo proves that the project is not just a static dashboard. It shows a complete junior network operations workflow:

1. Design the network
2. Segment users by VLAN
3. Enforce access control
4. Monitor hosts and services
5. Log operational data
6. Track incidents
7. Report status through a dashboard
8. Validate database backup and restore procedures

