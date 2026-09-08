"""Governed DOCX renderer for the editorial report specification."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from .domain import ReportBlock, ReportSpec

CONTENT_WIDTH_DXA = 9360
BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
MUTED = RGBColor(89, 98, 108)


def _set_run_font(run, name: str = "Calibri", size: float | None = None, bold: bool | None = None, color=None) -> None:
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def _set_cell_margins(cell, top=80, start=120, bottom=80, end=120) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    tr_pr.append(marker)


def _prevent_row_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:cantSplit")
    marker.set(qn("w:val"), "true")
    tr_pr.append(marker)


def _fixed_table_geometry(table, widths: list[int]) -> None:
    if not widths or sum(widths) != CONTENT_WIDTH_DXA:
        raise ValueError("table widths must sum to 9360 DXA")
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(CONTENT_WIDTH_DXA))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths[index]))
            tc_w.set(qn("w:type"), "dxa")
            _set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def _page_field(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction, separate, placeholder, end))


def _styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.10
    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 16, 8),
        ("Heading 2", 13, BLUE, 12, 6),
        ("Heading 3", 12, DARK_BLUE, 8, 4),
    ):
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
    bullet = doc.styles["List Bullet"]
    bullet.font.name = "Calibri"
    bullet.font.size = Pt(11)
    bullet.paragraph_format.space_after = Pt(8)
    bullet.paragraph_format.line_spacing = 1.167


def _section_geometry(section) -> None:
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.right_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)


def _header_footer(section, spec: ReportSpec) -> None:
    section.different_first_page_header_footer = True
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(f"{spec.anchor.issuer_name}  |  {spec.anchor.reporting_period}  |  As of {spec.anchor.analysis_date}")
    _set_run_font(run, size=8.5, color=MUTED)
    footer = section.footer
    table = footer.add_table(rows=1, cols=2, width=Inches(6.5))
    table.autofit = False
    left, right = table.rows[0].cells
    left_p = left.paragraphs[0]
    left_run = left_p.add_run(spec.confidentiality_label)
    _set_run_font(left_run, size=8, color=MUTED)
    right_p = right.paragraphs[0]
    right_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right_run = right_p.add_run("Page ")
    _set_run_font(right_run, size=8, color=MUTED)
    _page_field(right_p)
    _fixed_table_geometry(table, [7000, 2360])


def _cover(doc: Document, spec: ReportSpec) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(110)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    kicker = p.add_run("CREDIT RESEARCH REPORT")
    _set_run_font(kicker, size=10, bold=True, color=BLUE)
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(18)
    title.paragraph_format.space_after = Pt(8)
    run = title.add_run(spec.anchor.issuer_name)
    _set_run_font(run, size=28, bold=True, color=DARK_BLUE)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("CP-MEMO — CreditResearchReport")
    _set_run_font(run, size=15, color=BLUE)
    status = doc.add_paragraph()
    status.alignment = WD_ALIGN_PARAGRAPH.CENTER
    status.paragraph_format.space_before = Pt(24)
    run = status.add_run(spec.publication_status)
    _set_run_font(run, size=11, bold=True)
    facts = (
        ("Issuer ID", spec.anchor.issuer_id),
        ("Run", spec.anchor.run_id),
        ("Profile", spec.anchor.profile_id),
        ("Selection", spec.anchor.selection_id),
        ("Reporting period", spec.anchor.reporting_period),
        ("Analysis date", spec.anchor.analysis_date),
        ("Publication date", spec.publication_date),
    )
    table = doc.add_table(rows=len(facts), cols=2)
    for row, (label, value) in zip(table.rows, facts):
        label_run = row.cells[0].paragraphs[0].add_run(label)
        _set_run_font(label_run, size=9, bold=True, color=MUTED)
        value_run = row.cells[1].paragraphs[0].add_run(value)
        _set_run_font(value_run, size=9)
    _fixed_table_geometry(table, [2600, 6760])
    warning = doc.add_paragraph()
    warning.paragraph_format.space_before = Pt(22)
    warning.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = warning.add_run("Editorial consolidation only. No new credit analysis is performed by CP-MEMO — CreditResearchReport.")
    _set_run_font(run, size=9, color=MUTED)


def _render_block(doc: Document, block: ReportBlock) -> None:
    if block.kind == "table":
        if not block.rows:
            return
        columns = len(block.rows[0])
        if block.text == "Module provenance index" and columns == 4:
            widths = [2600, 1000, 2400, 3360]
        else:
            widths = [CONTENT_WIDTH_DXA // columns] * columns
            widths[-1] += CONTENT_WIDTH_DXA - sum(widths)
        table = doc.add_table(rows=len(block.rows), cols=columns)
        table.style = "Table Grid"
        for row_index, values in enumerate(block.rows):
            if len(values) != columns:
                raise ValueError("table rows have inconsistent column counts")
            for cell, value in zip(table.rows[row_index].cells, values):
                cell.text = value
                for run in cell.paragraphs[0].runs:
                    _set_run_font(run, size=8.5, bold=row_index == 0)
        _repeat_header(table.rows[0])
        for row in table.rows:
            _prevent_row_split(row)
        _fixed_table_geometry(table, widths)
        return
    style = "List Bullet" if block.kind == "bullet" else None
    p = doc.add_paragraph(style=style)
    if block.kind == "warning":
        label = p.add_run("Publication warning — ")
        _set_run_font(label, bold=True, color=RGBColor(155, 28, 28))
    run = p.add_run(block.text)
    _set_run_font(run)
    if block.source_note is not None:
        note = p.add_run(f" [{block.source_note}]")
        _set_run_font(note, size=8, color=BLUE)


def render_docx(spec: ReportSpec, path: Path) -> None:
    doc = Document()
    _styles(doc)
    for section in doc.sections:
        _section_geometry(section)
        _header_footer(section, spec)
    _cover(doc, spec)
    doc.add_page_break()
    for section in spec.sections:
        if section.title == "Module provenance index":
            doc.add_page_break()
        doc.add_heading(section.title, level=1)
        if not section.blocks:
            p = doc.add_paragraph("No eligible upstream finding was available for this section.")
            p.runs[0].italic = True
            _set_run_font(p.runs[0], color=MUTED)
        for block in section.blocks:
            _render_block(doc, block)
    if spec.source_notes:
        doc.add_page_break()
        doc.add_heading("Source Notes", level=1)
        for note in spec.source_notes:
            p = doc.add_paragraph()
            run = p.add_run(
                f"[{note.number}] {note.display}; {note.locator}; artifact {note.artifact_name}; SHA-256 {note.sha256}."
            )
            _set_run_font(run, size=8.5)
    doc.add_heading("Publication QA", level=2)
    p = doc.add_paragraph("Rendered page count: [[PAGE_COUNT]]. Page target: 10–15 pages (soft target).")
    _set_run_font(p.runs[0], size=9, color=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


def set_rendered_page_count(path: Path, count: int) -> None:
    doc = Document(path)
    found = False
    explanation = (
        " Within target."
        if 10 <= count <= 15
        else " Outside the soft target because fidelity and available upstream content take precedence."
    )
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("Rendered page count:"):
            paragraph.text = (
                f"Rendered page count: {count}. Page target: 10–15 pages (soft target)."
                + explanation
            )
            for run in paragraph.runs:
                _set_run_font(run, size=9, color=MUTED)
            found = True
    if not found:
        raise ValueError("rendered page-count placeholder is missing")
    doc.save(path)
