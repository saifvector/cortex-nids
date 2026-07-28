"""
Flow Builder module for NIDS.
Aggregates live network packets into bidirectional 5-tuple flows and extracts the exact 20 flow-based features.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FEATURE_NAMES_20 = [
    "Destination Port",
    "Total Length of Fwd Packets",
    "Fwd Packet Length Max",
    "Bwd Packet Length Max",
    "Flow Bytes/s",
    "Flow IAT Std",
    "Fwd IAT Min",
    "Fwd Header Length",
    "Bwd Header Length",
    "Bwd Packets/s",
    "FIN Flag Count",
    "PSH Flag Count",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
    "act_data_pkt_fwd",
    "min_seg_size_forward",
    "Active Mean",
    "Active Std",
    "Active Max",
    "Idle Std"
]


class NetworkFlow:
    """
    Bidirectional network flow tracker computing statistics for a 5-tuple conversation.
    """

    def __init__(self, key: Tuple[str, int, str, int, str], start_time: float):
        self.key = key  # (src_ip, src_port, dst_ip, dst_port, proto_name)
        self.src_ip, self.src_port, self.dst_ip, self.dst_port, self.protocol = key
        self.start_time = start_time
        self.last_seen = start_time

        self.fwd_packets = 0
        self.bwd_packets = 0
        self.fwd_bytes = 0
        self.bwd_bytes = 0

        self.fwd_pkt_lengths: List[int] = []
        self.bwd_pkt_lengths: List[int] = []

        self.fwd_iats: List[float] = []
        self.bwd_iats: List[float] = []
        self.all_iats: List[float] = []

        self.last_fwd_time: Optional[float] = None
        self.last_bwd_time: Optional[float] = None

        self.fwd_header_len = 0
        self.bwd_header_len = 0

        self.fin_flags = 0
        self.psh_flags = 0

        self.init_win_fwd = 0
        self.init_win_bwd = 0
        self.act_data_pkt_fwd = 0
        self.min_seg_size_fwd = 20

    def add_packet(self, pkt: Any, is_fwd: bool, pkt_time: float) -> None:
        duration_since_last = pkt_time - self.last_seen
        if duration_since_last > 0:
            self.all_iats.append(duration_since_last)

        self.last_seen = pkt_time
        pkt_len = len(pkt) if hasattr(pkt, "__len__") else 60

        # TCP Flag parsing
        if hasattr(pkt, "haslayer") and pkt.haslayer("TCP"):
            tcp_layer = pkt["TCP"]
            flags = str(tcp_layer.flags)
            if "F" in flags:
                self.fin_flags += 1
            if "P" in flags:
                self.psh_flags += 1

            window = getattr(tcp_layer, "window", 8192)
            hdr_len = getattr(tcp_layer, "dataofs", 5) * 4
        else:
            window = 0
            hdr_len = 20

        if is_fwd:
            self.fwd_packets += 1
            self.fwd_bytes += pkt_len
            self.fwd_pkt_lengths.append(pkt_len)
            self.fwd_header_len += hdr_len

            if self.last_fwd_time is not None:
                self.fwd_iats.append(pkt_time - self.last_fwd_time)
            self.last_fwd_time = pkt_time

            if self.fwd_packets == 1:
                self.init_win_fwd = window

            payload_len = pkt_len - (20 + hdr_len)
            if payload_len > 0:
                self.act_data_pkt_fwd += 1

            self.min_seg_size_fwd = min(self.min_seg_size_fwd, hdr_len)
        else:
            self.bwd_packets += 1
            self.bwd_bytes += pkt_len
            self.bwd_pkt_lengths.append(pkt_len)
            self.bwd_header_len += hdr_len

            if self.last_bwd_time is not None:
                self.bwd_iats.append(pkt_time - self.last_bwd_time)
            self.last_bwd_time = pkt_time

            if self.bwd_packets == 1:
                self.init_win_bwd = window

    def extract_features(self) -> Dict[str, Any]:
        duration_sec = max(0.001, self.last_seen - self.start_time)
        total_bytes = self.fwd_bytes + self.bwd_bytes
        total_packets = self.fwd_packets + self.bwd_packets

        flow_bytes_s = total_bytes / duration_sec
        bwd_pkts_s = self.bwd_packets / duration_sec

        flow_iat_std = float(np.std(self.all_iats)) if self.all_iats else 0.0
        fwd_iat_min = float(np.min(self.fwd_iats)) if self.fwd_iats else 0.0

        fwd_max = float(np.max(self.fwd_pkt_lengths)) if self.fwd_pkt_lengths else 0.0
        bwd_max = float(np.max(self.bwd_pkt_lengths)) if self.bwd_pkt_lengths else 0.0

        return {
            "Destination Port": float(self.dst_port),
            "Total Length of Fwd Packets": float(self.fwd_bytes),
            "Fwd Packet Length Max": fwd_max,
            "Bwd Packet Length Max": bwd_max,
            "Flow Bytes/s": float(flow_bytes_s),
            "Flow IAT Std": flow_iat_std,
            "Fwd IAT Min": fwd_iat_min,
            "Fwd Header Length": float(self.fwd_header_len),
            "Bwd Header Length": float(self.bwd_header_len),
            "Bwd Packets/s": float(bwd_pkts_s),
            "FIN Flag Count": float(self.fin_flags),
            "PSH Flag Count": float(self.psh_flags),
            "Init_Win_bytes_forward": float(self.init_win_fwd),
            "Init_Win_bytes_backward": float(self.init_win_bwd),
            "act_data_pkt_fwd": float(self.act_data_pkt_fwd),
            "min_seg_size_forward": float(self.min_seg_size_fwd),
            "Active Mean": 0.0,
            "Active Std": 0.0,
            "Active Max": 0.0,
            "Idle Std": 0.0,

            # Metadata properties for alert engine
            "_src_ip": self.src_ip,
            "_dst_ip": self.dst_ip,
            "_protocol": self.protocol,
            "_start_time": self.start_time,
            "_last_seen": self.last_seen
        }


class FlowBuilder:
    """
    Manages active network flows and extracts feature DataFrames upon flow timeouts.
    """

    def __init__(self, idle_timeout_sec: float = 2.0, active_timeout_sec: float = 10.0):
        self.idle_timeout = idle_timeout_sec
        self.active_timeout = active_timeout_sec
        self.active_flows: Dict[Tuple[str, int, str, int, str], NetworkFlow] = {}

    def process_packet(self, pkt: Any) -> Optional[Dict[str, Any]]:
        """
        Processes a single Scapy packet and updates its corresponding flow.

        Returns:
            Extracted feature dict if flow has completed, otherwise None.
        """
        if not hasattr(pkt, "haslayer") or not pkt.haslayer("IP"):
            return None

        ip_layer = pkt["IP"]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst

        if pkt.haslayer("TCP"):
            proto = "TCP"
            src_port = pkt["TCP"].sport
            dst_port = pkt["TCP"].dport
        elif pkt.haslayer("UDP"):
            proto = "UDP"
            src_port = pkt["UDP"].sport
            dst_port = pkt["UDP"].dport
        elif pkt.haslayer("ICMP"):
            proto = "ICMP"
            src_port = 0
            dst_port = 0
        else:
            proto = "IP"
            src_port = 0
            dst_port = 0

        now = time.time()
        fwd_key = (src_ip, src_port, dst_ip, dst_port, proto)
        bwd_key = (dst_ip, dst_port, src_ip, src_port, proto)

        if fwd_key in self.active_flows:
            flow = self.active_flows[fwd_key]
            flow.add_packet(pkt, is_fwd=True, pkt_time=now)
        elif bwd_key in self.active_flows:
            flow = self.active_flows[bwd_key]
            flow.add_packet(pkt, is_fwd=False, pkt_time=now)
        else:
            flow = NetworkFlow(fwd_key, start_time=now)
            flow.add_packet(pkt, is_fwd=True, pkt_time=now)
            self.active_flows[fwd_key] = flow

        # Check for flow expiration
        if (now - flow.start_time) > self.active_timeout:
            expired_flow = self.active_flows.pop(fwd_key if fwd_key in self.active_flows else bwd_key)
            return expired_flow.extract_features()

        return None

    def flush_expired_flows(self, force_all: bool = False) -> List[Dict[str, Any]]:
        """
        Flushes idle or force-completed flows and returns extracted feature dicts.
        """
        now = time.time()
        flushed_features = []
        keys_to_remove = []

        for key, flow in self.active_flows.items():
            if force_all or (now - flow.last_seen) > self.idle_timeout:
                flushed_features.append(flow.extract_features())
                keys_to_remove.append(key)

        for k in keys_to_remove:
            self.active_flows.pop(k, None)

        return flushed_features
