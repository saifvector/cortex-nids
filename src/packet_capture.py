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


USER_APPS = ["brave", "chrome", "edge", "msedge", "firefox", "opera", "anydesk", "curl"]
IGNORED_SYSTEM_NOISE = [
    "python", "python3", "uvicorn", "gunicorn", "node",
    "lockapp.exe", "startmenuexperiencehost.exe", "crossdeviceservice.exe",
    "phoneexperiencehost.exe", "nvcontainer.exe", "nvidia overlay", "nvidia",
    "agy.exe", "copilotapp.exe", "dbus", "kdeconnect", "antigravity"
]

def resolve_service_name(dst_ip: str, dport: int, pname: str = "") -> str:
    """Resolves IP to a human-readable website / service name."""
    pname_lower = pname.lower() if pname else ""

    # 1. Microsoft Cloud & Windows OS Services (StartMenu, Cortana, Azure, Office)
    if dst_ip.startswith(("20.", "40.", "4.213.", "13.107.", "52.96.", "52.97.", "52.98.", "52.99.", "52.10", "52.11")):
        return "Microsoft Windows Services"
    if any(m in pname_lower for m in ["startmenu", "lockapp", "phoneexperience", "crossdevice"]):
        return "Microsoft Windows Services"

    # 2. Google / YouTube
    if dst_ip.startswith(("142.250.", "142.251.", "172.217.", "216.58.", "74.125.", "192.178.")):
        if "agy" in pname_lower:
            return "Google Gemini AI API"
        if "bluestacks" in pname_lower:
            return "Google Play Services"
        return "YouTube / Google"

    # 3. GitHub
    if dst_ip.startswith("140.82."):
        return "GitHub"

    # 4. Amazon Web Services (AWS) / CloudFront CDN
    if dst_ip.startswith(("3.175.", "3.", "54.", "52.25.", "52.14.", "52.84.", "13.227.")):
        if "brave" in pname_lower:
            return "Amazon CloudFront (Brave CDN)"
        return "AWS Cloud"

    # 5. Meta / Instagram
    if dst_ip.startswith(("157.240.", "31.13.")):
        return "Meta / Instagram"

    # 6. Cloudflare CDN
    if dst_ip.startswith(("104.16.", "104.17.", "104.18.", "104.19.", "104.20.", "104.21.", "172.64.", "172.67.")):
        return "Cloudflare CDN"

    # 7. Akamai CDN
    if dst_ip.startswith(("23.53.", "23.63.", "184.26.", "32.189.", "32.190.")):
        return "Akamai Web CDN"

    # 8. Special Apps
    if "anydesk" in pname_lower:
        return "AnyDesk Remote Desktop"

    if dport == 53:
        return "DNS Lookup"
    if dport == 443:
        return "Secure Web (HTTPS)"
    if dport == 80:
        return "Web (HTTP)"
    return f"Host {dst_ip}"


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
        """
        Captures real active host socket connections via psutil when raw Layer-2 packet sniffing (Npcap)
        is restricted or uninstalled. Samples real local IP, remote server IP, and port pairs.
        """
        start_t = time.time()
        try:
            import psutil
            import socket as py_socket
            has_psutil = True
        except ImportError:
            has_psutil = False

        while self.is_capturing:
            if timeout and (time.time() - start_t) >= timeout:
                break

            captured_real = False
            if has_psutil:
                try:
                    def is_real_internet(c):
                        if not c.laddr or not c.raddr:
                            return False
                        l_ip = c.laddr.ip
                        r_ip = c.raddr.ip
                        # Strictly filter out internal loopback and unspecified addresses
                        if l_ip in ("127.0.0.1", "::1", "::", "0.0.0.0", "localhost"):
                            return False
                        if r_ip in ("127.0.0.1", "::1", "::", "0.0.0.0", "localhost"):
                            return False
                        # Filter out internal dashboard & API ports
                        if c.laddr.port in (8000, 3000) or c.raddr.port in (8000, 3000):
                            return False
                        # Filter out Cloud container mesh / CGNAT (100.64.0.0/10, Railway internal network)
                        if r_ip.startswith(("100.64.", "100.65.", "100.66.", "100.67.", "100.68.", "100.69.", "100.7", "100.8", "100.9", "100.1")):
                            return False
                        if l_ip.startswith("10.") and r_ip.startswith(("10.", "100.")):
                            return False
                        return True

                    active_conns = [c for c in psutil.net_connections(kind="inet") if is_real_internet(c)]
                    user_conns = []
                    other_conns = []

                    for c in active_conns:
                        try:
                            pname = psutil.Process(c.pid).name() if c.pid else "System"
                        except Exception:
                            pname = "System"
                        # Filter out server processes and background noise
                        if any(ign in pname.lower() for ign in IGNORED_SYSTEM_NOISE):
                            continue
                        if any(u in pname.lower() for u in USER_APPS):
                            user_conns.append((pname, c))
                        else:
                            other_conns.append((pname, c))

                    # Prioritize active user applications (Brave, Chrome, Edge, YouTube) over background daemons
                    candidates = user_conns if user_conns else other_conns
                    valid_candidates = [
                        (pname, c) for pname, c in candidates
                        if not any(ign in pname.lower() for ign in ["python", "uvicorn", "gunicorn", "node", "system", "host"])
                    ]

                    if valid_candidates:
                        sampled = random.sample(valid_candidates, min(3, len(valid_candidates)))
                        for pname, c in sampled:
                            proto = "TCP" if c.type == py_socket.SOCK_STREAM else "UDP"
                            local_ip = c.laddr.ip if c.laddr.ip not in ("0.0.0.0", "::") else "192.168.0.194"
                            src_ip = f"{local_ip} [{pname}]"
                            site_tag = resolve_service_name(c.raddr.ip, c.raddr.port, pname)
                            dst_ip = f"{site_tag} ({c.raddr.ip})"
                            sport = c.laddr.port
                            dport = c.raddr.port
                            pkt = SyntheticPacket(
                                src_ip=src_ip,
                                dst_ip=dst_ip,
                                proto=proto,
                                sport=sport,
                                dport=dport,
                                length=random.randint(64, 1460)
                            )
                            callback(pkt)
                            captured_real = True
                except Exception as e:
                    logger.debug("psutil connection capture error: %s", e)

            if not captured_real:
                # No active user sockets captured in this interval; pause briefly
                time.sleep(0.5)
            else:
                time.sleep(random.uniform(0.1, 0.3))

    def stop_capture(self) -> None:
        """Stops the active capture session."""
        self.is_capturing = False
        logger.info("Signaled packet capture to stop.")
