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
that automatic analysis forbids. See `docs/DECISIONS.md` section 30.

Invariant protected: the review control in `docs/AI_CODE_QUALITY.md` section 2
is enforced by a tool rather than by whoever remembers to ask for it.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
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
        "against a project under automatic analysis; see DECISIONS.md section 30"
    )
    found = sorted(token for token in SCANNER if token.lower() in CI.lower())
    assert found == [], (
        f"a CI job would start a second analysis ({found}), which fails against "
        "a project under automatic analysis; see DECISIONS.md section 30"
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
