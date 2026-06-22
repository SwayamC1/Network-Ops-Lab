Network Operations & Monitoring Lab

Cisco Packet Tracer · Python · SQL Server · Streamlit · Grafana

Designed a simulated small-business network operations lab to demonstrate VLAN segmentation, inter-VLAN routing, ACL enforcement, automated host and service monitoring, SQL Server incident tracking, backup/restore procedures, and dashboard reporting.

[![Grafana](https://img.shields.io/badge/Grafana-Live%20Dashboard-orange?logo=grafana)](https://tealjeep3109.grafana.net/public-dashboards/2fe1661bb8c7468d90b36d95464d0591)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-Developer-red?logo=microsoftsqlserver)](https://microsoft.com/sql-server)

---

## Public Demo Dashboard
**[→ Meridian Network Operations Center on Grafana](https://tealjeep3109.grafana.net/public-dashboards/2fe1661bb8c7468d90b36d95464d0591)**

The public Grafana dashboard uses exported demo data so the project can be reviewed without requiring access to my local SQL Server instance. The production-style local setup uses SQL Server, where monitor.py writes uptime logs and incident records directly to the database.

---

What I Built

The fictional company is Meridian Solutions, a small-business network environment with separate segments for IT Administration, Finance, Operations, Servers, and Guest access.

I treated this project like a junior network operations/admin lab: I designed the network, segmented it with VLANs, enforced a Guest-to-Server access restriction, built a Python monitor, logged operational data to SQL Server, created incident tracking, documented troubleshooting steps, and built dashboard views for status reporting.

The four main parts:

Designed and configured a segmented network in Cisco Packet Tracer using VLANs, trunking, inter-VLAN routing, and ACLs
Wrote a Python monitor that checks host reachability and service ports, then logs results to SQL Server
Built a SQL Server database with normalized tables, reporting views, indexes, least-privilege users, and backup/restore procedures
Created dashboard reporting using Streamlit locally and Grafana for a public demo view



---

## Screenshots

### Network Topology
![Topology](Screenshots/The%20full%20topology%20diagram.png)

### ACL Security Test — Guest VLAN Blocked from Server
![ACL Test](Screenshots/The%20Guest%20ping%20result.png)

### Public Grafana NOC Demo Dashboard
![Dashboard](Screenshots/Network-Lab-Monitor-Dashboard.png)

---

## Part 1 — Network Design (Cisco Packet Tracer)

Cisco Packet Tracer is commonly used in CCNA training and network fundamentals labs. I used it to build a realistic small-office topology with VLAN segmentation, inter-VLAN routing, trunking, and ACL-based access control.

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

`monitor.py` connects to the SQL Server database and checks every active host on a 60-second loop. For each host, it runs two types of checks:

**1. ICMP ping** — confirms the host is reachable on the network
**2. TCP port checks** — confirms expected services are reachable on their assigned ports

| Host            | Ports Checked                             |
| --------------- | ----------------------------------------- |
| Meridian-Router | SSH (22)                                  |
| IT-Admin-PC     | RDP (3389)                                |
| Finance-PC      | RDP (3389)                                |
| Ops-PC          | RDP (3389)                                |
| Server          | HTTP (80), HTTPS (443), SQL Server (1433) |
| Guest-PC        | HTTP (80)                                 |

The monitor creates two types of incidents:

| Incident Type    | Example                                                   | Meaning                                                    |
| ---------------- | --------------------------------------------------------- | ---------------------------------------------------------- |
| Host incident    | `HOST DOWN: Server is not responding to ping.`            | The device is unreachable                                  |
| Service incident | `SERVICE DOWN: SQL Server port 1433 is closed on Server.` | The host is online, but an expected service is unavailable |

When a host stops responding, the script automatically opens a host-level incident in SQL Server. When the host comes back online, the incident is auto-resolved.

When a host is online but an expected TCP port is closed, the script opens a service-level incident. When the port becomes reachable again, the service incident is auto-resolved.

```python
# Each host gets ICMP ping + TCP port checks
is_online, response_ms = ping_host(ip)
handle_host_incident(conn, host_id, hostname, is_online)

for port, service in HOST_PORTS.get(hostname, []):
    is_open = check_port(ip, port) if is_online else False
    if is_online:
        handle_service_incident(conn, host_id, hostname, service, port, is_open)

log_result(conn, host_id, is_online, response_ms, notes)
```


---

## Part 3 — SQL Server Database

I used **SQL Server Developer Edition** (free) and **SSMS** — the same tools used in enterprise environments.

**Schema:**
- `hosts` — every monitored device
- `uptime_log` — one row per ping check per host
- `incidents` — host and service incident records with timestamps and resolution notes
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

---
## Part 4 — Dashboard Reporting

The project includes two dashboard/reporting options:

1. **Local Streamlit dashboard** — reads directly from SQL Server and shows current host status, uptime percentage, incident records, and response-time history
2. **Public Grafana demo dashboard** — reads exported demo JSON data so the project can be reviewed publicly without requiring access to my local SQL Server environment

I used Grafana for the public-facing demo because operational teams commonly use dashboarding tools to monitor infrastructure health, incident trends, and service availability.

**Panels include:**

* Host status table with department, IP address, response time, and online/offline state
* Uptime percentage by host
* Incident log with descriptions and resolution notes
* Response-time history for monitored devices

---

## SQL Server vs SQLite — Why Both Exist

The operational monitor (`monitor.py`) and local Streamlit dashboard (`dashboard.py`) are built for **SQL Server** using `pyodbc`. This is the production-style setup and demonstrates SQL Server schema design, user permissions, reporting views, backup/restore procedures, and parameterized queries.

For public demo hosting, I included a separate SQLite database (`meridian_ops.db`) seeded with 24 hours of simulated monitoring data. This allows the public dashboard/demo files to be viewed without requiring access to my local SQL Server instance.

---

## Project Scope and Limitations

This is a simulated network operations lab built for portfolio and resume demonstration. The network topology was created in Cisco Packet Tracer rather than on physical Cisco hardware.

The local production-style setup uses SQL Server, `monitor.py`, and the Streamlit dashboard. The public Grafana dashboard uses exported demo data so recruiters and reviewers can view the project without needing my local database connection.

This project is intended to demonstrate junior-level network operations skills, including network segmentation, access control verification, Python automation, SQL Server administration, incident tracking, backup/restore documentation, and technical troubleshooting.


| Component             | Database   | Purpose                                                      |
| --------------------- | ---------- | ------------------------------------------------------------ |
| `monitor.py`          | SQL Server | Logs host reachability, service check results, and incidents |
| `dashboard.py`        | SQL Server | Local Streamlit dashboard reading from SQL Server            |
| `seed_sqlite.py`      | SQLite     | Seeds demo data for public dashboard review                  |
| `dashboard_data.json` | —          | Exported demo data used by Grafana                           |

---




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
| Grafana dashboard configuration | Public demo dashboard |
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
