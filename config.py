import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Root directory
ROOT_DIR = Path(__file__).parent.absolute()

# Config parameters
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "local").lower()
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")

# Output Directories
OUTPUT_CHARTS_DIR = ROOT_DIR / "output_charts"
OUTPUT_PRES_DIR = ROOT_DIR / "output_presentations"
SAMPLE_DATA_DIR = ROOT_DIR / "sample_data"

# Create directories
OUTPUT_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PRES_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

def check_vllm_connection():
    """
    Checks if vLLM endpoint is reachable by querying the base endpoint.
    Returns:
        bool: True if reachable, False otherwise
    """
    if EXECUTION_MODE == "local":
        return False
        
    try:
        # vLLM usually serves models list at vLLM_BASE_URL/models
        # For OpenAI compatible endpoints, it's v1/models
        url = VLLM_BASE_URL.rstrip("/") + "/models"
        # 2-second timeout so it doesn't hang UI
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as response:
            if response.status == 200:
                return True
    except Exception:
        pass
    return False

# Detect active status
VLLM_ACTIVE = check_vllm_connection()
