"""Deploy V profile-aware CREDIT OS runtime.

This package is intentionally separate from :mod:`tools.credit_os`.  Deploy B
continues to ship its frozen runtime; Deploy V opts into this adapter through an
explicit package specification.
"""

import sys
from pathlib import Path

# Repository layout is tools/{credit_os,credit_os_v}; installed layout is
# scripts/{credit_os,credit_os_v}. Adding their shared parent makes the same
# import-clean module names work in both places.
_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
if str(_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_ROOT))

from .identity import FULL_PROFILE, LITE_PROFILE, PROFILE_IDS

__all__ = ["FULL_PROFILE", "LITE_PROFILE", "PROFILE_IDS"]
