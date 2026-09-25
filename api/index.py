"""
Vercel Serverless Entry Point for AegisOps FastAPI Backend.
"""
import sys
import os
from pathlib import Path

# Add project root directory to sys.path so backend and config modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Mark environment as Vercel
os.environ["VERCEL"] = "1"

from backend.main import app
