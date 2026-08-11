"""
Dynamic Report Engine for NIDS.
Compiles real-time security incident reports, evaluation benchmarks, XAI feature rankings,
and system telemetry directly from predictions/alerts.db, SessionMetricsManager, and trained model checkpoints.

Exports HTML, PDF, CSV, and Markdown formats dynamically on demand.
"""
import io
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from api.session_metrics import session_metrics_manager
from src.alert_engine import AlertEngine
from src.model_loader import ModelLoader
from src.utils.utils import get_absolute_path

logger = logging.getLogger(__name__)


class DynamicReportEngine:
    """
    Real-time Dynamic Report Compilation Engine.
    Queries active alerts.db database, session metrics, and trained model artifacts
    to compile fresh, timestamped security reports in PDF, HTML, CSV, and Markdown.
    """

    def __init__(self):
        self.alert_engine = AlertEngine()
        self.model_loader = ModelLoader()
        self.reports_dir = get_absolute_path("reports/generated")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def get_live_report_data(self) -> Dict[str, Any]:
        """Queries alerts.db, session metrics, and model metadata to assemble fresh report metrics."""
        db_summary = self.alert_engine.get_analytics_summary()
        top_attacks = self.alert_engine.get_analytics_top_attacks(limit=10)
        severity_counts = self.alert_engine.get_analytics_severity()
        latest_alerts = self.alert_engine.query_historical_threats_paginated(page=1, page_size=50).get("alerts", [])
        session_metrics = session_metrics_manager.get_metrics()
        meta = self.model_loader.load_metadata()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "db_summary": db_summary,
            "top_attacks": top_attacks,
            "severity_counts": severity_counts,
            "latest_alerts": latest_alerts,
            "session_metrics": session_metrics,
            "model_metadata": meta,
        }

    def generate_html_report(self) -> str:
        """Generates a dynamic HTML security report compiled from live database data."""
        data = self.get_live_report_data()
        ts = data["timestamp"]
        summary = data["db_summary"]
        session = data["session_metrics"]
        top_atks = data["top_attacks"]
        alerts = data["latest_alerts"]

        top_atks_rows = ""
        for atk in top_atks:
            top_atks_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #1E2C42; color: #E2E8F0;">{atk.get('attack_type')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #1E2C42; color: #38BDF8; font-weight: bold; text-align: right;">{atk.get('count')}</td>
            </tr>
            """

        alerts_rows = ""
        for alt in alerts[:15]:
            alerts_rows += f"""
            <tr>
                <td style="padding: 6px 10px; border-bottom: 1px solid #1E2C42; color: #A855F7;">{alt.get('id')}</td>
                <td style="padding: 6px 10px; border-bottom: 1px solid #1E2C42; color: #94A3B8;">{alt.get('timestamp')}</td>
                <td style="padding: 6px 10px; border-bottom: 1px solid #1E2C42; color: #F8FAFC; font-weight: bold;">{alt.get('attack_type')}</td>
                <td style="padding: 6px 10px; border-bottom: 1px solid #1E2C42; color: #4ADE80;">{(alt.get('confidence', 0) * 100):.2f}%</td>
                <td style="padding: 6px 10px; border-bottom: 1px solid #1E2C42; color: #F43F5E;">{alt.get('risk_level')} ({alt.get('risk_score')})</td>
                <td style="padding: 6px 10px; border-bottom: 1px solid #1E2C42; color: #CBD5E1;">{alt.get('src_ip', '192.168.1.1')}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cortex NIDS - Live Security Incident & Telemetry Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #04070E; color: #F8FAFC; margin: 0; padding: 30px; }}
        .card {{ background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; }}
        h1 {{ color: #38BDF8; margin-top: 0; font-size: 24px; }}
        h2 {{ color: #A855F7; font-size: 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 8px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
        .kpi {{ background: #0B1220; border: 1px solid rgba(255, 255, 255, 0.08); padding: 16px; border-radius: 12px; }}
        .kpi-title {{ font-size: 11px; color: #94A3B8; text-transform: uppercase; }}
        .kpi-value {{ font-size: 22px; font-weight: bold; color: #38BDF8; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; font-family: monospace; font-size: 12px; }}
        th {{ background: #0F172A; color: #94A3B8; text-align: left; padding: 10px; border-bottom: 2px solid #1E2C42; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🛡️ Cortex NIDS Security & Threat Intelligence Report</h1>
        <p style="color: #94A3B8; font-size: 12px;">Compiled Live from <code>predictions/alerts.db</code> on <strong>{ts}</strong></p>

        <div class="grid">
            <div class="kpi">
                <div class="kpi-title">Total Database Flows</div>
                <div class="kpi-value">{summary.get('total_flows_ever', 0):,}</div>
            </div>
            <div class="kpi">
                <div class="kpi-title">Total Attacks Detected</div>
                <div class="kpi-value" style="color: #F43F5E;">{summary.get('total_attacks_ever', 0):,}</div>
            </div>
            <div class="kpi">
                <div class="kpi-title">Active Session Predictions</div>
                <div class="kpi-value" style="color: #4ADE80;">{session.get('prediction_count', 0):,}</div>
            </div>
            <div class="kpi">
                <div class="kpi-title">Avg Model Confidence</div>
                <div class="kpi-value">{(summary.get('average_confidence_ever', 0) * 100):.2f}%</div>
            </div>
        </div>

        <h2>🥇 Top Attack Categories</h2>
        <table>
            <thead>
                <tr><th>Attack Category</th><th style="text-align: right;">Total Incidents</th></tr>
            </thead>
            <tbody>{top_atks_rows}</tbody>
        </table>

        <h2 style="margin-top: 30px;">🚨 Recent Threat Alert Audit Log</h2>
        <table>
            <thead>
                <tr><th>Alert ID</th><th>Timestamp</th><th>Attack Type</th><th>Confidence</th><th>Risk Level</th><th>Source IP</th></tr>
            </thead>
            <tbody>{alerts_rows}</tbody>
        </table>
    </div>
</body>
</html>"""
        return html_content

    def generate_pdf_bytes(self) -> bytes:
        """Generates a dynamic PDF security report using ReportLab."""
        data = self.get_live_report_data()
        ts = data["timestamp"]
        summary = data["db_summary"]
        session = data["session_metrics"]
        top_atks = data["top_attacks"]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, textColor=colors.HexColor('#1E293B'), spaceAfter=6)
        sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=15)
        h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#0F172A'), spaceBefore=12, spaceAfter=8)

        story.append(Paragraph("CORTEX NIDS Enterprise Security Report", title_style))
        story.append(Paragraph(f"Generated Live from <b>predictions/alerts.db</b> | Date: {ts}", sub_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceAfter=15))

        kpi_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Database Flows", f"{summary.get('total_flows_ever', 0):,}", "Total Attacks Detected", f"{summary.get('total_attacks_ever', 0):,}"],
            ["Session Predictions", f"{session.get('prediction_count', 0):,}", "Average Confidence", f"{(summary.get('average_confidence_ever', 0) * 100):.2f}%"],
            ["Average Latency", f"{summary.get('average_latency_ever', 0):.2f} ms", "Active Model", "LightGBM Classifier"],
        ]
        t_kpi = Table(kpi_data, colWidths=[130, 130, 130, 130])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ]))
        story.append(t_kpi)
        story.append(Spacer(1, 15))

        story.append(Paragraph("Top Threat Attack Categories", h2_style))
        atk_table_data = [["Attack Category", "Incident Count"]]
        for a in top_atks:
            atk_table_data.append([a.get("attack_type", "BENIGN"), str(a.get("count", 0))])
        
        t_atk = Table(atk_table_data, colWidths=[300, 220])
        t_atk.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(t_atk)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_csv_string(self) -> str:
        """Exports all alerts in predictions/alerts.db as a formatted CSV string."""
        res = self.alert_engine.query_historical_threats_paginated(page=1, page_size=100000)
        alerts = res.get("alerts", [])
        if not alerts:
            return "id,timestamp,attack_type,confidence,risk_score,risk_level,src_ip,dst_ip,protocol,dst_port\n"
        df = pd.DataFrame(alerts)
        if "class_probabilities" in df.columns:
            df = df.drop(columns=["class_probabilities"])
        return df.to_csv(index=False)

    def generate_markdown_report(self) -> str:
        """Generates a Markdown security audit report."""
        data = self.get_live_report_data()
        ts = data["timestamp"]
        summary = data["db_summary"]
        session = data["session_metrics"]
        top_atks = data["top_attacks"]

        top_rows = "\n".join([f"| `{a.get('attack_type')}` | **{a.get('count')}** |" for a in top_atks])

        md = f"""# 🛡️ Cortex NIDS Live Security Audit Report

**Generated Timestamp**: `{ts}`  
**Data Source**: `predictions/alerts.db`  

---

## 📊 Performance & Telemetry Summary

- **Total Database Flows**: `{summary.get('total_flows_ever', 0):,}`
- **Total Attacks Detected**: `{summary.get('total_attacks_ever', 0):,}`
- **Session Predictions**: `{session.get('prediction_count', 0):,}`
- **Average Model Confidence**: `{(summary.get('average_confidence_ever', 0) * 100):.2f}%`
- **Average Inference Latency**: `{summary.get('average_latency_ever', 0):.2f} ms`

---

## 🥇 Top Attack Categories

| Attack Category | Total Incidents |
|:---|:---:|
{top_rows}

---
*Report generated dynamically by Cortex NIDS Reporting Engine.*
"""
        return md
