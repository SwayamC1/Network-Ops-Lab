# 🖥️ Network Operations & Monitoring Lab

> **Simulated enterprise network with Python monitoring, SQL Server logging, and a live Grafana NOC dashboard**  
> Cisco Packet Tracer · Python · SQL Server · Streamlit · Grafana

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-red?logo=microsoftsqlserver)](https://microsoft.com/sql-server)
**[![Grafana](https://img.shields.io/badge/Grafana-Live%20Dashboard-orange?logo=grafana)](https://tealjeep3109.grafana.net/d/sw8jw9x/meridian-network-operations-center)**

---

## 🔴 Live Dashboard
****[View the Meridian Network Operations Center →](https://tealjeep3109.grafana.net/goto/s8zz2q?orgId=stacks-1693850)****

---

## 📌 Project Overview

This lab simulates the infrastructure environment of **Meridian Solutions**, a fictional 25-person company with three departments: Finance, Operations, and IT Administration. The project covers the full stack of entry-level Network Admin and DBA work:

- Designed and configured a segmented network in Cisco Packet Tracer
- Wrote a Python monitoring script that pings all hosts and logs results to SQL Server
- Built a SQL Server database with normalized schema, views, roles, and backup/restore procedures
- Deployed a live Grafana dashboard showing host status, uptime %, and incident history

---

## 🏗️ Architecture
---

## 🌐 Part 1 — Network Design (Cisco Packet Tracer)

### Topology
- 1 Cisco ISR 4331 router
- 2 Cisco 2960-24TT switches (Dept-Switch, Server-Switch)
- 5 end devices across 5 VLANs

### VLAN Design

| VLAN | Name       | Subnet           | Purpose                     |
|------|------------|------------------|-----------------------------|
| 10   | IT-Admin   | 192.168.10.0/24  | IT Administration           |
| 20   | Finance    | 192.168.20.0/24  | Finance department          |
| 30   | Operations | 192.168.30.0/24  | Operations department       |
| 40   | Servers    | 192.168.40.0/24  | Internal servers (isolated) |
| 50   | Guest      | 192.168.50.0/24  | Guest network (restricted)  |

### Security
- Inter-VLAN routing via router-on-a-stick
- ACL `BLOCK-GUEST` denies Guest VLAN (50) → Server VLAN (40)
- Verified: Guest-PC cannot reach Server; can reach Finance ✅

---

## 🐍 Part 2 — Python Network Monitor

`monitor.py` runs every 60 seconds and:
- Pings all active hosts from the `hosts` table
- Logs each result to `uptime_log` (online/offline, response time)
- Auto-opens an incident in `incidents` when a host goes offline
- Auto-resolves the incident when the host comes back online

```bash
# Run the monitor
python monitor.py
```

---

## 🗃️ Part 3 — SQL Server Database

### Schema (4 objects)
- `hosts` — registered network devices
- `uptime_log` — ping results (one row per check per host)
- `incidents` — outage records with resolution notes
- Views: `v_host_uptime`, `v_current_status`, `v_open_incidents`

### DBA Work Demonstrated
- Role-based access control (NetworkMonitor, ReadOnlyUser)
- Least-privilege permissions on tables and views
- Full backup + differential backup
- Restore to test database with row count verification
- Documented runbook (`backup_restore_runbook.sql`)

```bash
# Set up the database
# Run in SQL Server Management Studio:
SQL/schema.sql
SQL/security_roles.sql
```

---

## 📊 Part 4 — Live Grafana Dashboard

**[→ Open Live Dashboard](https://tealjeep3109.grafana.net/goto/s8zz2q?orgId=stacks-1693850)**

Three panels:
- **Host Status** — current online/offline state per device
- **Host Uptime %** — bar gauge showing uptime percentage
- **Incident Log** — all incidents with descriptions and resolutions

Data source: `dashboard_data.json` (exported from SQLite, hosted on GitHub, read by Grafana Infinity plugin)

---

## 🔧 Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/SwayamC1/Network-Ops-Lab.git
cd Network-Ops-Lab

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create .env file:
# DB_SERVER=localhost
# DB_NAME=MeridianOps
# DB_USER=NetworkMonitor
# DB_PASSWORD=Monitor@2026!

# 5. Set up SQL Server database
# Run SQL/schema.sql then SQL/security_roles.sql in SSMS

# 6. Run the monitor
python monitor.py

# 7. Run the local dashboard
streamlit run dashboard.py
```

---

## 📄 Documentation
- [IP Addressing Plan](docs/ip_addressing_plan.md)
- [Troubleshooting Log](docs/troubleshooting_log.md)
- [Backup & Restore Runbook](SQL/backup_restore_runbook.sql)

---

*Built by [Swayam Chopra](https://linkedin.com/in/swayam-chopra100) · UMBC MIS '26*
