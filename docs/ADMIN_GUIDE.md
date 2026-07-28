# Administrator & Security Engineer Guide

This guide covers governance, secrets management, Role-Based Access Control (RBAC), SIEM exporter integration, and SOAR automated mitigation.

---

## 🔒 Role-Based Access Control (RBAC)

The system enforces 5 distinct roles:

| Role | View Dashboard | Run Predictions | Execute SOAR Blocks | Manage Users |
| :--- | :---: | :---: | :---: | :---: |
| **Administrator** | ✅ | ✅ | ✅ | ✅ |
| **SOC Analyst** | ✅ | ✅ | ✅ | ❌ |
| **Security Engineer** | ✅ | ✅ | ❌ | ❌ |
| **Read Only** | ✅ | ❌ | ❌ | ❌ |
| **Guest** | ❌ | ❌ | ❌ | ❌ |

### Managing Users via CLI:
```bash
# Add a new SOC Analyst
python scripts/run_security.py --create-user "john_doe" --role "SOC Analyst"
```

---

## 🔌 SIEM Integration & Exporters

Configure SIEM exports in `.env`:

```env
# Elastic Stack Export
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_INDEX=nids-alerts-v1

# Splunk HEC Export
SPLUNK_ENABLED=true
SPLUNK_HEC_URL=https://splunk.local:8088/services/collector
SPLUNK_HEC_TOKEN=your-splunk-token-here

# Microsoft Sentinel Export
SENTINEL_ENABLED=true
SENTINEL_WORKSPACE_ID=your-workspace-id
SENTINEL_SHARED_KEY=your-shared-key
```

### Test SIEM Connectors:
```bash
python scripts/run_siem.py
```

---

## ⚡ SOAR Automated Response & Firewall Mitigation

Configure automatic IP blocking for critical threats:

```env
SOAR_ENABLED=true
SOAR_AUTO_BLOCK_CRITICAL=true
SOAR_BLOCK_DURATION_MINUTES=60
```

### Run Active Response Playbook:
```bash
python scripts/run_soar.py --block-ip 185.220.101.5
```
- **Windows**: Executes `netsh advfirewall firewall add rule name="NIDS_BLOCK_185.220.101.5" dir=in action=block remoteip=185.220.101.5`.
- **Linux**: Executes `iptables -A INPUT -s 185.220.101.5 -j DROP`.
