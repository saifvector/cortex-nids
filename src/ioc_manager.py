"""
IOC Manager module for NIDS.
Manages malicious IP lists, whitelists, blacklists, and known Indicators of Compromise (IOCs).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from src.utils.utils import ensure_directory, get_absolute_path, load_json, save_json

logger = logging.getLogger(__name__)


class IOCManager:
    """
    Manages Indicators of Compromise (IOCs), Whitelists, Blacklists, and IP Reputation lists.
    """

    def __init__(self, db_path: Union[str, Path] = "predictions/ioc_database.json"):
        self.db_path = get_absolute_path(db_path)
        ensure_directory(self.db_path.parent)

        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.known_malicious_ips: Dict[str, Dict[str, Any]] = {}
        self.known_iocs: Dict[str, Dict[str, Any]] = {}

        self._load_database()

    def _load_database(self) -> None:
        """Loads IOC database from JSON file if exists, or initializes default rules."""
        if self.db_path.exists():
            try:
                data = load_json(self.db_path)
                self.whitelist = set(data.get("whitelist", []))
                self.blacklist = set(data.get("blacklist", []))
                self.known_malicious_ips = data.get("known_malicious_ips", {})
                self.known_iocs = data.get("known_iocs", {})
                logger.info("Loaded IOC database (%d whitelist, %d blacklist, %d IOCs)",
                            len(self.whitelist), len(self.blacklist), len(self.known_iocs))
                return
            except Exception as e:
                logger.error("Failed loading IOC database: %s. Using defaults.", e)

        # Default rules initialization
        self.whitelist = {"127.0.0.1", "::1", "192.168.1.1"}
        self.blacklist = {"198.51.100.14", "203.0.113.55", "185.220.101.5"}
        self.known_malicious_ips = {
            "185.220.101.5": {"category": "Tor Exit Node", "threat_score": 95, "first_seen": "2026-01-10"},
            "198.51.100.14": {"category": "Botnet C2", "threat_score": 90, "first_seen": "2026-02-14"},
            "203.0.113.55": {"category": "DDoS Attacker", "threat_score": 85, "first_seen": "2026-03-01"}
        }
        self.save_database()

    def save_database(self) -> None:
        """Saves current state to JSON database."""
        data = {
            "whitelist": list(self.whitelist),
            "blacklist": list(self.blacklist),
            "known_malicious_ips": self.known_malicious_ips,
            "known_iocs": self.known_iocs
        }
        save_json(data, self.db_path)

    def is_whitelisted(self, ip_address: str) -> bool:
        """Checks if an IP address is in the trusted whitelist."""
        return ip_address in self.whitelist

    def is_blacklisted(self, ip_address: str) -> bool:
        """Checks if an IP address is in the blacklist."""
        return ip_address in self.blacklist

    def match_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Matches an IP against whitelist, blacklist, and known IOC databases.

        Returns:
            Dictionary detailing match status, category, and threat override flags.
        """
        if self.is_whitelisted(ip_address):
            return {"matched": True, "type": "whitelist", "action": "allow", "threat_score": 0}

        if self.is_blacklisted(ip_address):
            return {"matched": True, "type": "blacklist", "action": "block", "threat_score": 100}

        if ip_address in self.known_malicious_ips:
            info = self.known_malicious_ips[ip_address]
            return {
                "matched": True,
                "type": "malicious_ip",
                "category": info.get("category", "Threat Feed"),
                "threat_score": info.get("threat_score", 80),
                "action": "flag"
            }

        return {"matched": False, "type": "none", "action": "inspect", "threat_score": 0}

    def add_to_whitelist(self, ip_address: str) -> None:
        """Adds an IP address to the whitelist."""
        self.whitelist.add(ip_address)
        self.blacklist.discard(ip_address)
        self.save_database()
        logger.info("Added IP %s to Whitelist.", ip_address)

    def add_to_blacklist(self, ip_address: str, category: str = "Manual Block") -> None:
        """Adds an IP address to the blacklist."""
        self.blacklist.add(ip_address)
        self.whitelist.discard(ip_address)
        self.known_malicious_ips[ip_address] = {
            "category": category,
            "threat_score": 100,
            "first_seen": "2026-07-26"
        }
        self.save_database()
        logger.info("Added IP %s to Blacklist (%s).", ip_address, category)

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistics on active IOC rules."""
        return {
            "whitelist_count": len(self.whitelist),
            "blacklist_count": len(self.blacklist),
            "known_malicious_ips_count": len(self.known_malicious_ips),
            "known_iocs_count": len(self.known_iocs)
        }
