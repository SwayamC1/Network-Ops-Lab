# Network Operations & Monitoring Lab

**Cisco Packet Tracer · Python · SQL Server · Streamlit · Grafana**

Designed a simulated small-business network operations environment to demonstrate VLAN segmentation, automated host monitoring, incident tracking, SQL Server administration, and dashboard reporting.

[![Grafana](https://img.shields.io/badge/Grafana-Live%20Dashboard-orange?logo=grafana)](https://tealjeep3109.grafana.net/public-dashboards/2fe1661bb8c7468d90b36d95464d0591)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-Developer-red?logo=microsoftsqlserver)](https://microsoft.com/sql-server)

---

## Public Dashboard
**[→ Meridian Network Operations Center on Grafana](https://tealjeep3109.grafana.net/public-dashboards/2fe1661bb8c7468d90b36d95464d0591)**

---

## What I Built

The fictional company is **Meridian Solutions** — 25 employees across Finance, Operations, and IT Administration. I treated it like a real environment: designed the network, secured it, built monitoring tools around it, stored the operational data in a database, and documented everything the way a junior admin would on the job.

**The four parts:**
1. Designed and configured a segmented network in Cisco Packet Tracer (VLANs, inter-VLAN routing, ACLs)
2. Wrote a Python script that pings every host every 60 seconds and logs results to SQL Server
3. Set up SQL Server with a normalized schema, user roles, backup jobs, and a restore runbook
4. Built a live Grafana dashboard that anyone can view showing host status, uptime %, and incidents

---

## Screenshots

### Network Topology
![Topology](Screenshots/The%20full%20topology%20diagram.png)

### ACL Security Test — Guest VLAN Blocked from Server
![ACL Test](Screenshots/The%20Guest%20ping%20result.png)

### Live Grafana NOC Dashboard
![Dashboard](Screenshots/Network-Lab-Monitor-Dashboard.png)

---

## Part 1 — Network Design (Cisco Packet Tracer)

Cisco Packet Tracer is the industry-standard simulation tool used in CCNA training. I used it to build a topology I'd realistically see in a small office environment.

**Devices:** 1 Cisco ISR 4331 router, 2 Cisco 2960-24TT switches, 5 PCs

**VLAN segmentation:**

| VLAN | Name | Subnet | Purpose |
|------|------|--------|---------|
| 10 | IT-Admin | 192.168.10.0/24 | IT staff |
| 20 | Finance | 192.168.20.0/24 | Finance dept |
| 30 | Operations | 192.168.30.0/24 | Ops dept |
| 40 | Servers | 192.168.40.0/24 | Internal servers |
| 50 | Guest | 192.168.50.0/24 | Guest WiFi |

**Inter-VLAN routing** is done via router-on-a-stick — one physical cable carries all VLANs as tagged traffic to the router, which routes between them using sub-interfaces.

**Security rule:** ACL `BLOCK-GUEST` blocks the Guest VLAN from reaching the Server VLAN. I tested and verified this — Guest-PC cannot ping the Server, but can still reach Finance and Operations.

**Real troubleshooting I did:** During setup, IT-Admin-PC had 100% packet loss. I diagnosed it with `show vlan brief` and found Fa0/2 was assigned to VLAN 40 instead of VLAN 10. Fixed the port assignment and verified with pings. This is documented in the troubleshooting log.

---

## Part 2 — Python Network Monitor

`monitor.py` connects to the SQL Server database and checks every active host on a 60-second loop. For each host it runs two checks:

**1. ICMP ping** — confirms the host is reachable on the network
**2. TCP port checks** — confirms key services are actually running

| Host | Ports Checked |
|---|---|
| Meridian-Router | SSH (22) |
| IT-Admin-PC | RDP (3389) |
| Finance-PC | RDP (3389) |
| Ops-PC | RDP (3389) |
| Server | HTTP (80), HTTPS (443), SQL Server (1433) |
| Guest-PC | HTTP (80) |

When a host stops responding, the script automatically opens an incident record in SQL Server. When it comes back online, the incident is auto-resolved. Port failures are logged as notes on the uptime record.

```python
# Each host gets ICMP ping + TCP port checks
is_online, response_ms = ping_host(ip)
for port, service in HOST_PORTS.get(hostname, []):
    is_open = check_port(ip, port) if is_online else False
log_result(conn, host_id, is_online, response_ms, notes)
```

---

## Part 3 — SQL Server Database

I used **SQL Server Developer Edition** (free) and **SSMS** — the same tools used in enterprise environments.

**Schema:**
- `hosts` — every monitored device
- `uptime_log` — one row per ping check per host
- `incidents` — outage records with timestamps and resolution notes
- `v_host_uptime` — view calculating uptime % per host
- `v_current_status` — view showing each host's most recent status
- `v_open_incidents` — view for unresolved incidents

**DBA tasks I completed:**
- Created two SQL Server logins with least-privilege permissions (NetworkMonitor can write ping data; ReadOnlyUser can only read views)
- Ran a full backup and a differential backup
- Restored the full backup to a test database (`MeridianOps_Test`) and verified row counts matched
- Documented the recovery procedure in a runbook

All SQL files are in the `/SQL` folder.

---

## Part 4 — Grafana Dashboard

I chose Grafana because it's what real network and DevOps teams use for operational monitoring — not a BI tool. The dashboard reads from `dashboard_data.json` hosted on GitHub using the Grafana Infinity plugin.

**Panels:**
- Host status table with department, IP, response time, and online/offline state
- Uptime % gauge per host with color thresholds (green ≥95%, yellow 80–95%, red <80%)
- Incident log with descriptions and resolutions

---

## Skills This Project Covers

| Skill | Where |
|---|---|
| VLAN configuration | Packet Tracer |
| Inter-VLAN routing (router-on-a-stick) | Packet Tracer |
| Access Control Lists | Packet Tracer |
| Network troubleshooting | Troubleshooting log |
| Python scripting | monitor.py |
| SQL Server schema design | schema.sql |
| Database backup and restore | backup_restore_runbook.sql |
| Role-based access control | security_roles.sql |
| Grafana dashboard configuration | Live dashboard |
| Technical documentation                | /docs folder                 |
| Cisco show command outputs             | /configs folder              |
| ACL verification testing               | /configs folder              |

---
## 🗄️ SQL Server vs SQLite — Why Both Exist

The operational monitor (`monitor.py`) and local dashboard (`dashboard.py`) are built for **SQL Server** using pyodbc. This is the production setup — it demonstrates real DBA work: schema design, user roles, backup/restore, and parameterized queries.

For public demo hosting, I included a separate SQLite database (`meridian_ops.db`) seeded with 24 hours of simulated monitoring data. This lets anyone view the Grafana dashboard without needing access to my local SQL Server instance.

**The SQL Server work is what matters for the resume.** The SQLite version exists purely so the live dashboard has data to display.

| Component | Database | Purpose |
|---|---|---|
| `monitor.py` | SQL Server | Production monitor — logs real ping results |
| `dashboard.py` | SQL Server | Local dashboard — reads from SQL Server |
| `seed_sqlite.py` | SQLite | Seeds demo data for public Grafana dashboard |
| `dashboard_data.json` | — | Exported from SQLite, read by Grafana Infinity |

## Local Setup

```bash
git clone https://github.com/SwayamC1/Network-Ops-Lab.git
cd Network-Ops-Lab
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file with your SQL Server credentials:

```
DB_SERVER=localhost
DB_NAME=MeridianOps
DB_USER=NetworkMonitor
DB_PASSWORD=<your_password>
```

Credentials are stored locally and excluded from GitHub via `.gitignore`.

Set up the database in SSMS by running `SQL/schema.sql` then `SQL/security_roles.sql`. Then:

```bash
python monitor.py       # start the network monitor
streamlit run streamlit/dashboard.py  # run the local Streamlit dashboard
```

---

## Documentation
- [IP Addressing Plan](docs/ip_addressing_plan.md)
- [Troubleshooting Log](docs/troubleshooting_log.md)
- [Backup & Restore Runbook](SQL/backup_restore_runbook.sql)
- [Demo Guide](DEMO.md)

## Network Device Configs
- [Router Show Commands](configs/router_show_commands.txt)
- [Dept-Switch Show Commands](configs/dept_switch_show_commands.txt)
- [Server-Switch Show Commands](configs/server_switch_show_commands.txt)
- [ACL Verification](configs/acl_verification.txt)
---

*Swayam Chopra · UMBC Information Systems '26 · [LinkedIn](https://linkedin.com/in/swayam-chopra100)*
