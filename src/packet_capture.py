"""
Packet Capture module for NIDS.
Detects network interfaces and captures live TCP, UDP, ICMP, HTTP, HTTPS, DNS, FTP, and SSH packets using Scapy.
Supports Layer 3 sockets and synthetic packet generator fallback when Npcap / Administrator rights are absent.
"""
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from scapy.all import sniff, get_if_list, conf, IP, TCP, UDP, ICMP
    SCAPY_AVAILABLE = True
except Exception as e:
    SCAPY_AVAILABLE = False

from src.utils.utils import get_absolute_path

logger = logging.getLogger(__name__)


def list_network_interfaces() -> List[Dict[str, str]]:
    """
    Returns a list of available network interfaces detected on the system.
    """
    interfaces = []
    if not SCAPY_AVAILABLE:
        logger.warning("Scapy is not installed or unavailable.")
        return [{"id": "loopback", "name": "Loopback Pseudo-Interface", "status": "active"}]

    try:
        if_list = get_if_list()
        for idx, iface in enumerate(if_list):
            interfaces.append({
                "id": str(iface),
                "name": str(iface),
                "index": str(idx)
            })
    except Exception as e:
        logger.error("Error listing network interfaces: %s", e)
        interfaces.append({"id": "default", "name": "Default Network Interface"})

    return interfaces


class SyntheticPacket:
    """Mock Scapy packet structure for non-privileged packet stream fallback."""

    def __init__(self, src_ip: str, dst_ip: str, proto: str, sport: int, dport: int, length: int):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.proto = proto
        self.sport = sport
        self.dport = dport
        self.length = length

    def haslayer(self, layer: str) -> bool:
        if layer == "IP":
            return True
        return layer == self.proto

    def __getitem__(self, item: str) -> Any:
        if item == "IP":
            class MockIP:
                src = self.src_ip
                dst = self.dst_ip
            return MockIP()
        if item in ("TCP", "UDP"):
            class MockTransport:
                sport = self.sport
                dport = self.dport
                flags = "P"
                window = 8192
                dataofs = 5
            return MockTransport()
        raise KeyError(item)

    def __len__(self) -> int:
        return self.length


class PacketCapturer:
    """
    Monitors live network traffic across TCP, UDP, ICMP, HTTP, HTTPS, DNS, FTP, and SSH protocols.
    Supports live socket sniffing and synthetic fallback when Administrator/Npcap driver is absent.
    """

    def __init__(
        self,
        interface: Optional[str] = None,
        bpf_filter: str = "ip",
        packet_count: int = 0
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.packet_count = packet_count
        self.is_capturing = False
        self.captured_packets_count = 0
        self.dropped_packets_count = 0

    def start_capture(
        self,
        packet_callback: Callable[[Any], None],
        stop_filter: Optional[Callable[[], bool]] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Starts sniffing network traffic continuously or until timeout/stop condition.
        """
        self.is_capturing = True
        logger.info("Starting live packet capture (Interface: %s, Filter: '%s')...", self.interface or "Default", self.bpf_filter)

        def internal_handler(pkt: Any) -> None:
            if not self.is_capturing:
                return
            try:
                self.captured_packets_count += 1
                packet_callback(pkt)
            except Exception as e:
                self.dropped_packets_count += 1
                logger.debug("Error processing captured packet: %s", e)

        # Attempt raw socket sniffing
        sniff_success = False
        if SCAPY_AVAILABLE:
            try:
                sniff(
                    iface=self.interface,
                    filter=self.bpf_filter,
                    prn=internal_handler,
                    count=self.packet_count,
                    timeout=timeout,
                    store=False
                )
                sniff_success = True
            except Exception as e:
                logger.warning("Raw socket packet sniffing restricted (%s). Engaging synthetic live capture mode...", e)

        # Fallback to Synthetic Traffic Generator if raw sockets are restricted
        if not sniff_success and self.is_capturing:
            self._run_synthetic_generator(internal_handler, timeout=timeout)

        self.is_capturing = False
        logger.info(
            "Packet capture stopped. Total Captured: %d, Dropped/Errors: %d",
            self.captured_packets_count, self.dropped_packets_count
        )

    def _run_synthetic_generator(self, callback: Callable[[Any], None], timeout: Optional[float] = None) -> None:
        """Simulates live network traffic packets when non-admin / without Npcap."""
        start_t = time.time()
        protocols = ["TCP", "UDP", "TCP", "TCP"]
        ports = [80, 443, 22, 53, 8080]

        while self.is_capturing:
            if timeout and (time.time() - start_t) >= timeout:
                break

            proto = random.choice(protocols)
            pkt = SyntheticPacket(
                src_ip=f"192.168.1.{random.randint(10, 200)}",
                dst_ip=f"10.0.0.{random.randint(1, 50)}",
                proto=proto,
                sport=random.randint(1024, 65535),
                dport=random.choice(ports),
                length=random.randint(64, 1500)
            )
            callback(pkt)
            time.sleep(random.uniform(0.05, 0.2))

    def stop_capture(self) -> None:
        """Stops the active capture session."""
        self.is_capturing = False
        logger.info("Signaled packet capture to stop.")
