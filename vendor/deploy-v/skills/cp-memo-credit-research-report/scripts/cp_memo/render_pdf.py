"""Headless DOCX rendering for structural and visual QA."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader


class RenderError(RuntimeError):
    pass


def _executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RenderError(f"required executable is unavailable: {name}")
    return path


def _page_number(path: Path) -> int:
    try:
        return int(path.stem.rsplit("-", 1)[1])
    except (IndexError, ValueError) as exc:
        raise RenderError(f"unexpected rendered page filename: {path.name}") from exc


def render_to_pages(docx_path: Path, workspace: Path) -> tuple[Path, tuple[Path, ...], int]:
    soffice = _executable("soffice")
    pdftoppm = _executable("pdftoppm")
    pdf_dir = workspace / "render"
    profile = workspace / "lo-profile"
    pdf_dir.mkdir(exist_ok=True)
    profile.mkdir(exist_ok=True)
    pdf_path = pdf_dir / f"{docx_path.stem}.pdf"
    pdf_path.unlink(missing_ok=True)
    for stale_page in pdf_dir.glob("page-*.png"):
        stale_page.unlink()
    profile_uri = profile.resolve().as_uri()
    env = os.environ.copy()
    runtime_temp = tempfile.gettempdir()
    env.update({"TMPDIR": runtime_temp, "TEMP": runtime_temp, "TMP": runtime_temp})
    command = [
        soffice,
        "--headless",
        f"-env:UserInstallation={profile_uri}",
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        str(pdf_dir),
        str(docx_path),
    ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120, env=env)
    if completed.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise RenderError(f"LibreOffice conversion failed: {completed.stderr.strip() or completed.stdout.strip()}")
    reader = PdfReader(str(pdf_path))
    count = len(reader.pages)
    if count < 1:
        raise RenderError("rendered PDF has no pages")
    prefix = pdf_dir / "page"
    raster = subprocess.run([pdftoppm, "-png", "-r", "144", str(pdf_path), str(prefix)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    pages = tuple(sorted(pdf_dir.glob("page-*.png"), key=_page_number))
    if raster.returncode != 0 or len(pages) != count or any(page.stat().st_size == 0 for page in pages):
        raise RenderError(f"PDF rasterization failed: {raster.stderr.strip()}")
    return pdf_path, pages, count
