"""
Run the Tools Web Service with uvicorn. Use from Docker or local.
"""
import os
import sys
from pathlib import Path

# Ensure app package is found when run as python run.py from webservice dir
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        log_level="info",
    )
