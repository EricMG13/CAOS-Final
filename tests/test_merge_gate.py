"""`make merge` must refuse before it can ever reach `gh pr merge`.

The target is a convenience -- docs/DECISIONS.md section 14 makes the `main`
ruleset the real gate -- but it drives an irreversible action from a shell
variable, and it merged PR #6 during an earlier session because nothing here
watched it. Every case runs against a stub `gh` on PATH that refuses `pr merge`
outright, so a regression fails the suite instead of merging a pull request.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Records what the target asked of `gh`, answers `pr view` with a fixed head,
# and refuses `pr merge` so that no test can reach a real pull request.
STUB_GH = """#!/bin/sh
if [ "$1" = "--version" ]; then
    echo "gh version ${STUB_GH_VERSION} (2026-09-03)"
    exit 0
fi
if [ "$1 $2 $3" = "pr merge --help" ]; then
    [ "${STUB_GH_MATCH_FLAG}" = "yes" ] && echo "  --match-head-commit SHA"
    exit 0
fi
echo "$@" >> "${STUB_GH_LOG}"
case "$1 $2" in
"pr view") echo deadbeef ;;
"pr checks") ;;
"pr merge") echo "stub refused pr merge" >&2 ; exit 99 ;;
esac
"""

REFUSED_PR_VALUES = ["", "abc", "6x", "01", "1; echo PWNED", '" ; echo PWNED ; "']


class _Attempt:
    """One `make merge` run and the `gh` calls it made."""

    def __init__(self, run: subprocess.CompletedProcess[str], calls: list[str]) -> None:
        self.run = run
        self.calls = calls

    @property
    def output(self) -> str:
        return self.run.stdout + self.run.stderr


def _merge(
    tmp_path: Path,
    pr: str,
    *,
    gh_version: str = "2.100.0",
    match_flag: str = "yes",
) -> _Attempt:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub = stub_dir / "gh"
    stub.write_text(STUB_GH, encoding="utf-8")
    stub.chmod(0o755)
    log = tmp_path / "gh-calls.log"
    log.write_text("", encoding="utf-8")

    run = subprocess.run(
        ["make", "merge", f"PR={pr}"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        env={
            # The stub shadows any real gh; make and sh come from the system.
            # The env deliberately carries no HOME, GH_TOKEN or GITHUB_TOKEN, so
            # a real gh reached by mistake could not authenticate, let alone
            # merge. Do not add them.
            "PATH": f"{stub_dir}:/usr/bin:/bin",
            "STUB_GH_VERSION": gh_version,
            "STUB_GH_MATCH_FLAG": match_flag,
            "STUB_GH_LOG": str(log),
        },
    )
    calls = [line for line in log.read_text(encoding="utf-8").splitlines() if line]
    return _Attempt(run, calls)


@pytest.mark.parametrize("pr", REFUSED_PR_VALUES)
def test_refuses_a_pr_that_is_not_a_number(tmp_path: Path, pr: str) -> None:
    """A crafted PR value never reaches `gh`, and never reaches a shell."""
    attempt = _merge(tmp_path, pr)

    assert attempt.run.returncode != 0
    assert "usage: make merge PR=<number>" in attempt.output
    assert "PWNED" not in attempt.output
    assert attempt.calls == []


def test_refuses_a_gh_that_cannot_pin_the_head_commit(tmp_path: Path) -> None:
    """Without --match-head-commit the merge is unpinned, so it must not run."""
    attempt = _merge(tmp_path, "6", match_flag="no")

    assert attempt.run.returncode != 0
    assert not any(call.startswith("pr merge") for call in attempt.calls)


@pytest.mark.parametrize("gh_version", ["2.100.0", "2.101.0", "3.0.0"])
def test_any_gh_carrying_the_flag_checks_then_merges_the_pinned_head(
    tmp_path: Path, gh_version: str
) -> None:
    """The flag is the requirement; a newer gh must not fail the target."""
    attempt = _merge(tmp_path, "6", gh_version=gh_version)

    assert attempt.calls == [
        "pr view 6 --json headRefOid --jq .headRefOid",
        "pr checks 6",
        "pr merge 6 --merge --match-head-commit deadbeef",
    ]
