"""
Main Entry Point for CortexAgent.exe Desktop Platform.
Executed by PyInstaller to run the desktop application window without opening a terminal window.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure all pipeline transformer modules are statically imported for PyInstaller / joblib unpickling
import src.encoding
import src.preprocessing
import src.scaling
import src.feature_selection
import src.data_loader
import src.data_validator
import src.evaluator
import src.predictor
import src.model_loader
import src.inference_pipeline
import src.prediction_service
import src.alert_engine
import src.packet_capture
import src.flow_builder

from agent.cortex_agent import launch_cortex_agent

if __name__ == "__main__":
    launch_cortex_agent()
