"""The third reviewer reads this repository with weights of its own, unasked.

`docs/AI_CODE_QUALITY.md` section 2 counts three reviewers. Two of them --
`confidence-review` and `adversarial-reviewer` -- are the same model in two
postures, so the third is the only one that brings different weights. CodeRabbit
could not be that here: it declined every pull request in this repository, for
one reason or another, and the ask could not be automated.

SonarQube Cloud analyses this repository automatically, from its own side of the
GitHub App, and posts the `SonarCloud Code Analysis` check. None of that lives in
this tree, so what these tests can hold is the shape of the tree around it -- and
the one way to break it from here, which is to commit the scanner configuration
that automatic analysis forbids. See `docs/DECISIONS.md` section 31.

Invariant protected: the review control in `docs/AI_CODE_QUALITY.md` section 2
is enforced by a tool rather than by whoever remembers to ask for it.
"""

from __future__ import annotations

import re
from pathlib import Path

from tracked import tracked_python

REPO = Path(__file__).resolve().parents[1]
PROPERTIES = REPO / ".sonarcloud.properties"
MAKEFILE = (REPO / "Makefile").read_text(encoding="utf-8")
PYPROJECT = (REPO / "pyproject.toml").read_text(encoding="utf-8")
DEFINITIONS = sorted((REPO / ".github" / "workflows").glob("*.yml"))
CI = "\n".join(path.read_text(encoding="utf-8") for path in DEFINITIONS)
QUALITY = (REPO / "docs" / "AI_CODE_QUALITY.md").read_text(encoding="utf-8")

USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)
# `owner/name@<40 hex>` is the only pinned form: a tag moves, a digest does not.
PINNED = re.compile(r"^[^@]+@[0-9a-f]{40}$")

# Every way this repository could start a scanner of its own. Any one of them
# turns the analysis that currently runs into a failing build -- see
# `test_nothing_here_starts_a_scanner_of_its_own` for why.
SCANNER = (
    "sonarqube-scan-action",
    "sonarcloud-github-action",
    "sonar-scanner",
    "sonarsource/sonarqube-quality-gate-action",
    "SONAR_TOKEN",
)


def analysis_properties() -> dict[str, str]:
    """`.sonarcloud.properties` as a mapping, comments and blanks dropped."""
    values: dict[str, str] = {}
    for line in PROPERTIES.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def declared(key: str) -> set[str]:
    """One comma-separated analysis property, as a set of entries."""
    return {entry.strip() for entry in analysis_properties()[key].split(",") if entry}


def make_variable(name: str) -> set[str]:
    """A `NAME := a b c` assignment from the Makefile, as a set of words."""
    found = re.search(rf"^{name} := (.+)$", MAKEFILE, re.M)
    assert found is not None, f"the Makefile no longer declares {name}"
    return set(found.group(1).split())


def test_the_repository_carries_no_coderabbit_configuration() -> None:
    """The replaced reviewer leaves no config behind to be read by nothing."""
    assert not (REPO / ".coderabbit.yaml").exists()


def test_nothing_here_starts_a_scanner_of_its_own() -> None:
    """Automatic analysis and a CI scanner are mutually exclusive.

    With automatic analysis on -- which is how this repository is analysed --
    running a scanner against the same project fails, and fails the build with
    it. So a `sonarqube` job is not a stronger gate than the analysis already
    running; it is the one commit that would stop it. `sonar-project.properties`
    is the scanner's own configuration file and is ignored by automatic
    analysis, so it too is a file that does nothing except invite the job.
    """
    assert not (REPO / "sonar-project.properties").exists(), (
        "sonar-project.properties configures the scanner CLI, which cannot run "
        "against a project under automatic analysis; see DECISIONS.md section 31"
    )
    found = sorted(token for token in SCANNER if token.lower() in CI.lower())
    assert found == [], (
        f"a CI job would start a second analysis ({found}), which fails against "
        "a project under automatic analysis; see DECISIONS.md section 31"
    )


def test_the_vendored_bundle_is_excluded_from_the_analysis() -> None:
    """A finding under `vendor/` names something no pull request may fix (6)."""
    declared = (REPO / ".sonarcloud.properties").read_text(encoding="utf-8")
    assert "sonar.exclusions=vendor/**" in declared
    assert next(REPO.glob("vendor/**/*.py"), None) is not None


def test_every_action_the_ci_uses_is_pinned_to_a_commit_digest() -> None:
    """A reviewer that is a third-party action would be a third-party risk."""
    assert DEFINITIONS, "no CI definitions found: the .github tree changed shape"
    used = USES.findall(CI)
    assert used, "no actions found: the CI definition must have changed shape"
    assert sorted(u for u in used if not PINNED.match(u)) == []


def test_the_review_control_names_the_tool_that_reads_the_repository() -> None:
    """The document cannot claim a third reviewer the repository does not have."""
    section = QUALITY[QUALITY.index("### Review") : QUALITY.index("## 3.")]
    assert "SonarQube" in section
    assert "SonarCloud Code Analysis" in section, (
        "the document must name the check the analysis actually posts, since "
        "that check is the only place this control is visible"
    )


def test_the_analysis_is_told_which_files_are_tests() -> None:
    """Otherwise production rules are skipped on anything that looks like one.

    SonarPython detects test-shaped files on its own and, with `sonar.tests`
    unset, declines to run production rules on them rather than guessing -- so
    29 files were analysed under neither rule set. It said so in the project's
    analysis warnings, which is the only place it could.
    """
    assert declared("sonar.tests") == {"tests"}


def test_the_analysis_is_told_which_python_it_is_reading() -> None:
    """Unset, every rule is evaluated against all of Python 3 at once.

    The repository is 3.14 only (`docs/DECISIONS.md` §10), so an analysis
    hedging across 3.0 upward is weaker on both ends: it misses what is now an
    error and reports what is now fine.
    """
    version = analysis_properties()["sonar.python.version"]
    found = re.search(r'^python_version = "([^"]+)"$', PYPROJECT, re.M)
    assert found is not None, "pyproject.toml no longer pins a mypy python_version"
    assert version == found.group(1), (
        f"the analysis reads Python {version}; the type gate reads {found.group(1)}"
    )


def test_the_analysis_claims_every_tracked_python_file() -> None:
    """Between sources and tests, nothing this repository wrote goes unclaimed.

    The floor `docs/AI_CODE_QUALITY.md` §4 holds bandit to, stated for this
    analysis too: a package a later phase adds cannot go unread without
    somebody saying so.
    """
    claimed = declared("sonar.sources") | declared("sonar.tests")
    tracked = (path.relative_to(REPO) for path in tracked_python(REPO))
    unclaimed = sorted(
        str(path)
        for path in tracked
        if not any(path.is_relative_to(claim) for claim in claimed)
    )
    assert unclaimed == [], f"files no analysis property claims: {unclaimed}"


def test_the_analysis_covers_everything_the_sast_gate_covers() -> None:
    """Containment, not equality: what bandit is pointed at, this reads too.

    Equality would refuse a `frontend` in `sonar.sources`, which bandit has no
    business scanning -- so the property is that nothing bandit reads can slip
    out of this analysis, not that the two lists stay identical forever.
    """
    assert make_variable("SEC_TARGETS") <= declared("sonar.sources")
    assert make_variable("SEC_UNSCANNED") <= declared("sonar.tests")
