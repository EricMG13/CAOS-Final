"""Import paths for the test suite."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# The gate scripts are executables, not a package; import them by path.
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
