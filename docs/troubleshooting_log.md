# Meridian Solutions — Troubleshooting Log

---

## Incident 1 — IT-Admin-PC: 100% Packet Loss to All Destinations

**Date:** 2026-06-16
**Severity:** High
**Affected host:** IT-Admin-PC (192.168.10.10)
**Detection:** Manual ping test during initial network verification

### Symptoms
- IT-Admin-PC had 100% packet loss to all destinations
- Could not reach default gateway (192.168.10.1)
- Could not reach Finance-PC (192.168.20.10) or Server (192.168.40.10)
- All other hosts on Dept-Switch were unaffected

### Diagnosis
Ran `show ip interface brief` on Meridian-Router — all interfaces showed up with correct IPs. Problem was not the router.

Ran `show vlan brief` on Dept-Switch and found:

IT-Admin-PC was physically connected to Fa0/2 but the port was assigned to VLAN 40 (Servers) instead of VLAN 10 (IT-Admin).

### Root Cause
During initial switch configuration, a console session reset mid-configuration. The VLAN assignment for Fa0/2 was saved incorrectly as VLAN 40 instead of VLAN 10, placing IT-Admin-PC in the wrong network segment.

### Fix


**Time to resolve:** 15 minutes
**Status:** Resolved ✅

---

## Incident 2 — Guest-PC Blocked from Server (ACL Verification)

**Date:** 2026-06-16
**Severity:** Informational
**Purpose:** Verify ACL BLOCK-GUEST is enforcing the Guest → Server restriction

### Test
From Guest-PC command prompt, tested two destinations:
- `ping 192.168.40.10` — Server (should be blocked by ACL)
- `ping 192.168.20.10` — Finance-PC (should be allowed)

### Results



### Conclusion
ACL BLOCK-GUEST is working as designed. Guest users cannot reach the Server VLAN (40) but retain normal access to department VLANs. Security policy is enforced correctly at the router sub-interface level.

**Status:** Verified ✅

---

## Incident 3 — Server Offline During Maintenance Window

**Date:** 2026-06-16
**Severity:** Medium
**Affected host:** Server (192.168.40.10)
**Detection:** Python monitor auto-opened incident after consecutive failed pings

### Symptoms
- Python monitor logged Server as offline for approximately 2 hours
- Incident auto-created in SQL Server incidents table with timestamp
- All other hosts remained online throughout

### Diagnosis
Checked Server-Switch port assignment — Fa0/2 correctly assigned to VLAN 40. Checked router sub-interface GigabitEthernet0/0/1 — up with correct IP (192.168.40.1). Confirmed host was intentionally taken offline for a scheduled maintenance window. Monitor was not notified in advance, triggering a false alert.

### Root Cause
No maintenance window notification process existed. The monitoring script correctly detected the outage but had no way to distinguish planned from unplanned downtime.

### Fix
No configuration change required. Server came back online after maintenance completed and the Python monitor auto-resolved the incident on the next successful ping cycle.

Added the following note to the backup/restore runbook: notify the monitoring team before any planned maintenance window to prevent false incident creation.

### Validation

**Time to resolve:** 2 hours (planned maintenance window)
**Status:** Resolved ✅


