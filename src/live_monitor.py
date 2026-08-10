"""
Live Monitor module for NIDS.
Coordinates packet capture, flow building, ML model prediction, alert storage, and real-time WebSocket streaming.
"""
import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from src.packet_capture import PacketCapturer, list_network_interfaces
from src.flow_builder import FlowBuilder
from src.prediction_service import PredictionService
from src.alert_engine import AlertEngine
from src.websocket_server import ws_manager
from src.utils.utils import get_absolute_path

logger = logging.getLogger(__name__)


class LiveMonitor:
    """
    Real-Time Network Intrusion Monitor.
    Sniffs live network interface packets, aggregates into flows, executes ML inference,
    persists threat alerts, and streams updates via WebSockets.
    """

    def __init__(
        self,
        interface: Optional[str] = None,
        bpf_filter: str = "ip",
        idle_timeout: float = 2.0,
        db_dir: Union[str, Path] = "predictions"
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter

        self.capturer = PacketCapturer(interface=interface, bpf_filter=bpf_filter)
        self.flow_builder = FlowBuilder(idle_timeout_sec=idle_timeout)
        self.alert_engine = AlertEngine(db_dir=db_dir)

        # Initialize Module 8 Prediction Engine
        self.prediction_service = PredictionService(output_dir=db_dir)
        self.predictor = self.prediction_service.predictor

        self.is_running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._flush_thread: Optional[threading.Thread] = None

    def start_monitoring(self) -> None:
        """
        Starts non-blocking background threads for packet sniffing and flow flushing.
        """
        if self.is_running:
            logger.warning("Live Monitor is already running.")
            return

        self.is_running = True
        logger.info("Starting NIDS Live Intrusion Monitor...")

        # 1. Packet Sniffing Thread
        self._capture_thread = threading.Thread(
            target=self.capturer.start_capture,
            args=(self._on_packet_received,),
            daemon=True
        )
        self._capture_thread.start()

        # 2. Flow Flushing Thread
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True
        )
        self._flush_thread.start()

        logger.info("Live Intrusion Monitor background threads started successfully.")

    def stop_monitoring(self) -> None:
        """Stops live monitoring threads."""
        self.is_running = False
        self.capturer.stop_capture()
        logger.info("Stopped Live Intrusion Monitor.")

    def _on_packet_received(self, pkt: Any) -> None:
        """Callback executed for every captured Scapy packet."""
        completed_flow = self.flow_builder.process_packet(pkt)
        if completed_flow:
            self._evaluate_flow(completed_flow)

    def _flush_loop(self) -> None:
        """Periodic loop flushing idle flows and executing ML inference."""
        while self.is_running:
            time.sleep(1.0)
            expired_flows = self.flow_builder.flush_expired_flows()
            for flow_feats in expired_flows:
                self._evaluate_flow(flow_feats)

    def _evaluate_flow(self, flow_feats: Dict[str, Any]) -> None:
        """
        Executes ML prediction on a completed flow feature dictionary,
        persists alerts, and broadcasts WebSocket update.
        """
        try:
            # Extract metadata
            src_ip = flow_feats.pop("_src_ip", "192.168.1.100")
            dst_ip = flow_feats.pop("_dst_ip", "10.0.0.1")
            protocol = flow_feats.pop("_protocol", "TCP")
            dst_port = int(flow_feats.get("Destination Port", 80))

            # Remove private keys before inference
            for k in list(flow_feats.keys()):
                if k.startswith("_"):
                    flow_feats.pop(k, None)

            # Predict using Module 8 Predictor
            pred_result = self.predictor.predict_single(flow_feats)

            # Record real-time metrics
            try:
                from api.metrics_manager import metrics_manager
                metrics_manager.record_prediction(
                    attack_type=pred_result.get("Attack_Type", "BENIGN"),
                    confidence=float(pred_result.get("Prediction_Confidence", 0.99)),
                    risk_score=float(pred_result.get("Risk_Score", 0.0)),
                    risk_level=pred_result.get("Risk_Level", "Low"),
                    latency_ms=float(pred_result.get("Prediction_Time_ms", 0.035)),
                    count=1
                )
            except Exception:
                pass

            # Store Alert
            alert_event = self.alert_engine.process_prediction(
                prediction_result=pred_result,
                src_ip=src_ip,
                dst_ip=dst_ip,
                protocol=protocol,
                dst_port=dst_port
            )

            # Broadcast WebSocket event asynchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(ws_manager.broadcast(alert_event), loop)
            except Exception:
                pass

        except Exception as e:
            logger.error("Error evaluating live flow: %s", e)
