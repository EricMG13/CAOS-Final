"""The third reviewer reads this repository with weights of its own, unasked.

`docs/AI_CODE_QUALITY.md` section 2 counts three reviewers. Two of them --
`confidence-review` and `adversarial-reviewer` -- are the same model in two
postures, so the third is the only one that brings different weights. CodeRabbit
could not be that here: it declined every pull request in this repository, for
one reason or another, and the ask could not be automated.

SonarQube Cloud is the third, and as of `docs/DECISIONS.md` section 41 it is
submitted from CI rather than read from SonarQube Cloud's own side. Section 31
chose the opposite and gave a good reason -- an analysis unreachable from a
commit cannot be narrowed by the agent whose code it reads. What overrode it is
that automatic analysis imports no coverage report, so the coverage the quality
gate judges could not exist under it at all.

That trade is the subject of most of this file. The configuration is now in the
tree and therefore editable in the same pull request it reviews, so what these
tests hold is the scope: every tracked file claimed, the bundle excluded, the
coverage report accounted for, and the secret exemption beside it scoped to one
string rather than to the file it sits in.

Invariant protected: the review control in `docs/AI_CODE_QUALITY.md` section 2
is enforced by a tool rather than by whoever remembers to ask for it.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from tracked import tracked_python

REPO = Path(__file__).resolve().parents[1]
PROPERTIES = REPO / "sonar-project.properties"
GITLEAKS = REPO / ".gitleaks.toml"
MAKEFILE = (REPO / "Makefile").read_text(encoding="utf-8")
PYPROJECT = (REPO / "pyproject.toml").read_text(encoding="utf-8")
DEFINITIONS = sorted((REPO / ".github" / "workflows").glob("*.yml"))
CI = "\n".join(path.read_text(encoding="utf-8") for path in DEFINITIONS)
QUALITY = (REPO / "docs" / "AI_CODE_QUALITY.md").read_text(encoding="utf-8")

JOB = re.compile(r"^  ([a-z][a-z0-9-]*):$", re.M)
USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)
# `owner/name@<40 hex>` is the only pinned form: a tag moves, a digest does not.
PINNED = re.compile(r"^[^@]+@[0-9a-f]{40}$")

# The Actions jobs the `main gates` ruleset requires (docs/DECISIONS.md §34).
# A required check is matched by name: rename the job and it never reports, and
# a check that never reports blocks every merge -- §14's own hazard, from the
# other end. `SonarCloud Code Analysis` is absent because no job posts it: the
# `sonarqube` job submits the analysis, and SonarQube Cloud's GitHub App posts
# the check that carries the verdict. `sonarqube` itself is absent because the
# ruleset does not require it yet (§41), and this list states the ruleset.
REQUIRED_JOBS = frozenset({"lint", "types", "test", "postgres", "security", "size"})

# The action that submits the analysis. `sonarcloud-github-action` is its
# predecessor under the old branding and is not what this repository runs.
SCAN_ACTION = "sonarsource/sonarqube-scan-action"


def analysis_properties() -> dict[str, str]:
    """`sonar-project.properties` as a mapping, comments and blanks dropped."""
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


def test_exactly_one_job_submits_the_analysis() -> None:
    """Two scanners against one project is the failure §31 recorded, inverted.

    Automatic analysis and a CI scanner are mutually exclusive, and so are two
    CI scanners on the same commit: the second run fails and fails the build
    with it. Under §31 the safe count was zero, because the analysis came from
    SonarQube Cloud's side. Under §41 it is exactly one, and the file that
    configures it has to exist rather than be refused.
    """
    assert PROPERTIES.exists(), (
        "sonar-project.properties is what the scanner reads; without it the "
        "analysis has no project key, no sources and no coverage report"
    )
    submissions = CI.lower().count(SCAN_ACTION)
    assert submissions == 1, (
        f"{submissions} jobs submit an analysis; one project takes one scan per "
        "commit, and a second run fails and fails the build with it"
    )


def test_the_analysis_runs_when_a_draft_is_marked_ready() -> None:
    """A draft pull request got an analysis before §41 and must still get one.

    Automatic analysis did not know whether a pull request was a draft. A CI
    analysis does: no `pull_request` run was created for the draft that carried
    §41, over five pushes, so `sonarqube` was skipped every time -- and marking
    it ready does not start one either, because `ready_for_review` is not a
    default activity type. Hence declared rather than defaulted.
    """
    triggers = re.search(r"^on:\n(?:  .*\n|    .*\n|      .*\n)+", CI, re.M)
    assert triggers is not None, "the workflow no longer declares `on:` as a block"
    assert "ready_for_review" in triggers.group(0), (
        "converting a draft to ready posts no analysis: `ready_for_review` is "
        "not a default pull_request activity type, and a draft gets no run"
    )


def test_one_analysis_configuration_exists_and_the_scanner_reads_it() -> None:
    """The switch-over is done, so the file automatic analysis read is gone.

    It was kept for one transition, because a file automatic analysis reads is
    not dead until automatic analysis is switched off -- a setting, not a
    commit. That is done and the `sonarqube` job is confirmed posting the check,
    so what is left would configure nothing and drift against the file that
    does. Its drift test went with it rather than staying as a check whose only
    branch is an early return.
    """
    assert not (REPO / ".sonarcloud.properties").exists(), (
        "automatic analysis is off (docs/DECISIONS.md §41), so this file is read "
        "by nothing while still claiming a scope the scanner's file also claims"
    )


def test_the_analysis_imports_the_coverage_report_the_suite_writes() -> None:
    """The whole reason the analysis moved into CI (§41).

    Two ways this silently becomes a no-op: the scanner is told a path the suite
    does not write, or the suite stops writing one. Neither is visible in the
    check, which reports missing coverage as 0.0% rather than as an error, so
    the two declarations are pinned to each other here.
    """
    declared_path = analysis_properties()["sonar.python.coverage.reportPaths"]
    written = re.search(r'^output = "([^"]+)"$', PYPROJECT, re.M)
    assert written is not None, "pyproject.toml no longer sets a coverage xml output"
    assert declared_path == written.group(1), (
        f"the analysis reads {declared_path}; the suite writes {written.group(1)}"
    )
    assert "--cov" in PYPROJECT, (
        "the coverage flags live in addopts so that a local run and the CI run "
        "produce the same report; without them the job uploads nothing"
    )


def test_the_coverage_floor_measures_what_the_analysis_reads() -> None:
    """A report that skipped a file raises the percentage of everything else.

    `scan_floors.py --cobertura` refuses that, and it can only refuse it against
    the right list: the directories the analysis reads, not the ones the SAST
    gate happens to share with them today.
    """
    assert make_variable("COV_TARGETS") == declared("sonar.sources")
    assert make_variable("COV_UNSCANNED") == declared("sonar.tests")
    assert "--cobertura" in CI, "the CI run does not apply the coverage floor"


def test_the_secret_exemption_names_a_string_rather_than_a_file() -> None:
    """gitleaks reads `sonar.projectKey` as a credential; it is an identifier.

    The exemption that says so is the one place in this repository where a
    scanner is told to ignore something, so its scope is the whole question. A
    `paths` or `files` clause would stop gitleaks reading
    sonar-project.properties at all, and a real credential pasted into that file
    later would be the one thing nothing here scans.

    The expected value is read from the properties file rather than written out
    here, for the reason this test is about: spelling the key in this file makes
    *this* file the thing gitleaks flags, and exempting it too would spread the
    exemption rather than hold it.
    """
    allowlist = tomllib.loads(GITLEAKS.read_text(encoding="utf-8"))["allowlist"]
    assert set(allowlist) & {"paths", "files", "commits"} == set(), (
        f"the exemption is scoped by {sorted(allowlist)}; scoping it by path "
        "exempts every future secret in that file too"
    )
    key = analysis_properties()["sonar.projectKey"]
    assert allowlist["regexes"] == [rf"sonar\.projectKey={key}"], (
        "the exemption does not name the project key this analysis declares, so "
        "either it exempts something else or the gate is red on the real one"
    )
    assert allowlist["regexTarget"] == "match"


def test_the_vendored_bundle_is_excluded_from_the_analysis() -> None:
    """A finding under `vendor/` names something no pull request may fix (6)."""
    assert "sonar.exclusions=vendor/**" in PROPERTIES.read_text(encoding="utf-8")
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


def test_every_required_check_is_a_job_the_ci_still_defines() -> None:
    """A renamed job does not fail the ruleset; it stops reporting to it.

    `docs/DECISIONS.md` §14 names the hazard from one end -- a required check
    that never reports blocks every merge -- and §34 fixes the set. This is the
    other end: the rename that quietly makes a required check unreportable.
    """
    defined = {match.group(1) for match in JOB.finditer(CI)}
    assert defined, "no jobs found: the CI definition must have changed shape"
    missing = sorted(REQUIRED_JOBS - defined)
    assert missing == [], (
        f"the ruleset requires checks no CI job posts: {missing}; "
        "renaming a required job blocks every merge until the ruleset follows"
    )
