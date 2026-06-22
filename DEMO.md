# Meridian Solutions — Project Demo Guide

This document walks through how to verify every component of the project end to end.

---

## Prerequisites

- SQL Server installed with MeridianOps database set up (run `SQL/schema.sql` then `SQL/security_roles.sql`)
- Python virtual environment activated with dependencies installed
- Cisco Packet Tracer installed

---

## Step 1 — Verify the Database

Open SSMS and run:

```sql
USE MeridianOps;
SELECT * FROM hosts;
SELECT * FROM v_host_uptime;
SELECT * FROM v_open_incidents;
```

Expected: 6 hosts returned, uptime view shows percentages, no open incidents.

---

## Step 2 — Start the Monitor

```bash
cd Network-Ops-Lab
venv\Scripts\activate
python monitor.py
```

Expected terminal output:
