import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import and execute main from backend scripts
from scripts.run_rag_threshold_sweep import main

if __name__ == "__main__":
    main()
