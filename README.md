# Network Operations & Monitoring Lab

**Cisco Packet Tracer · Python · SQL Server · Streamlit · Grafana**

Designed a simulated small-business network operations lab to demonstrate VLAN segmentation, inter-VLAN routing, ACL enforcement, automated host and service monitoring, SQL Server incident tracking, backup/restore procedures, and dashboard reporting.

[![Grafana](https://img.shields.io/badge/Grafana-Public%20Demo%20Dashboard-orange?logo=grafana)](https://tealjeep3109.grafana.net/public-dashboards/2fe1661bb8c7468d90b36d95464d0591)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-Developer-red?logo=microsoftsqlserver)](https://microsoft.com/sql-server)

---

## Public Demo Dashboard

**[→ Meridian Network Operations Center on Grafana](https://tealjeep3109.grafana.net/public-dashboards/2fe1661bb8c7468d90b36d95464d0591)**

The public Grafana dashboard uses exported demo data so the project can be reviewed without requiring access to my local SQL Server instance. The production-style local setup uses SQL Server, where `monitor.py` writes uptime logs and incident records directly to the database.

---

## What I Built

The fictional company is **Meridian Solutions**, a small-business network environment with separate segments for IT Administration, Finance, Operations, Servers, and Guest access.

I treated this project like a junior network operations/admin lab: I designed the network, segmented it with VLANs, enforced a Guest-to-Server access restriction, built a Python monitor, logged operational data to SQL Server, created incident tracking, documented troubleshooting steps, and built dashboard views for status reporting.

**The four main parts:**

1. Designed and configured a segmented network in Cisco Packet Tracer using VLANs, trunking, inter-VLAN routing, and ACLs
2. Wrote a Python monitor that checks host reachability and service ports, then logs results to SQL Server
3. Built a SQL Server database with normalized tables, reporting views, indexes, least-privilege users, and backup/restore procedures
4. Created dashboard reporting using Streamlit locally and Grafana for a public demo view

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

| VLAN | Name       | Subnet          | Purpose               |
| ---- | ---------- | --------------- | --------------------- |
| 10   | IT-Admin   | 192.168.10.0/24 | IT staff              |
| 20   | Finance    | 192.168.20.0/24 | Finance department    |
| 30   | Operations | 192.168.30.0/24 | Operations department |
| 40   | Servers    | 192.168.40.0/24 | Internal servers      |
| 50   | Guest      | 192.168.50.0/24 | Guest access          |

**Inter-VLAN routing** is handled through router-on-a-stick for the department VLANs. One physical router interface carries tagged VLAN traffic using subinterfaces. The Server VLAN uses a separate routed interface connected to the Server-Switch access uplink.

**Security rule:** ACL `BLOCK-GUEST` blocks the Guest VLAN from reaching the Server VLAN. I tested and verified this: Guest-PC cannot reach the Server, but it can still reach allowed department VLANs.

**Troubleshooting example:** During setup, IT-Admin-PC had 100% packet loss. I diagnosed it with `show vlan brief` and found `Fa0/2` was assigned to VLAN 40 instead of VLAN 10. I fixed the port assignment and verified connectivity with pings. This is documented in the troubleshooting log.

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

I used **SQL Server Developer Edition** and **SQL Server Management Studio (SSMS)** to build the production-style database setup.

**Schema:**

* `hosts` — every monitored device
* `uptime_log` — one row per monitoring check per host
* `incidents` — host and service incident records with timestamps and resolution notes
* `v_host_uptime` — reporting view calculating uptime percentage per host
* `v_current_status` — reporting view showing each host's most recent status
* `v_open_incidents` — reporting view for unresolved incidents
* `v_incident_history` — reporting view for open and resolved incidents
* `v_response_time_history` — reporting view for dashboard response-time charts

**DBA tasks completed:**

* Created a normalized SQL Server schema for host monitoring and incident tracking
* Added indexes for uptime queries and open incident lookups
* Created reporting views for dashboards and validation
* Created SQL Server logins and database users with least-privilege permissions
* Separated monitor write access from dashboard read-only access
* Built a full backup, differential backup, restore, and validation runbook
* Added a validation script to test hosts, views, incidents, and permissions

All SQL files are in the `/SQL` folder.

---

## Part 4 — Dashboard Reporting

The project includes two dashboard/reporting options:

1. **Local Streamlit dashboard** — reads directly from SQL Server and shows current host status, uptime percentage, incident records, service issues, and response-time history
2. **Public Grafana demo dashboard** — reads exported demo JSON data so the project can be reviewed publicly without requiring access to my local SQL Server environment

I used Grafana for the public-facing demo because operational teams commonly use dashboarding tools to monitor infrastructure health, incident trends, and service availability.

**Panels include:**

* Host status table with department, IP address, response time, and online/offline state
* Uptime percentage by host
* Incident log with descriptions and resolution notes
* Service-level incident examples
* Response-time history for monitored devices

---

## Skills This Project Covers

| Skill                               | Where Demonstrated                                        |
| ----------------------------------- | --------------------------------------------------------- |
| VLAN configuration                  | Packet Tracer topology and switch configs                 |
| Inter-VLAN routing                  | Router-on-a-stick configuration                           |
| Access Control Lists                | `BLOCK-GUEST` ACL verification                            |
| Network troubleshooting             | Troubleshooting log                                       |
| Cisco show command interpretation   | `/configs` show-command outputs                           |
| Running configuration documentation | `/configs` running-config files                           |
| Python scripting                    | `monitor.py`                                              |
| Host availability monitoring        | ICMP ping checks in `monitor.py`                          |
| Service availability monitoring     | TCP port checks in `monitor.py`                           |
| Incident tracking                   | SQL Server `incidents` table                              |
| SQL Server schema design            | `SQL/schema.sql`                                          |
| SQL reporting views                 | `v_current_status`, `v_host_uptime`, `v_incident_history` |
| Role-based access control           | `SQL/security_roles.sql`                                  |
| Database backup and restore         | `SQL/backup_restore_runbook.sql`                          |
| SQL validation/testing              | `SQL/validation_checks.sql`                               |
| Dashboard reporting                 | Streamlit local dashboard and Grafana public demo         |
| Technical documentation             | `README.md`, `DEMO.md`, `/docs`, `/configs`               |

---

## SQL Server vs SQLite — Why Both Exist

The operational monitor (`monitor.py`) and local Streamlit dashboard (`dashboard.py`) are built for **SQL Server** using `pyodbc`. This is the production-style setup and demonstrates SQL Server schema design, user permissions, reporting views, backup/restore procedures, and parameterized queries.

For public demo hosting, I included a separate SQLite database (`meridian_ops.db`) seeded with 24 hours of simulated monitoring data. This allows the public dashboard/demo files to be viewed without requiring access to my local SQL Server instance.

| Component                    | Database      | Purpose                                                      |
| ---------------------------- | ------------- | ------------------------------------------------------------ |
| `monitor.py`                 | SQL Server    | Logs host reachability, service check results, and incidents |
| `streamlit/dashboard.py`     | SQL Server    | Local Streamlit dashboard reading from SQL Server            |
| `streamlit/seed_sqlite.py`   | SQLite        | Seeds demo data for public dashboard review                  |
| `streamlit/app.py`           | SQLite        | Public demo Streamlit dashboard using sample data            |
| `streamlit/generate_json.py` | SQLite → JSON | Exports demo data for Grafana                                |
| `dashboard_data.json`        | —             | Exported demo data used by Grafana                           |

---

## Project Scope and Limitations

This is a simulated network operations lab built for portfolio and resume demonstration. The network topology was created in Cisco Packet Tracer rather than on physical Cisco hardware.

The local production-style setup uses SQL Server, `monitor.py`, and the Streamlit dashboard. The public Grafana dashboard uses exported demo data so recruiters and reviewers can view the project without needing my local database connection.

This project is intended to demonstrate junior-level network operations skills, including network segmentation, access control verification, Python automation, SQL Server administration, incident tracking, backup/restore documentation, and technical troubleshooting.

---

## How to Verify the Project

A reviewer can verify the project through the following files and steps:

1. Open `DEMO.md` for the end-to-end walkthrough
2. Review `/configs` for Cisco show commands and sanitized running configs
3. Run `SQL/schema.sql` and `SQL/security_roles.sql` in SSMS
4. Run `SQL/validation_checks.sql` to verify hosts, views, incidents, and permissions
5. Run `python monitor.py` to start host and service monitoring
6. Run `streamlit run streamlit/dashboard.py` to view the local SQL Server dashboard

The public Grafana dashboard is included as a demo view using exported sample data. The local production-style workflow uses SQL Server directly.

---

## Local Setup

Clone the repository:

```bash
git clone https://github.com/SwayamC1/Network-Ops-Lab.git
cd Network-Ops-Lab
```

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file from the included example file:

```bash
copy .env.example .env
```

Then update `.env` with your local SQL Server credentials:

```env
DB_SERVER=localhost
DB_NAME=MeridianOps

DB_USER=NetworkMonitor
DB_PASSWORD=<your_network_monitor_password>

DB_DASHBOARD_USER=ReadOnlyUser
DB_DASHBOARD_PASSWORD=<your_readonly_password>
```

`monitor.py` uses the `NetworkMonitor` account to write uptime logs and incidents. The Streamlit dashboard can use the optional `ReadOnlyUser` account so reporting access stays separate from write access.

Credentials are stored locally in `.env` and excluded from GitHub by `.gitignore`.

Set up the database in SSMS:

```text
SQL/schema.sql
SQL/security_roles.sql
SQL/validation_checks.sql
```

Start the network monitor:

```bash
python monitor.py
```

Run the local SQL Server dashboard:

```bash
streamlit run streamlit/dashboard.py
```

---

## Public Demo Data Setup

The public demo uses SQLite-generated sample data and exported JSON so the project can be viewed without requiring access to the local SQL Server database.

To regenerate the SQLite demo database:

```bash
cd streamlit
python seed_sqlite.py
```

To regenerate the JSON file used for public dashboard/demo data:

```bash
python generate_json.py
```

Expected generated demo data:

* 6 monitored hosts
* 24 hours of sample uptime records
* Host-level incidents
* Service-level incidents
* Response-time history for dashboard visualization

---

## Documentation

* [Demo Guide](DEMO.md)
* [IP Addressing Plan](docs/ip_addressing_plan.md)
* [Troubleshooting Log](docs/troubleshooting_log.md)
* [Backup & Restore Runbook](SQL/backup_restore_runbook.sql)
* [SQL Validation Checks](SQL/validation_checks.sql)

---

## Network Device Configs

* [Router Show Commands](configs/router_show_commands.txt)
* [Dept-Switch Show Commands](configs/dept_switch_show_commands.txt)
* [Server-Switch Show Commands](configs/server_switch_show_commands.txt)
* [ACL Verification](configs/acl_verification.txt)
* [Router Running Config](configs/router_running_config.txt)
* [Dept-Switch Running Config](configs/dept_switch_running_config.txt)
* [Server-Switch Running Config](configs/server_switch_running_config.txt)

---

*Swayam Chopra · UMBC Information Systems '26 · [LinkedIn](https://linkedin.com/in/swayam-chopra100)*
