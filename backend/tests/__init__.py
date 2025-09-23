import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / 'app'
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
