"""The file set a gate scans: what git tracks, so a gate sees what a PR carries.

Shared by the vocabulary and untested-definition gates. `git ls-files` rather
than a tree walk, because .gitignore already answers "is this ours" and a walk
would re-answer it differently.

The one subprocess call in this repository: fixed argv, resolved executable,
no shell, and no caller-supplied argument.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path


def tracked_python(repo: Path) -> list[Path]:
    """Absolute paths of the .py files git tracks under `repo`."""
    git = shutil.which("git")
    if git is None:
        message = "git is not on PATH; the gate cannot determine what a PR carries"
        raise RuntimeError(message)
    listed = subprocess.run(  # nosec B603
        [git, "ls-files", "-z", "*.py"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    listed_paths = (repo / name for name in listed.stdout.split("\0") if name)
    # A tracked file can be absent mid-rebase or after an unstaged delete.
    # Scanning what is not there is a crash, not a finding.
    return [path for path in listed_paths if path.is_file()]
