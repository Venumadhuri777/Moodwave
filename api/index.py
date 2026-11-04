import os
import sys
from pathlib import Path

# Add project root and backend directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for p in [str(BACKEND_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set environment variables for serverless execution
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    os.environ.setdefault("DATA_DIR", str(PROJECT_ROOT / "data" / "processed"))
    os.environ.setdefault("FEEDBACK_DB_PATH", "/tmp/feedback.db")
    os.environ.setdefault("FRONTEND_DIR", str(PROJECT_ROOT / "frontend"))
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

from app.main import app, init_app_state

# Ensure backend stores and indexes are initialized even if lifespan is skipped in serverless
init_app_state(app)

# Vercel Serverless Function entrypoint
app = app
