import os
import sys
from pathlib import Path

# Add railway-data/scripts to sys.path so that internal module imports (optimizer, auth, etc.) resolve cleanly
scripts_path = Path(__file__).resolve().parent / "railway-data" / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from api import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
