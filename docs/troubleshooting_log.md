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
Ran `show ip interface brief` on Meridian-Router — all interfaces up with correct IPs. Problem was not the router.

Ran `show vlan brief` on Dept-Switch:


IT-Admin-PC was physically connected to Fa0/2 but the port was assigned to VLAN 40 (Servers) instead of VLAN 10 (IT-Admin). Traffic from the PC was going to the wrong VLAN and being dropped.

### Root Cause
During initial switch configuration, a console session reset mid-configuration. The VLAN assignment for Fa0/2 was saved incorrectly as VLAN 40 instead of VLAN 10.

### Fix


### Validation
Ran `show vlan brief` — Fa0/2 now correctly listed under VLAN 10.
Ran ping from IT-Admin-PC:
- `ping 192.168.10.1` → 4/4 replies ✅
- `ping 192.168.20.10` → 4/4 replies ✅
- `ping 192.168.40.10` → 4/4 replies ✅

**Time to resolve:** 15 minutes
**Status:** Resolved ✅

---

## Incident 2 — Guest-PC Blocked from Server (ACL Verification)

**Date:** 2026-06-16
**Severity:** Informational
**Purpose:** Verify ACL BLOCK-GUEST is working correctly

### Test
From Guest-PC, tested two destinations:
- `ping 192.168.40.10` (Server — should be blocked)
- `ping 192.168.20.10` (Finance-PC — should be allowed)

### Results


### Conclusion
ACL is working as intended. Guest users are blocked from the Server VLAN (40) but can reach department VLANs. Security policy enforced correctly.

**Status:** Verified ✅

---

## Incident 3 — Server Offline During Maintenance Window

**Date:** 2026-06-16
**Severity:** Medium
**Affected host:** Server (192.168.40.10)
**Detection:** Python monitor auto-opened incident

### Symptoms
- Python monitor logged Server as offline
- Incident auto-created in SQL Server incidents table
- All other hosts remained online

### Diagnosis
Checked Dept-Switch and Server-Switch port assignments — both correct.
Checked router sub-interface GigabitEthernet0/0/1 — up with correct IP (192.168.40.1).
Determined host was intentionally taken offline for a scheduled maintenance window.
Monitor had not been notified of the maintenance schedule, causing a false alert.

### Root Cause
No maintenance window notification process was in place. The monitoring script treated the planned downtime as an unplanned outage.

### Fix
Server came back online after maintenance completed. Incident auto-resolved by the monitor when the next successful ping was logged.

Added note to runbook: notify monitoring team before any planned maintenance to avoid false incident creation.

**Time to resolve:** 2 hours (planned maintenance window)
**Status:** Resolved ✅
