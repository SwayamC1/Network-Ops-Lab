import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect("meridian_ops.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT h.hostname, h.ip_address, h.department, h.vlan,
           CASE WHEN u.is_online = 1 THEN 'Online' ELSE 'Offline' END AS status,
           u.response_ms, u.checked_at
    FROM hosts h
    JOIN uptime_log u ON u.log_id = (
        SELECT log_id FROM uptime_log
        WHERE host_id = h.host_id
        ORDER BY checked_at DESC LIMIT 1
    )
""")
current_status = [dict(r) for r in cursor.fetchall()]

cursor.execute("""
    SELECT h.hostname, h.department,
           ROUND(SUM(u.is_online) * 100.0 / COUNT(*), 2) AS uptime_pct,
           AVG(CASE WHEN u.is_online = 1 THEN u.response_ms END) AS avg_response_ms
    FROM hosts h
    JOIN uptime_log u ON u.host_id = h.host_id
    GROUP BY h.host_id, h.hostname, h.department
""")
uptime = [dict(r) for r in cursor.fetchall()]

cursor.execute("""
    SELECT h.hostname, h.department,
           i.started_at, i.resolved_at,
           i.description, i.resolution,
           CASE WHEN i.resolved_at IS NULL THEN 'Open' ELSE 'Resolved' END AS status
    FROM incidents i
    JOIN hosts h ON h.host_id = i.host_id
    ORDER BY i.started_at DESC
""")
incidents = [dict(r) for r in cursor.fetchall()]

cursor.execute("""
    SELECT h.hostname, u.checked_at, u.response_ms
    FROM uptime_log u
    JOIN hosts h ON h.host_id = u.host_id
    WHERE u.is_online = 1
    ORDER BY u.checked_at ASC
""")
history = [dict(r) for r in cursor.fetchall()]

output = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "current_status": current_status,
    "uptime": uptime,
    "incidents": incidents,
    "response_history": history
}

with open("dashboard_data.json", "w") as f:
    json.dump(output, f, indent=2)

conn.close()
print("✅ dashboard_data.json created.")
