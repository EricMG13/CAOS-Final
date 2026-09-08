"""Draft, render, validate, and exclusively publish one CP-MEMO DOCX."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path

from .domain import BuildResult
from .fidelity import validate_fidelity
from .inventory import inventory_snapshot
from .planner import plan_report
from .render_pdf import render_to_pages
from .renderer import render_docx, set_rendered_page_count
from .validator import validate_docx

ISSUER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TARGET_RE = re.compile(r"^(?P<issuer>[A-Za-z0-9][A-Za-z0-9.-]*)_CP-MEMO_(?P<date>\d{8})\.docx$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _publish_exclusive(source: Path, destination: Path) -> None:
    """Copy to a newly-created inode so later draft mutation cannot affect output."""
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with source.open("rb") as reader, os.fdopen(descriptor, "wb") as writer:
            shutil.copyfileobj(reader, writer, 1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
    except BaseException:
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
        raise


def _rerender_without_stale_pages(
    draft: Path,
    workspace: Path,
    previous_pdf: Path,
    previous_pages: tuple[Path, ...],
) -> tuple[Path, tuple[Path, ...], int]:
    previous_pdf.unlink(missing_ok=True)
    for page in previous_pages:
        page.unlink(missing_ok=True)
    return render_to_pages(draft, workspace)


def build_draft(snapshot: dict, catalog: dict, authority_digest: str, output_dir: Path, publication_date: str, confidentiality_label: str = "Confidential", requested_run_id: str | None = None) -> BuildResult:
    if not isinstance(publication_date, str) or not DATE_RE.fullmatch(publication_date):
        return BuildResult("BLOCKED", message="publication_date must be YYYY-MM-DD")
    try:
        date.fromisoformat(publication_date)
    except ValueError:
        return BuildResult("BLOCKED", message="publication_date is not a valid calendar date")
    if not isinstance(confidentiality_label, str) or not confidentiality_label.strip() or len(confidentiality_label) > 80 or not confidentiality_label.isprintable():
        return BuildResult("BLOCKED", message="confidentiality label must be one non-empty line of at most 80 characters")
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = inventory_snapshot(snapshot, catalog, authority_digest, requested_run_id)
    if inventory.status != "READY" or inventory.anchor is None:
        return BuildResult("BLOCKED", message=inventory.message or inventory.status)
    if not ISSUER_RE.fullmatch(inventory.anchor.issuer_id):
        return BuildResult("BLOCKED", message="issuer_id is unsafe for publication filename")
    target = output_dir / f"{inventory.anchor.issuer_id}_CP-MEMO_{publication_date.replace('-', '')}.docx"
    if target.exists():
        return BuildResult("COLLISION", output_path=str(target), message="target report already exists")
    spec = plan_report(inventory, publication_date, confidentiality_label)
    validate_fidelity(spec)
    workspace = Path(tempfile.mkdtemp(prefix=".cp-memo-", dir=output_dir))
    try:
        draft = workspace / "draft.docx"
        render_docx(spec, draft)
        pdf, pages, inserted_count = render_to_pages(draft, workspace)
        set_rendered_page_count(draft, inserted_count)
        pdf, pages, final_count = _rerender_without_stale_pages(draft, workspace, pdf, pages)
        if final_count != inserted_count:
            set_rendered_page_count(draft, final_count)
            pdf, pages, converged_count = _rerender_without_stale_pages(draft, workspace, pdf, pages)
            if converged_count != final_count:
                raise ValueError("rendered page count did not converge after updating the DOCX")
            final_count = converged_count
        validate_docx(draft, expected_page_count=final_count)
        draft_sha256 = _sha256(draft)
        session = workspace / "session.json"
        _write_json(session, {
            "schema_version": "1.0",
            "draft": str(draft),
            "draft_sha256": draft_sha256,
            "output": str(target),
            "output_dir": str(output_dir),
            "page_count": final_count,
            "pages": [str(page) for page in pages],
            "visual_approval_required": True,
        })
        return BuildResult("DRAFT_READY", session_path=str(session), output_path=str(target), page_count=final_count, sha256=draft_sha256, message="inspect every rendered page before publication")
    except BaseException:
        shutil.rmtree(workspace, ignore_errors=True)
        raise


def _safe_workspace(session: Path, output_dir: Path) -> Path:
    workspace = session.resolve().parent
    if session.name != "session.json" or workspace.parent != output_dir or not workspace.name.startswith(".cp-memo-") or workspace.is_symlink():
        raise ValueError("session path is outside a CP-MEMO temporary workspace")
    return workspace


def _validate_session_render(payload: dict, workspace: Path) -> int:
    page_count = payload.get("page_count")
    pages = payload.get("pages")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        raise ValueError("session page_count is invalid")
    if not isinstance(pages, list) or len(pages) != page_count or not all(isinstance(item, str) for item in pages):
        raise ValueError("session page inventory does not match page_count")
    workspace = workspace.resolve()
    render_dir = workspace / "render"
    if render_dir.is_symlink() or not render_dir.is_dir() or render_dir.resolve() != render_dir:
        raise ValueError("session render directory is missing, unsafe, or outside the workspace")
    expected_pages = tuple(
        render_dir / f"page-{number:0{len(str(page_count))}d}.png"
        for number in range(1, page_count + 1)
    )
    if set(render_dir.glob("page-*.png")) != set(expected_pages):
        raise ValueError("session rendered page inventory is incomplete or contains extras")
    for declared, expected in zip(map(Path, pages), expected_pages):
        if declared != expected or expected.is_symlink() or expected.resolve() != expected or not expected.is_file() or expected.stat().st_size == 0:
            raise ValueError("session contains an invalid rendered page")
    pdf = render_dir / "draft.pdf"
    if pdf.is_symlink() or pdf.resolve() != pdf or not pdf.is_file() or pdf.stat().st_size == 0:
        raise ValueError("session rendered PDF is missing, empty, or unsafe")
    return page_count


def publish_draft(session_path: Path, visual_approved: bool) -> BuildResult:
    if not visual_approved:
        return BuildResult("BLOCKED", session_path=str(session_path), message="visual page inspection has not been approved")
    session_path = session_path.resolve()
    payload = json.loads(session_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise ValueError("unsupported session record")
    output_dir = Path(payload["output_dir"]).resolve()
    workspace = _safe_workspace(session_path, output_dir)
    draft = Path(payload["draft"]).resolve()
    destination = Path(payload["output"]).resolve()
    if draft.parent != workspace or destination.parent != output_dir:
        raise ValueError("session paths are inconsistent")
    target_match = TARGET_RE.fullmatch(destination.name)
    if target_match is None or not ISSUER_RE.fullmatch(target_match.group("issuer")):
        raise ValueError("session output filename is not a canonical CP-MEMO target")
    date_token = target_match.group("date")
    try:
        date.fromisoformat(f"{date_token[:4]}-{date_token[4:6]}-{date_token[6:]}")
    except ValueError as exc:
        raise ValueError("session output filename has an invalid publication date") from exc
    page_count = _validate_session_render(payload, workspace)
    if _sha256(draft) != payload.get("draft_sha256"):
        raise ValueError("draft changed after validation")
    validate_docx(draft, expected_page_count=page_count)
    try:
        _publish_exclusive(draft, destination)
    except FileExistsError:
        return BuildResult("COLLISION", session_path=str(session_path), output_path=str(destination), message="target report already exists")
    try:
        if _sha256(destination) != payload.get("draft_sha256"):
            raise ValueError("published report bytes do not match the approved draft")
        validate_docx(destination, expected_page_count=page_count)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    result = BuildResult("PUBLISHED", output_path=str(destination), page_count=page_count, sha256=_sha256(destination))
    shutil.rmtree(workspace)
    return result
