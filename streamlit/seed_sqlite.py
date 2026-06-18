# ============================================================
# Meridian Solutions | Network Operations Lab
# File: seed_sqlite.py
# Description: Creates a local SQLite database with sample
#              data for the live Streamlit Cloud deployment.
#              SQL Server is used in production (see schema.sql)
# Author: Swayam Chopra
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
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id     INTEGER NOT NULL REFERENCES hosts(host_id),
    started_at  TEXT NOT NULL,
    resolved_at TEXT,
    description TEXT NOT NULL,
    resolution  TEXT
);
""")

# ─────────────────────────────────────────
# SEED HOSTS
# ─────────────────────────────────────────

hosts = [
    ("Meridian-Router", "192.168.10.1",  "IT Administration", 10),
    ("IT-Admin-PC",     "192.168.10.10", "IT Administration", 10),
    ("Finance-PC",      "192.168.20.10", "Finance",           20),
    ("Ops-PC",          "192.168.30.10", "Operations",        30),
    ("Server",          "192.168.40.10", "Servers",           40),
    ("Guest-PC",        "192.168.50.10", "Guest",             50),
]

cursor.executemany(
    "INSERT INTO hosts (hostname, ip_address, department, vlan) VALUES (?,?,?,?)",
    hosts
)

# ─────────────────────────────────────────
# SEED UPTIME LOG (simulated 24 hours)
# ─────────────────────────────────────────

now = datetime.now()
logs = []

for host_id in range(1, 7):
    for hours_ago in range(24, 0, -1):
        checked_at = now - timedelta(hours=hours_ago)
        # Server goes offline between hours 10-12 ago
        if host_id == 5 and 10 <= hours_ago <= 12:
            is_online   = 0
            response_ms = None
        # Finance-PC goes offline between hours 5-6 ago
        elif host_id == 3 and 5 <= hours_ago <= 6:
            is_online   = 0
            response_ms = None
        else:
            is_online   = 1
            response_ms = random.randint(1, 12)
        logs.append((host_id, checked_at.strftime("%Y-%m-%d %H:%M:%S"), is_online, response_ms))

cursor.executemany(
    "INSERT INTO uptime_log (host_id, checked_at, is_online, response_ms) VALUES (?,?,?,?)",
    logs
)

# ─────────────────────────────────────────
# SEED INCIDENTS
# ─────────────────────────────────────────

incidents = [
    # Resolved: wrong VLAN assignment (from our real Packet Tracer work)
    (2,
     (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
     (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
     "IT-Admin-PC had 100% packet loss to all destinations including default gateway.",
     "Root cause: Fa0/2 on Dept-Switch was assigned to VLAN 40 (Servers) instead of VLAN 10 (IT-Admin). Fixed by reassigning port to correct VLAN. Verified with successful ping."),
    # Resolved: Server went offline
    (5,
     (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
     (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"),
     "Server not responding to ping. Uptime monitor auto-created incident.",
     "Server rebooted after scheduled maintenance window. Host came back online automatically."),
    # Resolved: Finance-PC
    (3,
     (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
     (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
     "Finance-PC went offline during business hours.",
     "User had accidentally unplugged the network cable. Reconnected and verified connectivity."),
]

cursor.executemany(
    """INSERT INTO incidents
       (host_id, started_at, resolved_at, description, resolution)
       VALUES (?,?,?,?,?)""",
    incidents
)

conn.commit()
conn.close()
print("✅ meridian_ops.db created with sample data.")
