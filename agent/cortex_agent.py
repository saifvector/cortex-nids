"""
CortexAgent Desktop Application Engine — Premium SOC Dashboard.
Provides a modern CustomTkinter GUI for Live Network Sniffing (Mode 1)
and Threat Validation Lab (Mode 2).
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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import customtkinter as ctk

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

# ─────────────────────────────────────────────────
# COLOR PALETTE — Enterprise SOC Dark Theme
# ─────────────────────────────────────────────────
BG_DARK      = "#0A0E17"
BG_SIDEBAR   = "#0D1117"
BG_CARD      = "#111827"
BG_CARD_ALT  = "#151D2E"
BG_INPUT     = "#1A2332"
BORDER       = "#1E2C42"
BORDER_LIGHT = "#2A3A54"

TEXT_WHITE   = "#F0F4F8"
TEXT_MUTED   = "#8899A6"
TEXT_DIM     = "#5C6B7D"

CYAN         = "#06B6D4"
CYAN_DARK    = "#0891B2"
GREEN        = "#10B981"
GREEN_DARK   = "#059669"
RED          = "#EF4444"
RED_DARK     = "#DC2626"
ORANGE       = "#F59E0B"
ORANGE_DARK  = "#D97706"
BLUE         = "#3B82F6"
PURPLE       = "#8B5CF6"
PINK         = "#EC4899"


class CortexAgentGUI(ctk.CTk):
    """Premium SOC-style desktop application for Cortex NIDS."""

    def __init__(self):
        super().__init__()

        # ── Window Configuration ──
        self.title("CortexAgent — Enterprise Network Threat Detection")
        self.geometry("1200x780")
        self.minsize(1050, 700)
        self.configure(fg_color=BG_DARK)

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # ── Telemetry Counters ──
        self.flows_captured = 0
        self.predictions_made = 0
        self.threats_detected = 0
        self.total_confidence_sum = 0.0
        self.last_detection_str = "—"
        self.backend_online = False

        # ── Mode States ──
        self.monitoring_active = False
        self.simulation_active = False

        # ── Threads ──
        self.monitor_thread = None
        self.flush_thread = None
        self.sim_thread = None

        # ── Components ──
        self.target_api_url = "https://web-production-31259.up.railway.app"
        self.selected_interface = ""
        self.selected_profile = "Balanced Mix"
        self.sim_interval = 0.5

        # ── Production ML Engines ──
        self.prediction_service = None
        self.alert_engine = None
        self.capturer = None
        self.flow_builder = None

        self._init_production_engines()

        # ── Navigation State ──
        self.current_page = "dashboard"
        self.nav_buttons = {}
        self.pages = {}

        # ── Build UI ──
        self._build_layout()
        self._check_backend_health()

        # ── Start clock update ──
        self._update_clock()

    # ═══════════════════════════════════════════════
    #  PRODUCTION ML ENGINE INITIALIZATION
    # ═══════════════════════════════════════════════
    def _init_production_engines(self):
        self._init_error = None
        try:
            # For WRITABLE outputs (SQLite, predictions), use the EXE's directory,
            # NOT sys._MEIPASS (which is a read-only temp extraction dir).
            # Model files are READ from sys._MEIPASS automatically via ModelLoader/constants.py.
            if getattr(sys, 'frozen', False):
                exe_dir = Path(sys.executable).parent
                db_dir = exe_dir / "predictions"
            else:
                db_dir = PROJECT_ROOT / "predictions"

            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Writable output directory: %s", db_dir)

            self.alert_engine = AlertEngine(db_dir=db_dir)
            logger.info("AlertEngine ready: SQLite at %s", self.alert_engine.sqlite_path)

            self.prediction_service = PredictionService(output_dir=db_dir)
            logger.info("PredictionService initialized: model=%s, features=%d",
                        self.prediction_service.model_name,
                        len(self.prediction_service.feature_names))
            logger.info("Predictor ready: %s", type(self.prediction_service.predictor).__name__)

            self.flow_builder = FlowBuilder(idle_timeout_sec=2.0)
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"Error initializing production ML engines: {e}", exc_info=True)

    # ═══════════════════════════════════════════════
    #  MAIN LAYOUT BUILDER
    # ═══════════════════════════════════════════════
    def _build_layout(self):
        # Grid: sidebar (col 0, fixed width) | content (col 1, expand)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

    # ═══════════════════════════════════════════════
    #  LEFT SIDEBAR
    # ═══════════════════════════════════════════════
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=BG_SIDEBAR,
                               border_width=1, border_color=BORDER)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # ── LOGO / BRAND ──
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 6))

        ctk.CTkLabel(brand_frame, text="🛡️", font=ctk.CTkFont(size=28)).pack(side="left", padx=(0, 8))
        brand_text = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text.pack(side="left")
        ctk.CTkLabel(brand_text, text="CORTEX", font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
                     text_color=CYAN).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="NIDS Agent", font=ctk.CTkFont(family="Inter", size=10),
                     text_color=TEXT_MUTED).pack(anchor="w")

        # Separator
        ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(16, 12))

        # ── NAVIGATION BUTTONS ──
        nav_items = [
            ("dashboard",  "📊", "Dashboard"),
            ("monitoring", "📡", "Monitoring"),
            ("threatlab",  "⚡", "Threat Lab"),
            ("logs",       "📋", "Detection Logs"),
            ("settings",   "⚙️", "Settings"),
            ("about",      "ℹ️", "About"),
        ]

        for page_id, icon, label in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                font=ctk.CTkFont(family="Inter", size=13),
                height=40,
                corner_radius=8,
                fg_color=BG_CARD if page_id == "dashboard" else "transparent",
                hover_color=BG_CARD_ALT,
                text_color=TEXT_WHITE if page_id == "dashboard" else TEXT_MUTED,
                command=lambda p=page_id: self._navigate(p)
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[page_id] = btn

        # ── BOTTOM STATUS ──
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Backend status indicator
        self.backend_badge = ctk.CTkLabel(
            sidebar,
            text="  ○  CHECKING...",
            font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
            text_color=ORANGE,
            anchor="w"
        )
        self.backend_badge.pack(fill="x", padx=20, pady=(0, 4))

        # Engine status
        engine_status = "ML Engine: Active" if self.prediction_service else "ML Engine: FAILED"
        engine_color = GREEN if self.prediction_service else RED
        ctk.CTkLabel(
            sidebar,
            text=f"  ● {engine_status}",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=engine_color,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            sidebar,
            text="  v2.0.0  •  LightGBM",
            font=ctk.CTkFont(family="JetBrains Mono", size=9),
            text_color=TEXT_DIM,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 16))

    # ═══════════════════════════════════════════════
    #  CONTENT AREA (RIGHT SIDE)
    # ═══════════════════════════════════════════════
    def _build_content_area(self):
        # Main content frame
        self.content_frame = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)

        # ── TOP HEADER BAR ──
        header = ctk.CTkFrame(self.content_frame, height=50, fg_color=BG_SIDEBAR,
                              corner_radius=0, border_width=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        self.page_title_lbl = ctk.CTkLabel(
            header, text="📊  DASHBOARD",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=TEXT_WHITE
        )
        self.page_title_lbl.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        self.clock_lbl = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=TEXT_MUTED
        )
        self.clock_lbl.grid(row=0, column=2, padx=20, pady=12, sticky="e")

        # ── PAGE CONTAINER ──
        self.page_container = ctk.CTkFrame(self.content_frame, fg_color=BG_DARK, corner_radius=0)
        self.page_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.page_container.grid_columnconfigure(0, weight=1)
        self.page_container.grid_rowconfigure(0, weight=1)

        # Build all pages
        self._build_dashboard_page()
        self._build_monitoring_page()
        self._build_threatlab_page()
        self._build_logs_page()
        self._build_settings_page()
        self._build_about_page()

        # Show dashboard by default
        self._navigate("dashboard")

    # ═══════════════════════════════════════════════
    #  NAVIGATION
    # ═══════════════════════════════════════════════
    def _navigate(self, page_id: str):
        # Hide all pages
        for pid, frame in self.pages.items():
            frame.grid_forget()

        # Update nav button styles
        icon_map = {
            "dashboard": "📊", "monitoring": "📡", "threatlab": "⚡",
            "logs": "📋", "settings": "⚙️", "about": "ℹ️"
        }
        title_map = {
            "dashboard": "DASHBOARD", "monitoring": "LIVE MONITORING",
            "threatlab": "THREAT VALIDATION LAB", "logs": "DETECTION LOGS",
            "settings": "SETTINGS", "about": "ABOUT"
        }

        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(fg_color=BG_CARD, text_color=TEXT_WHITE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

        # Show selected page
        if page_id in self.pages:
            self.pages[page_id].grid(row=0, column=0, sticky="nsew")

        self.page_title_lbl.configure(text=f"{icon_map.get(page_id, '')}  {title_map.get(page_id, page_id.upper())}")
        self.current_page = page_id

    # ═══════════════════════════════════════════════
    #  PAGE: DASHBOARD
    # ═══════════════════════════════════════════════
    def _build_dashboard_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color=BG_DARK)
        self.pages["dashboard"] = page

        # Scrollable area
        scroll = ctk.CTkScrollableFrame(page, fg_color=BG_DARK, scrollbar_button_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)
        scroll.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # ── STAT CARDS ROW ──
        self.stat_cards = {}
        stats_def = [
            ("flows",   "FLOWS CAPTURED",    "0",    CYAN,   "📦"),
            ("preds",   "PREDICTIONS MADE",  "0",    BLUE,   "🧠"),
            ("threats", "THREATS DETECTED",  "0",    RED,    "🚨"),
            ("conf",    "AVG CONFIDENCE",    "0.0%", GREEN,  "📈"),
            ("last",    "LAST DETECTION",    "—",    ORANGE, "🎯"),
        ]

        for col, (key, title, initial, color, icon) in enumerate(stats_def):
            card = self._make_stat_card(scroll, icon, title, initial, color)
            card.grid(row=0, column=col, sticky="nsew", padx=4, pady=(0, 12))
            self.stat_cards[key] = card

        # ── QUICK ACTIONS ROW ──
        actions_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                                     border_width=1, border_color=BORDER)
        actions_frame.grid(row=1, column=0, columnspan=5, sticky="ew", padx=4, pady=(0, 12))

        ctk.CTkLabel(actions_frame, text="QUICK ACTIONS",
                     font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 8))

        btn_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        self.dash_mon_btn = ctk.CTkButton(
            btn_row, text="📡  Start Monitoring", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=GREEN_DARK, hover_color=GREEN, height=38, corner_radius=8,
            command=self.start_monitoring
        )
        self.dash_mon_btn.pack(side="left", padx=(0, 8))

        self.dash_sim_btn = ctk.CTkButton(
            btn_row, text="⚡  Start Simulation", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ORANGE_DARK, hover_color=ORANGE, height=38, corner_radius=8,
            command=self.start_simulation
        )
        self.dash_sim_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="🔄  Reset Counters", font=ctk.CTkFont(size=12),
            fg_color=BG_INPUT, hover_color=BORDER_LIGHT, height=38, corner_radius=8,
            command=self._reset_counters
        ).pack(side="left")

        # ── LIVE CONSOLE LOG ──
        console_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                                    border_width=1, border_color=BORDER)
        console_card.grid(row=2, column=0, columnspan=5, sticky="nsew", padx=4, pady=(0, 4))
        scroll.grid_rowconfigure(2, weight=1)

        console_header = ctk.CTkFrame(console_card, fg_color="transparent")
        console_header.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(console_header, text="💻  REAL-TIME DETECTION CONSOLE",
                     font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                     text_color=TEXT_WHITE).pack(side="left")

        ctk.CTkButton(
            console_header, text="Clear", width=60, height=26, corner_radius=6,
            fg_color=BG_INPUT, hover_color=BORDER_LIGHT,
            font=ctk.CTkFont(size=11), command=self._clear_log
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            console_card,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color="#050810",
            text_color=CYAN,
            corner_radius=6,
            height=250,
            border_width=1,
            border_color=BORDER
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Configure log tags
        self.log_text.tag_config("INFO", foreground=CYAN)
        self.log_text.tag_config("FLOW", foreground=GREEN)
        self.log_text.tag_config("THREAT", foreground=RED)
        self.log_text.tag_config("WARN", foreground=ORANGE)
        self.log_text.tag_config("ERROR", foreground="#FF6B6B")
        self.log_text.tag_config("SUCCESS", foreground=GREEN)

        self.log("INFO", "CortexAgent v2.0 initialized. Production LightGBM pipeline active.")
        if self.prediction_service:
            self.log("SUCCESS", f"ML Model: {self.prediction_service.model_name} | "
                     f"Features: {len(self.prediction_service.feature_names)} | Predictor: Ready")
        else:
            err = getattr(self, '_init_error', 'Unknown error')
            self.log("ERROR", f"ML PredictionService failed to initialize: {err}")

    def _make_stat_card(self, parent, icon: str, title: str, value: str, color: str):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                            border_width=1, border_color=BORDER)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        # Icon + Title row
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=16)).pack(side="left")
        ctk.CTkLabel(top, text=title,
                     font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(6, 0))

        # Value
        val_lbl = ctk.CTkLabel(inner, text=value,
                               font=ctk.CTkFont(family="JetBrains Mono", size=22, weight="bold"),
                               text_color=color)
        val_lbl.pack(anchor="w", pady=(6, 0))

        card._value_label = val_lbl
        return card

    # ═══════════════════════════════════════════════
    #  PAGE: MONITORING
    # ═══════════════════════════════════════════════
    def _build_monitoring_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color=BG_DARK)
        self.pages["monitoring"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color=BG_DARK, scrollbar_button_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Control Card ──
        ctrl_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                                 border_width=1, border_color=BORDER)
        ctrl_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(ctrl_card, text="📡  LIVE PACKET MONITORING",
                     font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                     text_color=CYAN).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(ctrl_card, text="Captures real network packets via Wi-Fi/Ethernet and classifies threats using LightGBM ML pipeline.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
                     wraplength=700).pack(anchor="w", padx=20, pady=(0, 12))

        # Interface selector
        iface_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        iface_row.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(iface_row, text="Network Interface:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))

        interfaces = self._get_interface_list()
        self.iface_menu = ctk.CTkOptionMenu(
            iface_row, values=interfaces,
            font=ctk.CTkFont(size=11),
            fg_color=BG_INPUT, button_color=BORDER_LIGHT,
            dropdown_fg_color=BG_CARD,
            width=350, height=32,
            command=self._on_interface_change
        )
        self.iface_menu.pack(side="left")
        if interfaces:
            self.selected_interface = interfaces[0]

        # Buttons
        btn_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        self.mon_start_btn = ctk.CTkButton(
            btn_row, text="▶  Start Monitoring",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=GREEN_DARK, hover_color=GREEN,
            height=40, corner_radius=8, width=180,
            command=self.start_monitoring
        )
        self.mon_start_btn.pack(side="left", padx=(0, 8))

        self.mon_stop_btn = ctk.CTkButton(
            btn_row, text="⏹  Stop Monitoring",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=BG_INPUT, hover_color=RED_DARK,
            height=40, corner_radius=8, width=180,
            state="disabled",
            command=self.stop_monitoring
        )
        self.mon_stop_btn.pack(side="left", padx=(0, 16))

        self.mon_status_badge = ctk.CTkLabel(
            btn_row, text="● IDLE",
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            text_color=TEXT_DIM
        )
        self.mon_status_badge.pack(side="left")

        # ── Live Stats ──
        stats_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                                  border_width=1, border_color=BORDER)
        stats_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(stats_card, text="MONITORING SESSION STATS",
                     font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(14, 10))

        mon_stats_row = ctk.CTkFrame(stats_card, fg_color="transparent")
        mon_stats_row.pack(fill="x", padx=20, pady=(0, 16))
        mon_stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.mon_stat_lbls = {}
        for col, (key, title, color) in enumerate([
            ("packets", "Packets Seen", CYAN),
            ("flows", "Flows Built", BLUE),
            ("preds", "ML Predictions", GREEN),
            ("threats", "Threats Found", RED)
        ]):
            f = ctk.CTkFrame(mon_stats_row, fg_color=BG_CARD_ALT, corner_radius=8)
            f.grid(row=0, column=col, sticky="ew", padx=4)
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=TEXT_MUTED).pack(padx=12, pady=(8, 2))
            lbl = ctk.CTkLabel(f, text="0", font=ctk.CTkFont(family="JetBrains Mono", size=20, weight="bold"),
                               text_color=color)
            lbl.pack(padx=12, pady=(0, 8))
            self.mon_stat_lbls[key] = lbl

    # ═══════════════════════════════════════════════
    #  PAGE: THREAT LAB
    # ═══════════════════════════════════════════════
    def _build_threatlab_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color=BG_DARK)
        self.pages["threatlab"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color=BG_DARK, scrollbar_button_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Header ──
        header_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                                   border_width=1, border_color=BORDER)
        header_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(header_card, text="⚡  THREAT VALIDATION LABORATORY",
                     font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                     text_color=ORANGE).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(header_card, text="Generates realistic synthetic attack traffic flows and classifies them through the production ML pipeline to validate detection accuracy.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
                     wraplength=700).pack(anchor="w", padx=20, pady=(0, 12))

        # Controls row
        ctrl_row = ctk.CTkFrame(header_card, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=20, pady=(0, 16))

        # Profile selector
        ctk.CTkLabel(ctrl_row, text="Attack Profile:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))

        profiles = [
            "Balanced Mix",
            "DoS GoldenEye Flood",
            "DDoS Attack Vector",
            "PortScan Recon"
        ]
        self.profile_menu = ctk.CTkOptionMenu(
            ctrl_row, values=profiles,
            font=ctk.CTkFont(size=11),
            fg_color=BG_INPUT, button_color=BORDER_LIGHT,
            dropdown_fg_color=BG_CARD,
            width=220, height=32,
            command=self._on_profile_change
        )
        self.profile_menu.pack(side="left", padx=(0, 16))

        # Interval
        ctk.CTkLabel(ctrl_row, text="Interval (s):",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 6))

        self.interval_entry = ctk.CTkEntry(
            ctrl_row, width=60, height=32, font=ctk.CTkFont(size=11),
            fg_color=BG_INPUT, border_color=BORDER
        )
        self.interval_entry.insert(0, "0.5")
        self.interval_entry.pack(side="left", padx=(0, 16))

        self.sim_start_btn = ctk.CTkButton(
            ctrl_row, text="⚡  Start Simulation",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ORANGE_DARK, hover_color=ORANGE,
            height=38, corner_radius=8, width=180,
            command=self.start_simulation
        )
        self.sim_start_btn.pack(side="left", padx=(0, 8))

        self.sim_stop_btn = ctk.CTkButton(
            ctrl_row, text="⏹  Stop",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=BG_INPUT, hover_color=RED_DARK,
            height=38, corner_radius=8, width=100,
            state="disabled",
            command=self.stop_simulation
        )
        self.sim_stop_btn.pack(side="left")

        self.sim_status_badge = ctk.CTkLabel(
            ctrl_row, text="● IDLE",
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            text_color=TEXT_DIM
        )
        self.sim_status_badge.pack(side="right")

        # ── Attack Profile Cards ──
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 12))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        attack_cards_def = [
            ("🔍", "PortScan", "Reconnaissance", "Network port scanning", BLUE, "50-60"),
            ("💥", "DoS", "Denial of Service", "GoldenEye / Hulk / Slowloris", RED, "75-85"),
            ("🌊", "DDoS", "Distributed DoS", "Volumetric flood attack", PINK, "85-95"),
            ("🤖", "Bot", "Botnet C2", "Command & control traffic", PURPLE, "80-90"),
        ]

        for col, (icon, name, cat, desc, color, severity) in enumerate(attack_cards_def):
            c = ctk.CTkFrame(cards_frame, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER)
            c.grid(row=0, column=col, sticky="nsew", padx=4)

            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(size=24)).pack(padx=14, pady=(14, 4))
            ctk.CTkLabel(c, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=color).pack()
            ctk.CTkLabel(c, text=cat, font=ctk.CTkFont(size=10),
                         text_color=TEXT_MUTED).pack()
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=9),
                         text_color=TEXT_DIM, wraplength=140).pack(padx=10, pady=(4, 2))
            ctk.CTkLabel(c, text=f"Severity: {severity}/100",
                         font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
                         text_color=color).pack(pady=(2, 14))

    # ═══════════════════════════════════════════════
    #  PAGE: DETECTION LOGS
    # ═══════════════════════════════════════════════
    def _build_logs_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color=BG_DARK)
        self.pages["logs"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=10,
                              border_width=1, border_color=BORDER)
        header.pack(fill="x", padx=16, pady=(12, 8))

        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(h_inner, text="📋  FULL DETECTION LOG",
                     font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                     text_color=TEXT_WHITE).pack(side="left")

        ctk.CTkButton(h_inner, text="Clear All", width=80, height=30,
                      corner_radius=6, fg_color=BG_INPUT, hover_color=RED_DARK,
                      font=ctk.CTkFont(size=11), command=self._clear_log
                      ).pack(side="right")

        self.logs_auto_scroll = ctk.CTkSwitch(
            h_inner, text="Auto-Scroll", font=ctk.CTkFont(size=11),
            onvalue=True, offvalue=False
        )
        self.logs_auto_scroll.select()
        self.logs_auto_scroll.pack(side="right", padx=16)

        # Log display (shares the same log_text widget from dashboard — reference only display)
        self.logs_text = ctk.CTkTextbox(
            page,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color="#050810",
            text_color=CYAN,
            corner_radius=8,
            border_width=1,
            border_color=BORDER
        )
        self.logs_text.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.logs_text.tag_config("INFO", foreground=CYAN)
        self.logs_text.tag_config("FLOW", foreground=GREEN)
        self.logs_text.tag_config("THREAT", foreground=RED)
        self.logs_text.tag_config("WARN", foreground=ORANGE)
        self.logs_text.tag_config("ERROR", foreground="#FF6B6B")
        self.logs_text.tag_config("SUCCESS", foreground=GREEN)

    # ═══════════════════════════════════════════════
    #  PAGE: SETTINGS
    # ═══════════════════════════════════════════════
    def _build_settings_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color=BG_DARK)
        self.pages["settings"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color=BG_DARK, scrollbar_button_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # ── API Endpoint ──
        api_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                                border_width=1, border_color=BORDER)
        api_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(api_card, text="🌐  BACKEND API CONFIGURATION",
                     font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                     text_color=TEXT_WHITE).pack(anchor="w", padx=20, pady=(16, 8))

        api_row = ctk.CTkFrame(api_card, fg_color="transparent")
        api_row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(api_row, text="Target Endpoint:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))

        self.api_entry = ctk.CTkEntry(
            api_row, width=450, height=34,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=BG_INPUT, border_color=BORDER
        )
        self.api_entry.insert(0, self.target_api_url)
        self.api_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            api_row, text="Test Health", width=100, height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=CYAN_DARK, hover_color=CYAN,
            corner_radius=6,
            command=self._check_backend_health
        ).pack(side="left")

        # ── ML Engine Status ──
        ml_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10,
                               border_width=1, border_color=BORDER)
        ml_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(ml_card, text="🧠  ML ENGINE STATUS",
                     font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                     text_color=TEXT_WHITE).pack(anchor="w", padx=20, pady=(16, 8))

        ml_info = ctk.CTkFrame(ml_card, fg_color="transparent")
        ml_info.pack(fill="x", padx=20, pady=(0, 16))

        if self.prediction_service:
            status_items = [
                ("Model", self.prediction_service.model_name, GREEN),
                ("Features", str(len(self.prediction_service.feature_names)), CYAN),
                ("Predictor", type(self.prediction_service.predictor).__name__, GREEN),
                ("Status", "ACTIVE", GREEN),
            ]
        else:
            status_items = [
                ("Model", "NOT LOADED", RED),
                ("Features", "—", RED),
                ("Predictor", "—", RED),
                ("Status", "FAILED", RED),
            ]

        for label, value, color in status_items:
            row = ctk.CTkFrame(ml_info, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_MUTED, width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(family="JetBrains Mono", size=11),
                         text_color=color).pack(side="left")

    # ═══════════════════════════════════════════════
    #  PAGE: ABOUT
    # ═══════════════════════════════════════════════
    def _build_about_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color=BG_DARK)
        self.pages["about"] = page

        center = ctk.CTkFrame(page, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(center, text="🛡️", font=ctk.CTkFont(size=48)).pack(pady=(0, 8))
        ctk.CTkLabel(center, text="CortexAgent",
                     font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
                     text_color=CYAN).pack()
        ctk.CTkLabel(center, text="Enterprise Network Threat Detection",
                     font=ctk.CTkFont(family="Inter", size=14),
                     text_color=TEXT_MUTED).pack(pady=(4, 16))

        ctk.CTkFrame(center, height=1, width=300, fg_color=BORDER).pack(pady=8)

        info_items = [
            ("Version", "2.0.0"),
            ("Engine", "LightGBM + CICIDS2017"),
            ("Pipeline", "Production InferencePipeline"),
            ("Features", "20 Network Flow Features"),
            ("Framework", "CustomTkinter + Python 3.x"),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(center, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT_MUTED, width=120, anchor="e").pack(side="left")
            ctk.CTkLabel(row, text=f"  {value}", font=ctk.CTkFont(size=12),
                         text_color=TEXT_WHITE).pack(side="left")

        ctk.CTkFrame(center, height=1, width=300, fg_color=BORDER).pack(pady=12)

        ctk.CTkLabel(center, text="Built for Cortex NIDS Platform",
                     font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack()
        ctk.CTkLabel(center, text="© 2026 — MIT License",
                     font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(pady=(2, 0))

    # ═══════════════════════════════════════════════
    #  UTILITY METHODS
    # ═══════════════════════════════════════════════
    def _get_interface_list(self):
        default_opt = "Auto-Detect Active Connection (Recommended)"
        try:
            ifaces = list_network_interfaces()
            names = [ifc.get("name", "") for ifc in ifaces if ifc.get("name")]
            return [default_opt] + [n for n in names if n]
        except Exception:
            return [default_opt]

    def _on_interface_change(self, choice):
        self.selected_interface = choice

    def _on_profile_change(self, choice):
        self.selected_profile = choice

    def _update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_lbl.configure(text=now)
        self.after(1000, self._update_clock)

    def _reset_counters(self):
        self.flows_captured = 0
        self.predictions_made = 0
        self.threats_detected = 0
        self.total_confidence_sum = 0.0
        self.last_detection_str = "—"
        self._update_dashboard_stats()
        self.log("INFO", "Telemetry counters reset.")

    def log(self, level: str, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level:<7}] {msg}\n"

        def _append():
            # Dashboard console
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert("end", formatted, level)
                self.log_text.see("end")
            # Logs page console
            if hasattr(self, 'logs_text') and self.logs_text:
                self.logs_text.insert("end", formatted, level)
                if hasattr(self, 'logs_auto_scroll') and self.logs_auto_scroll.get():
                    self.logs_text.see("end")

        self.after(0, _append)

    def _clear_log(self):
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.delete("1.0", "end")
        if hasattr(self, 'logs_text') and self.logs_text:
            self.logs_text.delete("1.0", "end")

    def _check_backend_health(self):
        import urllib.request

        # Update API URL from settings entry if available
        if hasattr(self, 'api_entry'):
            self.target_api_url = self.api_entry.get().strip()

        def _check():
            url = f"{self.target_api_url.rstrip('/')}/health"
            try:
                req = urllib.request.urlopen(url, timeout=3.0)
                if req.getcode() == 200:
                    self.backend_online = True
                    self.after(0, lambda: self.backend_badge.configure(
                        text="  ●  ONLINE (RAILWAY)", text_color=GREEN))
                    self.log("SUCCESS", f"Connected to Cloud Backend API: {url}")
                    return
            except Exception:
                pass
            self.backend_online = False
            self.after(0, lambda: self.backend_badge.configure(
                text="  ○  OFFLINE (LOCAL)", text_color=RED))
            self.log("WARN", f"Backend unreachable at {url}. Running in local SQLite mode.")

        threading.Thread(target=_check, daemon=True).start()

    def _update_dashboard_stats(self):
        avg_conf = (self.total_confidence_sum / max(1, self.predictions_made)) * 100

        def _update():
            if "flows" in self.stat_cards:
                self.stat_cards["flows"]._value_label.configure(text=f"{self.flows_captured:,}")
            if "preds" in self.stat_cards:
                self.stat_cards["preds"]._value_label.configure(text=f"{self.predictions_made:,}")
            if "threats" in self.stat_cards:
                self.stat_cards["threats"]._value_label.configure(text=f"{self.threats_detected:,}")
            if "conf" in self.stat_cards:
                self.stat_cards["conf"]._value_label.configure(text=f"{avg_conf:.1f}%")
            if "last" in self.stat_cards:
                self.stat_cards["last"]._value_label.configure(text=self.last_detection_str[:20])

            # Update monitoring page stats too
            if hasattr(self, 'mon_stat_lbls'):
                self.mon_stat_lbls.get("flows", None) and self.mon_stat_lbls["flows"].configure(text=f"{self.flows_captured:,}")
                self.mon_stat_lbls.get("preds", None) and self.mon_stat_lbls["preds"].configure(text=f"{self.predictions_made:,}")
                self.mon_stat_lbls.get("threats", None) and self.mon_stat_lbls["threats"].configure(text=f"{self.threats_detected:,}")

        self.after(0, _update)

    # ═══════════════════════════════════════════════
    #  MODE 1: LIVE PACKET MONITORING
    # ═══════════════════════════════════════════════
    def start_monitoring(self):
        if self.monitoring_active:
            return

        iface = self.selected_interface
        self.monitoring_active = True

        # Update buttons across pages
        self.mon_start_btn.configure(state="disabled", fg_color=BG_INPUT)
        self.mon_stop_btn.configure(state="normal", fg_color=RED_DARK)
        self.mon_status_badge.configure(text="● RUNNING", text_color=GREEN)
        self.dash_mon_btn.configure(state="disabled", fg_color=BG_INPUT, text="📡  Monitoring...")

        self.log("INFO", f"Starting Mode 1: Live Packet Monitor on '{iface}'...")

        self.capturer = PacketCapturer(
            interface=iface if (iface and not iface.startswith("Auto-Detect") and iface != "Default Interface") else None,
            bpf_filter="ip"
        )
        self.flow_builder = FlowBuilder(idle_timeout_sec=2.0)

        self.monitor_thread = threading.Thread(
            target=self.capturer.start_capture,
            args=(self._on_packet_received,),
            daemon=True
        )
        self.monitor_thread.start()

        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()

    def stop_monitoring(self):
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.capturer:
            self.capturer.stop_capture()

        self.mon_start_btn.configure(state="normal", fg_color=GREEN_DARK)
        self.mon_stop_btn.configure(state="disabled", fg_color=BG_INPUT)
        self.mon_status_badge.configure(text="● IDLE", text_color=TEXT_DIM)
        self.dash_mon_btn.configure(state="normal", fg_color=GREEN_DARK, text="📡  Start Monitoring")

        self.log("WARN", "Stopped Mode 1: Live Packet Monitor.")

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

    # ═══════════════════════════════════════════════
    #  MODE 2: THREAT VALIDATION LAB
    # ═══════════════════════════════════════════════
    def start_simulation(self):
        if self.simulation_active:
            return

        self.simulation_active = True
        self.sim_start_btn.configure(state="disabled", fg_color=BG_INPUT)
        self.sim_stop_btn.configure(state="normal", fg_color=RED_DARK)
        self.sim_status_badge.configure(text="● RUNNING", text_color=ORANGE)
        self.dash_sim_btn.configure(state="disabled", fg_color=BG_INPUT, text="⚡  Simulating...")

        # Parse interval
        try:
            self.sim_interval = float(self.interval_entry.get())
        except (ValueError, AttributeError):
            self.sim_interval = 0.5

        self.log("INFO", f"Starting Mode 2: Threat Validation Lab ({self.selected_profile})...")

        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()

    def stop_simulation(self):
        if not self.simulation_active:
            return

        self.simulation_active = False
        self.sim_start_btn.configure(state="normal", fg_color=ORANGE_DARK)
        self.sim_stop_btn.configure(state="disabled", fg_color=BG_INPUT)
        self.sim_status_badge.configure(text="● IDLE", text_color=TEXT_DIM)
        self.dash_sim_btn.configure(state="normal", fg_color=ORANGE_DARK, text="⚡  Start Simulation")

        self.log("WARN", "Stopped Mode 2: Threat Validation Lab.")

    def _simulation_loop(self):
        profile_choice = self.selected_profile

        while self.simulation_active:
            # Determine profile type
            if "DoS" in profile_choice:
                mode = "DoS GoldenEye"
            elif "DDoS" in profile_choice:
                mode = "DDoS"
            elif "PortScan" in profile_choice:
                mode = "PortScan"
            else: # Balanced Mix
                r = random.random()
                if r < 0.40:
                    mode = "BENIGN"
                elif r < 0.65:
                    mode = "DoS GoldenEye"
                elif r < 0.85:
                    mode = "DDoS"
                else:
                    mode = "PortScan"

            ip_last = random.randint(2, 250)

            if mode == "DoS GoldenEye":
                flow_feats = {
                    "_src_ip": f"172.16.0.{ip_last}",
                    "_dst_ip": "10.0.0.1",
                    "_protocol": "TCP",
                    "Destination Port": 80.0,
                    "Total Length of Fwd Packets": 322.0,
                    "Fwd Packet Length Max": 322.0,
                    "Bwd Packet Length Max": 3525.0,
                    "Flow Bytes/s": 324.4,
                    "Flow IAT Std": 2786056.0,
                    "Fwd IAT Min": 609.0,
                    "Fwd Header Length": 168.0,
                    "Bwd Header Length": 136.0,
                    "Bwd Packets/s": 0.33,
                    "FIN Flag Count": 0.0,
                    "PSH Flag Count": 1.0,
                    "Init_Win_bytes_forward": 29200.0,
                    "Init_Win_bytes_backward": 235.0,
                    "act_data_pkt_fwd": 1.0,
                    "min_seg_size_forward": 32.0,
                    "Active Mean": 4846.0,
                    "Active Std": 0.0,
                    "Active Max": 4846.0,
                    "Idle Std": 0.0
                }
            elif mode == "DDoS":
                flow_feats = {
                    "_src_ip": f"10.0.0.{ip_last}",
                    "_dst_ip": "10.0.0.1",
                    "_protocol": "TCP",
                    "Destination Port": 80.0,
                    "Total Length of Fwd Packets": 30.0,
                    "Fwd Packet Length Max": 6.0,
                    "Bwd Packet Length Max": 0.0,
                    "Flow Bytes/s": 6.0,
                    "Flow IAT Std": 2500306.0,
                    "Fwd IAT Min": 1.0,
                    "Fwd Header Length": 100.0,
                    "Bwd Header Length": 0.0,
                    "Bwd Packets/s": 0.0,
                    "FIN Flag Count": 0.0,
                    "PSH Flag Count": 0.0,
                    "Init_Win_bytes_forward": 256.0,
                    "Init_Win_bytes_backward": -1.0,
                    "act_data_pkt_fwd": 4.0,
                    "min_seg_size_forward": 20.0,
                    "Active Mean": 8003.0,
                    "Active Std": 0.0,
                    "Active Max": 8003.0,
                    "Idle Std": 0.0
                }
            elif mode == "PortScan":
                target_ports = [21, 22, 23, 25, 53, 80, 110, 1700, 3306, 8080]
                flow_feats = {
                    "_src_ip": f"192.168.1.{ip_last}",
                    "_dst_ip": "10.0.0.1",
                    "_protocol": "TCP",
                    "Destination Port": float(random.choice(target_ports)),
                    "Total Length of Fwd Packets": 2.0,
                    "Fwd Packet Length Max": 2.0,
                    "Bwd Packet Length Max": 6.0,
                    "Flow Bytes/s": 380952.0,
                    "Flow IAT Std": 0.0,
                    "Fwd IAT Min": 0.0,
                    "Fwd Header Length": 24.0,
                    "Bwd Header Length": 20.0,
                    "Bwd Packets/s": 47619.0,
                    "FIN Flag Count": 0.0,
                    "PSH Flag Count": 1.0,
                    "Init_Win_bytes_forward": 1024.0,
                    "Init_Win_bytes_backward": 0.0,
                    "act_data_pkt_fwd": 0.0,
                    "min_seg_size_forward": 24.0,
                    "Active Mean": 0.0,
                    "Active Std": 0.0,
                    "Active Max": 0.0,
                    "Idle Std": 0.0
                }
            else: # BENIGN
                flow_feats = {
                    "_src_ip": f"192.168.1.{ip_last}",
                    "_dst_ip": "10.0.0.1",
                    "_protocol": "TCP",
                    "Destination Port": random.choice([80, 443, 8080]),
                    "Total Length of Fwd Packets": random.randint(500, 5000),
                    "Fwd Packet Length Max": random.randint(200, 1460),
                    "Bwd Packet Length Max": random.randint(200, 1460),
                    "Flow Bytes/s": random.randint(10000, 100000),
                    "Flow IAT Std": random.uniform(10, 200),
                    "Fwd IAT Min": random.randint(1, 10),
                    "Fwd Header Length": 40,
                    "Bwd Header Length": 40,
                    "Bwd Packets/s": random.randint(10, 100),
                    "FIN Flag Count": 0,
                    "PSH Flag Count": 1,
                    "Init_Win_bytes_forward": 8192,
                    "Init_Win_bytes_backward": 8192,
                    "act_data_pkt_fwd": random.randint(2, 10),
                    "min_seg_size_forward": 20,
                    "Active Mean": 0,
                    "Active Std": 0,
                    "Active Max": 0,
                    "Idle Std": 0
                }

            self._evaluate_and_post_flow(flow_feats, is_live=False)
            time.sleep(self.sim_interval)

    # ═══════════════════════════════════════════════
    #  SHARED PRODUCTION INFERENCE & TELEMETRY
    # ═══════════════════════════════════════════════
    def _resolve_process_name(self, flow_feats: Dict[str, Any]) -> str:
        """Resolves active Windows Application / Process Name for the flow using psutil."""
        try:
            import psutil
            sp = flow_feats.get("_src_port")
            dp = flow_feats.get("_dst_port", flow_feats.get("Destination Port"))

            src_port = int(float(sp)) if sp is not None else None
            dst_port = int(float(dp)) if dp is not None else None

            conns = {}
            active_procs = {}
            for c in psutil.net_connections(kind="inet"):
                if c.pid:
                    try:
                        pname = psutil.Process(c.pid).name()
                        if pname and pname.lower() not in ["system idle process", "pythonservice.exe"]:
                            if c.laddr:
                                conns[c.laddr.port] = pname
                            if c.raddr:
                                conns[c.raddr.port] = pname
                            active_procs[c.pid] = pname
                    except Exception:
                        pass

            # 1. Exact socket port match (Local or Remote)
            if src_port and src_port in conns:
                return conns[src_port]
            if dst_port and dst_port in conns:
                return conns[dst_port]

            # 2. Match active running application processes by traffic type
            proc_names = list(active_procs.values())
            if proc_names:
                # Check VS Code
                code_apps = [p for p in proc_names if "code" in p.lower()]
                if code_apps and (dst_port in [80, 443, 8080] or src_port in [80, 443, 8080]):
                    return code_apps[0]

                # Check Web Browsers (Brave, Chrome, Edge, Firefox, Opera)
                browsers = [p for p in proc_names if any(b in p.lower() for b in ["brave", "chrome", "msedge", "firefox", "opera"])]
                if browsers and (dst_port in [80, 443] or src_port in [80, 443]):
                    return browsers[0]

                # Check IDEs & Developer Tools (Antigravity, Python, VS Code)
                devs = [p for p in proc_names if any(d in p.lower() for d in ["antigravity", "python", "idea"])]
                if devs:
                    return devs[0]

                return proc_names[0]
        except Exception:
            pass
        return "svchost.exe"

    def _evaluate_and_post_flow(self, flow_feats: Dict[str, Any], is_live: bool = False):
        import urllib.request

        try:
            # Guard: ensure prediction pipeline is initialized
            if self.prediction_service is None or self.prediction_service.predictor is None:
                self.log("ERROR", "PredictionService not initialized. Cannot run inference. Check model files.")
                return

            self.flows_captured += 1

            app_name = self._resolve_process_name(flow_feats)
            app_str = f" [{app_name}]" if app_name else ""

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
                self.log("THREAT", f"🚨 ALERT [{risk_level}]: {attack_type} | Risk: {risk_score:.1f}/100 |{app_str} {src_ip} -> :{dst_port} | Latency: {latency:.2f}ms")
            else:
                self.log("FLOW", f"Flow{app_str} [{src_ip} -> :{dst_port}] | {attack_type} | Confidence: {confidence*100:.1f}% | {latency:.2f}ms")

            # 2. Persist to Local SQLite (alerts.db)
            if self.alert_engine:
                self.alert_engine.process_prediction(
                    prediction_result=pred_result,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    protocol=protocol,
                    dst_port=dst_port
                )

            # 3. Post Telemetry to Cloud Backend (Railway API)
            if self.backend_online:
                try:
                    # Metric summary counter
                    payload = json.dumps({
                        "attack_type": attack_type,
                        "confidence": confidence,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "latency_ms": latency,
                        "count": 1
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        f"{self.target_api_url.rstrip('/')}/metrics/record",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=1.0)
                except Exception:
                    pass

                try:
                    # Full alert event for WebSocket stream & Live Threats page on website
                    alert_payload = json.dumps({
                        "attack_type": attack_type,
                        "confidence": confidence,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "latency_ms": latency,
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "protocol": protocol,
                        "dst_port": dst_port
                    }).encode("utf-8")
                    req2 = urllib.request.Request(
                        f"{self.target_api_url.rstrip('/')}/alerts/record",
                        data=alert_payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    urllib.request.urlopen(req2, timeout=1.0)
                except Exception:
                    pass

            # 4. Update Dashboard Stats
            self._update_dashboard_stats()

        except Exception as e:
            self.log("ERROR", f"Inference pipeline error: {e}")


def launch_cortex_agent():
    """Entry point for CortexAgent desktop application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    app = CortexAgentGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_cortex_agent()
