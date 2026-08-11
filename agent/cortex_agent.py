"""
CortexAgent Desktop Application Engine.
Provides a GUI for Live Network Sniffing (Mode 1) and Threat Validation Lab (Mode 2).
Reuses production LiveMonitor, PacketCapturer, FlowBuilder, and PredictionService.
"""
import json
import logging
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Production Imports (REUSING EXISTING CODEBASE)
from src.packet_capture import list_network_interfaces, PacketCapturer
from src.flow_builder import FlowBuilder
from src.prediction_service import PredictionService
from src.alert_engine import AlertEngine
from scripts.simulate_live_attacks import ATTACK_PROFILES

logger = logging.getLogger("CortexAgent")


class CortexAgentGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Cortex NIDS - Desktop Monitoring & Threat Validation Platform")
        self.root.geometry("980x740")
        self.root.minsize(900, 680)
        self.root.configure(bg="#04070E")

        # Telemetry Counters
        self.flows_captured = 0
        self.predictions_made = 0
        self.threats_detected = 0
        self.total_confidence_sum = 0.0
        self.last_detection_str = "None"
        self.backend_online = False

        # Mode States
        self.monitoring_active = False
        self.simulation_active = False

        # Threads
        self.monitor_thread = None
        self.flush_thread = None
        self.sim_thread = None

        # Components
        self.target_api_url = tk.StringVar(value="https://web-production-31259.up.railway.app")
        self.selected_interface = tk.StringVar()
        self.selected_profile = tk.StringVar(value="Balanced Mix (70% Benign, 30% Attack)")
        self.sim_interval = tk.DoubleVar(value=0.5)

        # Initialize Production ML Engines
        self.prediction_service = None
        self.alert_engine = None
        self.capturer = None
        self.flow_builder = None

        self._init_production_engines()
        self._build_ui()
        self._check_backend_health()

    def _init_production_engines(self):
        try:
            db_dir = PROJECT_ROOT / "predictions"
            db_dir.mkdir(exist_ok=True)
            self.alert_engine = AlertEngine(db_dir=db_dir)
            self.prediction_service = PredictionService(output_dir=db_dir)
            self.flow_builder = FlowBuilder(idle_timeout_sec=2.0)
        except Exception as e:
            logger.error(f"Error initializing production ML engines: {e}")

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Custom Styling Colors
        bg_dark = "#04070E"
        card_bg = "#0B1220"
        border_color = "#1E2C42"
        text_white = "#F8FAFC"
        accent_blue = "#3B82F6"
        accent_cyan = "#06B6D4"
        accent_green = "#10B981"
        accent_red = "#F43F5E"
        accent_orange = "#F59E0B"

        style.configure("TFrame", background=bg_dark)
        style.configure("Card.TFrame", background=card_bg, relief="flat")
        style.configure("TLabel", background=bg_dark, foreground=text_white, font=("Inter", 10))
        style.configure("Card.TLabel", background=card_bg, foreground=text_white, font=("Inter", 10))
        style.configure("Title.TLabel", background=bg_dark, foreground=text_white, font=("Inter", 14, "bold"))
        style.configure("Header.TLabel", background=card_bg, foreground=accent_cyan, font=("Inter", 11, "bold"))
        style.configure("StatNum.TLabel", background=card_bg, foreground=accent_cyan, font=("JetBrains Mono", 18, "bold"))
        style.configure("StatLabel.TLabel", background=card_bg, foreground="#94A3B8", font=("Inter", 9))

        # Main Container
        main_container = ttk.Frame(self.root, padding=16)
        main_container.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # TOP HEADER BAR
        # -------------------------------------------------------------
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        title_lbl = ttk.Label(header_frame, text="🛡️ CORTEX NIDS AGENT v2.0", style="Title.TLabel")
        title_lbl.pack(side=tk.LEFT)

        self.backend_status_lbl = tk.Label(
            header_frame,
            text="CHECKING BACKEND...",
            bg="#1E2C42",
            fg="#F59E0B",
            font=("JetBrains Mono", 9, "bold"),
            px=10,
            py=4
        )
        self.backend_status_lbl.pack(side=tk.RIGHT)

        # Target API Entry Bar
        api_bar = ttk.Frame(main_container)
        api_bar.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(api_bar, text="Target API Endpoint:", font=("Inter", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        api_entry = tk.Entry(
            api_bar,
            textvariable=self.target_api_url,
            bg="#0B1220",
            fg="#38BDF8",
            insertbackground="white",
            relief="solid",
            bd=1,
            font=("JetBrains Mono", 9)
        )
        api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_check = tk.Button(
            api_bar,
            text="Test Health",
            command=self._check_backend_health,
            bg="#1E2C42",
            fg="white",
            activebackground="#3B82F6",
            activeforeground="white",
            relief="flat",
            font=("Inter", 9, "bold"),
            px=12,
            py=2
        )
        btn_check.pack(side=tk.RIGHT)

        # -------------------------------------------------------------
        # CONTROL PANELS (MODE 1 & MODE 2)
        # -------------------------------------------------------------
        controls_frame = ttk.Frame(main_container)
        controls_frame.pack(fill=tk.X, pady=(0, 12))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)

        # MODE 1: LIVE MONITORING CARD
        mode1_card = tk.Frame(controls_frame, bg=card_bg, highlightbackground=border_color, highlightthickness=1, bd=0)
        mode1_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        m1_head = tk.Label(mode1_card, text="📡 MODE 1: LIVE PACKET MONITORING", bg=card_bg, fg=accent_cyan, font=("Inter", 10, "bold"))
        m1_head.pack(anchor="w", padx=12, pady=(10, 6))

        m1_sub = tk.Label(mode1_card, text="Sniffs real network packets (Wi-Fi/Ethernet) & executes ML threat classification.", bg=card_bg, fg="#94A3B8", font=("Inter", 8))
        m1_sub.pack(anchor="w", padx=12, pady=(0, 8))

        # Interface Selector
        iface_frame = tk.Frame(mode1_card, bg=card_bg)
        iface_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Label(iface_frame, text="Interface:", bg=card_bg, fg="#CBD5E1", font=("Inter", 9)).pack(side=tk.LEFT, padx=(0, 6))

        interfaces = self._get_interface_list()
        self.iface_combo = ttk.Combobox(iface_frame, textvariable=self.selected_interface, values=interfaces, state="readonly", font=("Inter", 8))
        if interfaces:
            self.iface_combo.current(0)
        self.iface_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        m1_btn_frame = tk.Frame(mode1_card, bg=card_bg)
        m1_btn_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.btn_start_mon = tk.Button(
            m1_btn_frame,
            text="▶ Start Monitoring",
            command=self.start_monitoring,
            bg=accent_green,
            fg="white",
            font=("Inter", 9, "bold"),
            relief="flat",
            px=12,
            py=4
        )
        self.btn_start_mon.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stop_mon = tk.Button(
            m1_btn_frame,
            text="⏹ Stop Monitoring",
            command=self.stop_monitoring,
            bg="#334155",
            fg="white",
            state=tk.DISABLED,
            font=("Inter", 9, "bold"),
            relief="flat",
            px=12,
            py=4
        )
        self.btn_stop_mon.pack(side=tk.LEFT)

        self.mon_status_lbl = tk.Label(m1_btn_frame, text="IDLE", bg=card_bg, fg="#64748B", font=("JetBrains Mono", 9, "bold"))
        self.mon_status_lbl.pack(side=tk.RIGHT)

        # MODE 2: THREAT VALIDATION LAB CARD
        mode2_card = tk.Frame(controls_frame, bg=card_bg, highlightbackground=border_color, highlightthickness=1, bd=0)
        mode2_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        m2_head = tk.Label(mode2_card, text="⚡ MODE 2: THREAT VALIDATION LAB", bg=card_bg, fg=accent_orange, font=("Inter", 10, "bold"))
        m2_head.pack(anchor="w", padx=12, pady=(10, 6))

        m2_sub = tk.Label(mode2_card, text="Generates realistic attack traffic flows (DoS, DDoS, PortScan) through ML pipeline.", bg=card_bg, fg="#94A3B8", font=("Inter", 8))
        m2_sub.pack(anchor="w", padx=12, pady=(0, 8))

        # Profile Selector
        prof_frame = tk.Frame(mode2_card, bg=card_bg)
        prof_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Label(prof_frame, text="Attack Profile:", bg=card_bg, fg="#CBD5E1", font=("Inter", 9)).pack(side=tk.LEFT, padx=(0, 6))

        profiles = [
            "Balanced Mix (70% Benign, 30% Attack)",
            "DoS GoldenEye Attack Flood",
            "DDoS Attack Vector",
            "PortScan Reconnaissance"
        ]
        self.prof_combo = ttk.Combobox(prof_frame, textvariable=self.selected_profile, values=profiles, state="readonly", font=("Inter", 8))
        self.prof_combo.current(0)
        self.prof_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        m2_btn_frame = tk.Frame(mode2_card, bg=card_bg)
        m2_btn_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.btn_start_sim = tk.Button(
            m2_btn_frame,
            text="⚡ Start Simulation",
            command=self.start_simulation,
            bg=accent_orange,
            fg="white",
            font=("Inter", 9, "bold"),
            relief="flat",
            px=12,
            py=4
        )
        self.btn_start_sim.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stop_sim = tk.Button(
            m2_btn_frame,
            text="⏹ Stop Simulation",
            command=self.stop_simulation,
            bg="#334155",
            fg="white",
            state=tk.DISABLED,
            font=("Inter", 9, "bold"),
            relief="flat",
            px=12,
            py=4
        )
        self.btn_stop_sim.pack(side=tk.LEFT)

        self.sim_status_lbl = tk.Label(m2_btn_frame, text="IDLE", bg=card_bg, fg="#64748B", font=("JetBrains Mono", 9, "bold"))
        self.sim_status_lbl.pack(side=tk.RIGHT)

        # -------------------------------------------------------------
        # TELEMETRY STATISTICS GRID (5 STATS)
        # -------------------------------------------------------------
        stats_frame = ttk.Frame(main_container)
        stats_frame.pack(fill=tk.X, pady=(0, 12))
        for idx in range(5):
            stats_frame.columnconfigure(idx, weight=1)

        self.card_flows = self._create_stat_card(stats_frame, 0, "FLOWS CAPTURED", "0")
        self.card_preds = self._create_stat_card(stats_frame, 1, "PREDICTIONS MADE", "0")
        self.card_threats = self._create_stat_card(stats_frame, 2, "THREATS DETECTED", "0", fg_color=accent_red)
        self.card_conf = self._create_stat_card(stats_frame, 3, "AVG CONFIDENCE", "0.0%")
        self.card_last = self._create_stat_card(stats_frame, 4, "LAST DETECTION", "None", fg_color=accent_cyan)

        # -------------------------------------------------------------
        # EVENT LOG CONSOLE
        # -------------------------------------------------------------
        console_frame = tk.Frame(main_container, bg=card_bg, highlightbackground=border_color, highlightthickness=1)
        console_frame.pack(fill=tk.BOTH, expand=True)

        c_head = tk.Frame(console_frame, bg=card_bg)
        c_head.pack(fill=tk.X, padx=12, pady=6)
        tk.Label(c_head, text="💻 REAL-TIME SYSTEM & ML DETECTION CONSOLE LOG", bg=card_bg, fg=text_white, font=("Inter", 9, "bold")).pack(side=tk.LEFT)

        btn_clear = tk.Button(c_head, text="Clear Log", command=self._clear_log, bg="#1E2C42", fg="#94A3B8", relief="flat", font=("Inter", 8), px=8)
        btn_clear.pack(side=tk.RIGHT)

        self.log_text = scrolledtext.ScrolledText(
            console_frame,
            bg="#04070E",
            fg="#38BDF8",
            insertbackground="white",
            font=("JetBrains Mono", 9),
            bd=0,
            relief="flat"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Tag configurations for colorized logging
        self.log_text.tag_config("INFO", foreground="#38BDF8")
        self.log_text.tag_config("FLOW", foreground="#10B981")
        self.log_text.tag_config("THREAT", foreground="#F43F5E", font=("JetBrains Mono", 9, "bold"))
        self.log_text.tag_config("WARN", foreground="#F59E0B")
        self.log_text.tag_config("ERROR", foreground="#EF4444", font=("JetBrains Mono", 9, "bold"))

        self.log("INFO", "CortexAgent Desktop Engine initialized successfully. Production ML Pipeline active.")

    def _create_stat_card(self, parent, col, title, initial_val, fg_color="#06B6D4"):
        card = tk.Frame(parent, bg="#0B1220", highlightbackground="#1E2C42", highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=3)

        tk.Label(card, text=title, bg="#0B1220", fg="#94A3B8", font=("Inter", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        lbl_val = tk.Label(card, text=initial_val, bg="#0B1220", fg=fg_color, font=("JetBrains Mono", 14, "bold"))
        lbl_val.pack(anchor="w", padx=8, pady=(0, 6))
        return lbl_val

    def _get_interface_list(self):
        try:
            ifaces = list_network_interfaces()
            names = [ifc.get("name", "Default Interface") for ifc in ifaces]
            return names if names else ["Default Interface"]
        except Exception:
            return ["Default Interface"]

    def log(self, level: str, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level:<7}] {msg}\n"

        def _append():
            self.log_text.insert(tk.END, formatted, level)
            self.log_text.see(tk.END)

        self.root.after(0, _append)

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _check_backend_health(self):
        def _check():
            url = f"{self.target_api_url.get().rstrip('/')}/health"
            try:
                req = urllib.request.urlopen(url, timeout=3.0)
                if req.getcode() == 200:
                    self.backend_online = True
                    self.root.after(0, lambda: self.backend_status_lbl.config(text="● ONLINE (RAILWAY)", bg="#065F46", fg="#34D399"))
                    self.log("INFO", f"Connected to Cloud Backend API: {url}")
                    return
            except Exception:
                pass
            self.backend_online = False
            self.root.after(0, lambda: self.backend_status_lbl.config(text="○ OFFLINE (LOCAL ML ONLY)", bg="#881337", fg="#FCA5A5"))
            self.log("WARN", f"Could not reach Backend API at {url}. Live alerts will run in local SQLite mode.")

        threading.Thread(target=_check, daemon=True).start()

    # -------------------------------------------------------------
    # MODE 1: LIVE PACKET MONITORING LOGIC
    # -------------------------------------------------------------
    def start_monitoring(self):
        if self.monitoring_active:
            return

        selected_iface = self.selected_interface.get()
        self.monitoring_active = True
        self.btn_start_mon.config(state=tk.DISABLED, bg="#334155")
        self.btn_stop_mon.config(state=tk.NORMAL, bg="#F43F5E")
        self.mon_status_lbl.config(text="RUNNING", fg="#10B981")

        self.log("INFO", f"Starting Mode 1: Live Network Packet Monitor on interface '{selected_iface}'...")

        self.capturer = PacketCapturer(interface=selected_iface if selected_iface != "Default Interface" else None, bpf_filter="ip")
        self.flow_builder = FlowBuilder(idle_timeout_sec=2.0)

        # 1. Packet Capture Thread
        self.monitor_thread = threading.Thread(
            target=self.capturer.start_capture,
            args=(self._on_packet_received,),
            daemon=True
        )
        self.monitor_thread.start()

        # 2. Flow Flush Loop Thread
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()

    def stop_monitoring(self):
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.capturer:
            self.capturer.stop_capture()

        self.btn_start_mon.config(state=tk.NORMAL, bg="#10B981")
        self.btn_stop_mon.config(state=tk.DISABLED, bg="#334155")
        self.mon_status_lbl.config(text="IDLE", fg="#64748B")

        self.log("WARN", "Stopped Mode 1: Live Network Packet Monitor.")

    def _on_packet_received(self, pkt):
        if not self.monitoring_active:
            return
        flow = self.flow_builder.process_packet(pkt)
        if flow:
            self._evaluate_and_post_flow(flow, is_live=True)

    def _flush_loop(self):
        while self.monitoring_active:
            time.sleep(1.0)
            expired = self.flow_builder.flush_expired_flows()
            for flow in expired:
                self._evaluate_and_post_flow(flow, is_live=True)

    # -------------------------------------------------------------
    # MODE 2: THREAT VALIDATION LAB LOGIC
    # -------------------------------------------------------------
    def start_simulation(self):
        if self.simulation_active:
            return

        self.simulation_active = True
        self.btn_start_sim.config(state=tk.DISABLED, bg="#334155")
        self.btn_stop_sim.config(state=tk.NORMAL, bg="#F43F5E")
        self.sim_status_lbl.config(text="RUNNING", fg="#F59E0B")

        profile_choice = self.selected_profile.get()
        self.log("INFO", f"Starting Mode 2: Threat Validation Lab ({profile_choice})...")

        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()

    def stop_simulation(self):
        if not self.simulation_active:
            return

        self.simulation_active = False
        self.btn_start_sim.config(state=tk.NORMAL, bg="#F59E0B")
        self.btn_stop_sim.config(state=tk.DISABLED, bg="#334155")
        self.sim_status_lbl.config(text="IDLE", fg="#64748B")

        self.log("WARN", "Stopped Mode 2: Threat Validation Lab.")

    def _simulation_loop(self):
        profile_choice = self.selected_profile.get()

        while self.simulation_active:
            # Pick profile based on user selection
            if "DoS" in profile_choice:
                prof = ATTACK_PROFILES[1]  # DoS GoldenEye
            elif "DDoS" in profile_choice:
                prof = ATTACK_PROFILES[2]  # DDoS
            elif "PortScan" in profile_choice:
                prof = ATTACK_PROFILES[3]  # PortScan
            else:
                # Balanced Mix
                r = random.random()
                if r < 0.70:
                    prof = ATTACK_PROFILES[0]
                elif r < 0.80:
                    prof = ATTACK_PROFILES[1]
                elif r < 0.90:
                    prof = ATTACK_PROFILES[2]
                else:
                    prof = ATTACK_PROFILES[3]

            src_ip = prof["src_ip"].format(random.randint(2, 250))
            dst_port = random.choice(prof["dst_port"])
            fwd_pkts = random.randint(*prof["fwd_pkts"])
            flow_bytes = random.randint(*prof["flow_bytes"])

            flow_feats = {
                "_src_ip": src_ip,
                "_dst_ip": "10.0.0.1",
                "_protocol": "TCP",
                "Destination Port": dst_port,
                "Total Length of Fwd Packets": flow_bytes,
                "Fwd Packet Length Max": random.randint(100, 1460),
                "Bwd Packet Length Max": random.randint(0, 1460),
                "Flow Bytes/s": random.randint(500, 50000),
                "Flow IAT Std": random.uniform(10, 500),
                "Fwd IAT Min": random.randint(1, 20),
                "Fwd Header Length": 40,
                "Bwd Header Length": 40,
                "Bwd Packets/s": random.randint(5, 50),
                "FIN Flag Count": 0,
                "PSH Flag Count": random.choice([0, 1]),
                "Init_Win_bytes_forward": 8192,
                "Init_Win_bytes_backward": 255,
                "act_data_pkt_fwd": max(1, fwd_pkts // 2),
                "min_seg_size_forward": 20,
                "Active Mean": 0,
                "Active Std": 0,
                "Active Max": 0,
                "Idle Std": 0
            }

            self._evaluate_and_post_flow(flow_feats, is_live=False)
            time.sleep(self.sim_interval.get())

    # -------------------------------------------------------------
    # SHARED PRODUCTION INFERENCE & TELEMETRY POSTING
    # -------------------------------------------------------------
    def _evaluate_and_post_flow(self, flow_feats: Dict[str, Any], is_live: bool = False):
        try:
            self.flows_captured += 1

            src_ip = flow_feats.pop("_src_ip", "192.168.1.100")
            dst_ip = flow_feats.pop("_dst_ip", "10.0.0.1")
            protocol = flow_feats.pop("_protocol", "TCP")
            dst_port = int(flow_feats.get("Destination Port", 80))

            # Clean private keys
            for k in list(flow_feats.keys()):
                if k.startswith("_"):
                    flow_feats.pop(k, None)

            # 1. Execute Production ML Inference
            pred_result = self.prediction_service.predictor.predict_single(flow_feats)
            self.predictions_made += 1

            attack_type = pred_result.get("Attack_Type", "BENIGN")
            risk_level = pred_result.get("Risk_Level", "Low")
            risk_score = float(pred_result.get("Risk_Score", 0.0))
            confidence = float(pred_result.get("Prediction_Confidence", 0.99))
            latency = float(pred_result.get("Prediction_Time_ms", 0.035))

            self.total_confidence_sum += confidence
            avg_conf = self.total_confidence_sum / max(1, self.predictions_made)

            # Update Counters if Threat
            if risk_level in ["High", "Critical"] or attack_type != "BENIGN":
                self.threats_detected += 1
                self.last_detection_str = f"{attack_type} ({risk_level})"
                self.log("THREAT", f"🚨 ALERT [{risk_level}]: {attack_type} | Risk: {risk_score:.1f}/100 | {src_ip} -> :{dst_port} | Latency: {latency:.2f}ms")
            else:
                self.log("FLOW", f"Flow [{src_ip} -> :{dst_port}] | Predict: {attack_type} | Confidence: {confidence*100:.1f}% | Latency: {latency:.2f}ms")

            # 2. Persist to Local SQLite (alerts.db)
            if self.alert_engine:
                self.alert_engine.process_prediction(
                    prediction_result=pred_result,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    protocol=protocol,
                    dst_port=dst_port
                )

            # 3. Post Telemetry Stream to Cloud Backend (Railway API)
            if self.backend_online:
                try:
                    payload = json.dumps({
                        "attack_type": attack_type,
                        "confidence": confidence,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "latency_ms": latency,
                        "count": 1
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        f"{self.target_api_url.get().rstrip('/')}/metrics/record",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=1.0)
                except Exception:
                    pass

            # 4. Update UI Telemetry Counters
            def _update_ui():
                self.card_flows.config(text=f"{self.flows_captured:,}")
                self.card_preds.config(text=f"{self.predictions_made:,}")
                self.card_threats.config(text=f"{self.threats_detected:,}")
                self.card_conf.config(text=f"{avg_conf * 100:.1f}%")
                self.card_last.config(text=self.last_detection_str[:18])

            self.root.after(0, _update_ui)

        except Exception as e:
            self.log("ERROR", f"Inference pipeline evaluation error: {e}")


def launch_cortex_agent():
    root = tk.Tk()
    app = CortexAgentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_cortex_agent()
