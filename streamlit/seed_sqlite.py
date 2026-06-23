# ============================================================
# Meridian Solutions | Network Operations Lab
# File: seed_sqlite.py
# Description: Creates a local SQLite database with sample
#              demo data for public dashboard review.
#              SQL Server is used for the production-style setup.
# Author: Swayam Chopra | UMBC MIS 2026
# ============================================================

import sqlite3
from datetime import datetime, timedelta
import random

conn = sqlite3.connect("meridian_ops.db")
cursor = conn.cursor()

# ─────────────────────────────────────────
# TABLES
# ─────────────────────────────────────────

cursor.executescript("""
DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS uptime_log;
DROP TABLE IF EXISTS hosts;

CREATE TABLE hosts (
    host_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname   TEXT NOT NULL,
    ip_address TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    vlan       INTEGER NOT NULL,
    is_active  INTEGER NOT NULL DEFAULT 1,
    added_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE uptime_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id     INTEGER NOT NULL REFERENCES hosts(host_id),
    checked_at  TEXT NOT NULL DEFAULT (datetime('now')),
    is_online   INTEGER NOT NULL,
    response_ms INTEGER,
    notes       TEXT
);

CREATE TABLE incidents (
    incident_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id       INTEGER NOT NULL REFERENCES hosts(host_id),
    incident_type TEXT NOT NULL DEFAULT 'HOST',
    service_name  TEXT,
    port_number   INTEGER,
    started_at    TEXT NOT NULL,
    resolved_at   TEXT,
    description   TEXT NOT NULL,
    resolution    TEXT
);
""")

# ─────────────────────────────────────────
# SEED HOSTS
# ─────────────────────────────────────────

hosts = [
    ("Meridian-Router", "192.168.10.1", "IT Administration", 10),
    ("IT-Admin-PC", "192.168.10.10", "IT Administration", 10),
    ("Finance-PC", "192.168.20.10", "Finance", 20),
    ("Ops-PC", "192.168.30.10", "Operations", 30),
    ("Server", "192.168.40.10", "Servers", 40),
    ("Guest-PC", "192.168.50.10", "Guest", 50),
]

cursor.executemany(
    "INSERT INTO hosts (hostname, ip_address, department, vlan) VALUES (?,?,?,?)",
    hosts
)

# ─────────────────────────────────────────
# SEED UPTIME LOG
# Simulates 24 hours of monitoring
# ─────────────────────────────────────────

now = datetime.now()
logs = []

for host_id in range(1, 7):
    for hours_ago in range(24, 0, -1):
        checked_at = now - timedelta(hours=hours_ago)

        # Server host outage between 12 and 10 hours ago
        if host_id == 5 and 10 <= hours_ago <= 12:
            is_online = 0
            response_ms = None
            notes = None

        # Finance-PC host outage between 6 and 5 hours ago
        elif host_id == 3 and 5 <= hours_ago <= 6:
            is_online = 0
            response_ms = None
            notes = None

        # Ops-PC online, but RDP service issue for a few hours
        elif host_id == 4 and 3 <= hours_ago <= 4:
            is_online = 1
            response_ms = random.randint(2, 15)
            notes = "RDP port 3389 closed"

        # Server online, but SQL Server service issue for a few hours
        elif host_id == 5 and 2 <= hours_ago <= 3:
            is_online = 1
            response_ms = random.randint(2, 15)
            notes = "SQL Server port 1433 closed"

        else:
            is_online = 1
            response_ms = random.randint(1, 12)
            notes = None

        logs.append((
            host_id,
            checked_at.strftime("%Y-%m-%d %H:%M:%S"),
            is_online,
            response_ms,
            notes
        ))

cursor.executemany(
    """
    INSERT INTO uptime_log
        (host_id, checked_at, is_online, response_ms, notes)
    VALUES
        (?,?,?,?,?)
    """,
    logs
)

# ─────────────────────────────────────────
# SEED INCIDENTS
# Includes host-level and service-level examples
# ─────────────────────────────────────────

incidents = [
    (
        2,
        "HOST",
        None,
        None,
        (now - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=17, minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "HOST DOWN: IT-Admin-PC had 100% packet loss to all destinations.",
        "Root cause: Fa0/2 on Dept-Switch was assigned to VLAN 40 instead of VLAN 10. Reassigned the port to VLAN 10 and verified connectivity."
    ),
    (
        5,
        "HOST",
        None,
        None,
        (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "HOST DOWN: Server was not responding to ping during scheduled maintenance.",
        "Server came back online after maintenance completed. Incident auto-resolved on the next successful ping cycle."
    ),
    (
        3,
        "HOST",
        None,
        None,
        (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "HOST DOWN: Finance-PC went offline during business hours.",
        "User had accidentally unplugged the network cable. Reconnected and verified connectivity."
    ),
    (
        4,
        "SERVICE",
        "RDP",
        3389,
        (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "SERVICE DOWN: RDP port 3389 was closed on Ops-PC.",
        "RDP became reachable again after the service was restarted. Incident auto-resolved by monitor."
    ),
    (
        5,
        "SERVICE",
        "SQL Server",
        1433,
        (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "SERVICE DOWN: SQL Server port 1433 was closed on Server.",
        "SQL Server port 1433 became reachable again after the database service restarted. Incident auto-resolved by monitor."
    ),
]

cursor.executemany(
    """
    INSERT INTO incidents
        (host_id, incident_type, service_name, port_number,
         started_at, resolved_at, description, resolution)
    VALUES
        (?,?,?,?,?,?,?,?)
    """,
    incidents
)

conn.commit()
conn.close()

print("✅ meridian_ops.db created with host and service incident demo data.")

