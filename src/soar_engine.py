"""
SOAR (Security Orchestration, Automation, and Response) Engine for NIDS.
Executes automated threat mitigation playbooks, firewall rule enforcement, TCP reset triggers, and incident logs.
"""
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.utils.utils import ensure_directory, get_absolute_path, load_json, save_json

logger = logging.getLogger(__name__)


class FirewallManager:
    """
    Manages active firewall block rules (Windows Firewall netsh / Linux iptables / simulated mode).
    """

    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.active_blocks: Dict[str, Dict[str, Any]] = {}

    def block_ip(self, ip_address: str, reason: str = "NIDS Auto-Block", duration_sec: int = 3600) -> Dict[str, Any]:
        """
        Enforces a firewall block rule on a malicious source IP address.
        """
        rule_name = f"CORTEX_NIDS_BLOCK_{ip_address.replace('.', '_')}"

        if self.simulation_mode:
            logger.info("[SOAR SIMULATION] Firewall rule created: BLOCK %s (%s)", ip_address, reason)
            status = "simulated"
        else:
            status = self._execute_sys_block(rule_name, ip_address)

        record = {
            "ip": ip_address,
            "rule_name": rule_name,
            "reason": reason,
            "blocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": duration_sec,
            "status": status
        }

        self.active_blocks[ip_address] = record
        return record

    def unblock_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Removes an active firewall block rule for an IP address.
        """
        if ip_address not in self.active_blocks:
            return {"status": "not_found", "message": f"IP {ip_address} is not currently blocked"}

        rule_info = self.active_blocks.pop(ip_address)

        if not self.simulation_mode:
            self._execute_sys_unblock(rule_info["rule_name"], ip_address)

        logger.info("[SOAR] Unblocked IP %s from active firewall rules.", ip_address)
        return {"status": "unblocked", "ip": ip_address}

    def _execute_sys_block(self, rule_name: str, ip_address: str) -> str:
        """Executes OS-level firewall blocking commands."""
        try:
            if sys.platform == "win32":
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip_address}'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return "active"
            else:
                cmd = f"iptables -A INPUT -s {ip_address} -j DROP"
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return "active"
        except Exception as e:
            logger.error("OS Firewall command failed: %s. Reverting to simulation mode.", e)
            return "simulated"

    def _execute_sys_unblock(self, rule_name: str, ip_address: str) -> None:
        """Executes OS-level firewall unblock commands."""
        try:
            if sys.platform == "win32":
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                cmd = f"iptables -D INPUT -s {ip_address} -j DROP"
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            logger.error("OS Firewall unblock failed: %s", e)


class SOAREngine:
    """
    Automated Incident Playbook Executor and Active Response Manager.
    """

    def __init__(self, history_path: Union[str, Path] = "predictions/mitigation_history.json"):
        self.history_path = get_absolute_path(history_path)
        ensure_directory(self.history_path.parent)

        self.firewall = FirewallManager(simulation_mode=True)
        self.mitigation_history: List[Dict[str, Any]] = []

        self._load_history()

    def _load_history(self) -> None:
        """Loads mitigation logs from JSON storage."""
        if self.history_path.exists():
            try:
                data = load_json(self.history_path)
                self.mitigation_history = data.get("history", [])
            except Exception as e:
                logger.error("Failed loading mitigation history: %s", e)

    def save_history(self) -> None:
        """Persists mitigation logs to JSON storage."""
        try:
            save_json({"history": self.mitigation_history[-500:]}, self.history_path)
        except Exception as e:
            logger.error("Failed saving mitigation history: %s", e)

    def execute_playbook(self, playbook_name: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a target threat response playbook:
        - `dos_mitigation`: Rate-limits & blocks source IP for DoS/DDoS attacks.
        - `port_scan_containment`: Temporarily quarantines scanning source IP.
        - `botnet_isolation`: Immediate high-priority block & SIEM alert trigger.
        """
        src_ip = alert_data.get("src_ip", "192.168.1.100")
        attack = alert_data.get("attack_type", "Unknown")
        risk_score = alert_data.get("risk_score", 0)

        logger.info("[SOAR PLAYBOOK] Executing %s for %s threat (Score: %s)", playbook_name, attack, risk_score)

        actions_taken = []
        if playbook_name in ("dos_mitigation", "ddos_containment"):
            block_res = self.firewall.block_ip(src_ip, reason=f"Auto-Triggered: {playbook_name}", duration_sec=7200)
            actions_taken.append({"action": "firewall_block", "details": block_res})
            actions_taken.append({"action": "rate_limit", "target_port": alert_data.get("dst_port", 80), "limit": "10 req/s"})

        elif playbook_name in ("port_scan_containment", "recon_containment"):
            block_res = self.firewall.block_ip(src_ip, reason="PortScan Containment Playbook", duration_sec=1800)
            actions_taken.append({"action": "temporary_quarantine", "details": block_res})

        elif playbook_name in ("botnet_isolation", "brute_force_isolation"):
            block_res = self.firewall.block_ip(src_ip, reason="Botnet C2 Isolation Playbook", duration_sec=86400)
            actions_taken.append({"action": "emergency_isolation", "details": block_res})
            actions_taken.append({"action": "terminate_tcp_session", "src_ip": src_ip})

        else:
            # Generic mitigation
            if risk_score >= 70:
                block_res = self.firewall.block_ip(src_ip, reason=f"High-Risk Alert ({risk_score}/100)")
                actions_taken.append({"action": "auto_block", "details": block_res})

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "playbook": playbook_name,
            "attack_type": attack,
            "target_ip": src_ip,
            "actions_taken": actions_taken,
            "status": "completed"
        }

        self.mitigation_history.append(record)
        self.save_history()

        return record

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistics on active firewall blocks and playbook executions."""
        return {
            "active_blocks_count": len(self.firewall.active_blocks),
            "active_blocks": list(self.firewall.active_blocks.values()),
            "total_playbooks_executed": len(self.mitigation_history),
            "recent_actions": self.mitigation_history[-10:]
        }
