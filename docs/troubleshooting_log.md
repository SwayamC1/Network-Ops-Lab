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
