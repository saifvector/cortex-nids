"""
Main Entry Point for CortexAgent.exe Desktop Platform.
Executed by PyInstaller to run the desktop application window without opening a terminal window.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.cortex_agent import launch_cortex_agent

if __name__ == "__main__":
    launch_cortex_agent()
