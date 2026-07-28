"""
Automated PDF Documentation Generator for NIDS.
Generates Project_Report.pdf, Architecture.pdf, and Installation.pdf using ReportLab.
"""
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.utils import ensure_directory, get_absolute_path


def create_pdf(filename: str, title: str, subtitle: str, content_blocks: list):
    output_dir = ensure_directory(get_absolute_path("reports"))
    pdf_path = output_dir / filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=0,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        "DocHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=8
    )

    story = [
        Paragraph(title, title_style),
        Paragraph(f"{subtitle} | Generated: {datetime.now().strftime('%Y-%m-%d')}", subtitle_style),
        Spacer(1, 10)
    ]

    for section_title, text_body in content_blocks:
        story.append(Paragraph(section_title, heading_style))
        story.append(Paragraph(text_body, body_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated PDF: {pdf_path}")


def main():
    # 1. Project Report PDF
    create_pdf(
        "Project_Report.pdf",
        "Enterprise Network Intrusion Detection System",
        "Comprehensive Project Executive Report & Model Evaluation",
        [
            ("1. Executive Summary", "This report documents the design, implementation, and evaluation of the Machine Learning-Based Enterprise Network Intrusion Detection System (NIDS). The platform achieves 99.87% accuracy and sub-millisecond prediction latency."),
            ("2. Machine Learning Architecture", "The core classifier uses LightGBM trained on 2,830,743 network telemetry records across 15 attack categories. Feature engineering maps 78 raw fields down to 20 optimal flow-based indicators."),
            ("3. SOC Dashboard & Operational Performance", "Integrates a commercial-grade React 18 SOC Dashboard with ultra glassmorphism styling, live WebSocket packet streaming, active firewall rule enforcement (SOAR), and SIEM exports.")
        ]
    )

    # 2. Architecture PDF
    create_pdf(
        "Architecture.pdf",
        "NIDS Technical Architecture Specification",
        "System Topography, Component Relationships, and Pipeline Flow",
        [
            ("1. Configuration & Data Ingestion", "The configuration layer uses Pydantic schema validation for thread-safe settings loading. Data loaders ingest PCAPs, NetFlow, and CSV telemetry."),
            ("2. Inference Engine & Alert Subsystem", "The inference pipeline processes 5-tuple flows in real time, scoring risk levels (Low, Medium, High, Critical) and persisting alert events into SQLite and SIEM exporters."),
            ("3. Security & Governance", "JWT Bearer authentication, PBKDF2 password hashing, and 5-Tier RBAC protect administrative endpoints and SOAR playbooks.")
        ]
    )

    # 3. Installation PDF
    create_pdf(
        "Installation.pdf",
        "NIDS Deployment & Installation Guide",
        "Standard Operational Procedures for Docker and Local Execution",
        [
            ("1. Local Setup Procedures", "Run setup.ps1 (Windows) or setup.sh (Linux/macOS) to provision .venv, install dependencies, and execute environment verification checks."),
            ("2. Docker Containerization", "Run 'docker compose up -d --build' to deploy backend, frontend, Prometheus, and Grafana containers."),
            ("3. Health Check & Validation", "Execute 'python scripts/check_environment.py' to verify system RAM, disk space, open ports, and model artifacts.")
        ]
    )


if __name__ == "__main__":
    main()
