"""
DOCX Builder — generates a professional compliance document package
matching the Yash-Technologies template format.

Sections per document:
  Cover Page → Revision History → Table of Contents
  → Part I Policies (grouped by framework)
  → Part II Procedures (grouped by framework)
"""

import io
from datetime import datetime
from typing import List, Optional

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ─── Colour palette ───────────────────────────────────────────────────────────
DARK_BLUE   = RGBColor(0x1F, 0x35, 0x64)   # header background / banner
MID_BLUE    = RGBColor(0x2E, 0x74, 0xB5)   # section headings
LIGHT_BLUE  = RGBColor(0xBD, 0xD7, 0xEE)   # table header fill
TABLE_FILL  = RGBColor(0xF2, 0xF2, 0xF2)   # alternate row fill
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT   = RGBColor(0x20, 0x20, 0x20)
GOLD        = RGBColor(0xFF, 0xC0, 0x00)   # accent / banner stripe


def _set_cell_bg(cell, rgb: RGBColor):
    """Set background colour on a table cell."""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    hex_str = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    shd.set(qn("w:fill"),  hex_str)
    tcPr.append(shd)


def _cell_text(cell, text: str, bold=False, size=10,
               colour: Optional[RGBColor] = None,
               align: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p   = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)
    if colour:
        run.font.color.rgb = colour


def _add_horizontal_rule(doc: Document):
    """Insert a thin horizontal line paragraph."""
    p    = doc.add_paragraph()
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "2E74B5")
    pBdr.append(bot)
    pPr.append(pBdr)
    p.paragraph_format.space_after  = Pt(2)
    p.paragraph_format.space_before = Pt(2)


def _build_cover_page(doc: Document, org_name: str, frameworks: List[str],
                      generated_date: str, author: str = "GRC AI Platform"):
    """Full cover page matching formal compliance document standards."""

    # ── Main banner title ─────────────────────────────────────────────────────
    banner = doc.add_paragraph()
    banner.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = banner.add_run("Compliance Documentation Package")
    run.bold = True
    run.font.size = Pt(30)
    run.font.color.rgb = DARK_BLUE
    banner.paragraph_format.space_before = Pt(48)
    banner.paragraph_format.space_after  = Pt(4)

    _add_horizontal_rule(doc)

    # Organisation name
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(org_name)
    r.bold = True
    r.font.size = Pt(24)
    r.font.color.rgb = MID_BLUE
    p.paragraph_format.space_after = Pt(2)

    # Framework line
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(f"Frameworks: {', '.join(frameworks)}")
    r2.font.size = Pt(13)
    r2.font.color.rgb = RGBColor(0x44, 0x72, 0xC4)
    p2.paragraph_format.space_after = Pt(2)

    _add_horizontal_rule(doc)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Confidentiality stamp
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("CONFIDENTIAL — INTERNAL USE ONLY")
    r3.bold = True
    r3.font.size = Pt(11)
    r3.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    p3.paragraph_format.space_after = Pt(16)

    # ── Document Attributes Table ─────────────────────────────────────────────
    attrs = [
        ("Document Title",         f"{org_name} — Compliance Policy & Procedure Package"),
        ("Document Type",          "Policy / Procedure Package"),
        ("Author",                 author),
        ("Owner (Business/Function)", "Compliance & Information Security"),
        ("Effective Date",         generated_date),
        ("Review Date",            f"Annual — due by {_next_year(generated_date)}"),
        ("Document Status",        "Approved"),
        ("Version",                "1.0"),
        ("Confidentiality",        "Internal — Confidential"),
        ("Framework(s)",           ", ".join(frameworks)),
    ]

    tbl = doc.add_table(rows=len(attrs), cols=2)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, (k, v) in enumerate(attrs):
        row = tbl.rows[i]
        _set_cell_bg(row.cells[0], LIGHT_BLUE)
        _cell_text(row.cells[0], k, bold=True, size=10, colour=DARK_BLUE)
        _cell_text(row.cells[1], v, size=10)
        # Alternate slight shading on value column
        if i % 2 == 0:
            _set_cell_bg(row.cells[1], RGBColor(0xFA, 0xFA, 0xFA))

    doc.add_page_break()


def _next_year(date_str: str) -> str:
    """Return same date next year, or 'one year from effective date'."""
    try:
        from datetime import datetime, timedelta
        d = datetime.strptime(date_str, "%d %B %Y")
        return (d.replace(year=d.year + 1)).strftime("%d %B %Y")
    except Exception:
        return "one year from effective date"


def _build_revision_history(doc: Document, policies: list, procedures: list):
    """Version Control / Revision History table — formal document register."""
    h = doc.add_heading("Version Control / Revision History", level=1)
    h.runs[0].font.color.rgb = DARK_BLUE

    # Intro paragraph
    intro = doc.add_paragraph(
        "This table tracks all versions of the documents contained in this compliance package. "
        "All changes must be reviewed and approved by the document owner before publication."
    )
    intro.paragraph_format.space_after = Pt(8)
    for r in intro.runs:
        r.font.size = Pt(10)

    # ── Version history for the package itself ────────────────────────────────
    vh_cols = ["Version", "Date", "Author", "Approver", "Description of Change"]
    vh_data = [
        ("1.0", datetime.now().strftime("%d %B %Y"), "GRC AI Platform",
         "Chief Information Security Officer", "Initial release — AI-generated compliance package"),
    ]

    vh_tbl = doc.add_table(rows=1 + len(vh_data), cols=len(vh_cols))
    vh_tbl.style = "Table Grid"

    hdr = vh_tbl.rows[0]
    for i, label in enumerate(vh_cols):
        _set_cell_bg(hdr.cells[i], DARK_BLUE)
        _cell_text(hdr.cells[i], label, bold=True, size=9,
                   colour=WHITE, align=WD_ALIGN_PARAGRAPH.CENTER)

    for ri, (ver, date, auth, appr, desc) in enumerate(vh_data):
        cells = vh_tbl.rows[ri + 1].cells
        _cell_text(cells[0], ver,  size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[1], date, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[2], auth, size=9)
        _cell_text(cells[3], appr, size=9)
        _cell_text(cells[4], desc, size=9)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ── Document Register (all policies + procedures) ─────────────────────────
    sh = doc.add_heading("Document Register", level=2)
    sh.runs[0].font.color.rgb = MID_BLUE

    cols = ["Document Title", "Document ID", "Type", "Framework",
            "Version", "Effective Date", "Review Date", "Owner", "Classification"]
    tbl = doc.add_table(rows=1 + len(policies) + len(procedures), cols=len(cols))
    tbl.style = "Table Grid"

    hdr2 = tbl.rows[0]
    for i, label in enumerate(cols):
        _set_cell_bg(hdr2.cells[i], LIGHT_BLUE)
        _cell_text(hdr2.cells[i], label, bold=True, size=8, colour=DARK_BLUE,
                   align=WD_ALIGN_PARAGRAPH.CENTER)

    row_idx = 1
    for p in policies:
        cells = tbl.rows[row_idx].cells
        if row_idx % 2 == 0:
            for c in cells: _set_cell_bg(c, TABLE_FILL)
        _cell_text(cells[0], p.get("title", ""),          size=8)
        _cell_text(cells[1], p.get("policy_id", ""),      size=8)
        _cell_text(cells[2], "Policy",                    size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[3], p.get("framework", ""),      size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[4], p.get("version", "1.0"),     size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[5], p.get("effective_date", ""), size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[6], p.get("review_date", ""),    size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[7], p.get("owner", ""),          size=8)
        _cell_text(cells[8], p.get("classification", "Internal"), size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        row_idx += 1

    for p in procedures:
        cells = tbl.rows[row_idx].cells
        if row_idx % 2 == 0:
            for c in cells: _set_cell_bg(c, TABLE_FILL)
        _cell_text(cells[0], p.get("title", ""),          size=8)
        _cell_text(cells[1], p.get("procedure_id", ""),   size=8)
        _cell_text(cells[2], "Procedure",                 size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[3], p.get("framework", ""),      size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[4], "1.0",                       size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[5], datetime.now().strftime("%Y-%m-%d"), size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_text(cells[6], "",                          size=8)
        _cell_text(cells[7], p.get("owner", ""),          size=8)
        _cell_text(cells[8], "Internal",                  size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        row_idx += 1

    doc.add_page_break()


def _build_toc_placeholder(doc: Document, policies: list, procedures: list):
    """Table of Contents — Word native TOC field (updates page numbers on open)."""
    h = doc.add_heading("Table of Contents", level=1)
    h.runs[0].font.color.rgb = DARK_BLUE

    # Style toc 1–4 for visual hierarchy
    for sn, sz, bd, col, ind, spb in [
        ("toc 1", 11, True,  "1F3564", 0.0, 10),
        ("toc 2", 10, False, "2E74B5", 0.2,  4),
        ("toc 3",  9, False, "4A5FA8", 0.4,  2),
    ]:
        try:
            st = doc.styles[sn]
            st.font.name = "Calibri"
            st.font.size = Pt(sz)
            st.font.bold = bd
            r, g, b = int(col[0:2],16), int(col[2:4],16), int(col[4:6],16)
            st.font.color.rgb = RGBColor(r, g, b)
            st.paragraph_format.left_indent  = Inches(ind)
            st.paragraph_format.space_before = Pt(spb)
            st.paragraph_format.space_after  = Pt(2)
        except Exception:
            pass

    # Word native TOC field — real page numbers calculated when opened
    toc_p = doc.add_paragraph()
    rb = toc_p.add_run()
    fc1 = OxmlElement("w:fldChar")
    fc1.set(qn("w:fldCharType"), "begin")
    fc1.set(qn("w:dirty"), "true")
    rb._r.append(fc1)
    ri = toc_p.add_run()
    ins = OxmlElement("w:instrText")
    ins.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    ins.text = ' TOC \\o "1-4" \\h \\z \\u '
    ri._r.append(ins)
    rs = toc_p.add_run()
    fc2 = OxmlElement("w:fldChar")
    fc2.set(qn("w:fldCharType"), "separate")
    rs._r.append(fc2)
    re_run = toc_p.add_run()
    fc3 = OxmlElement("w:fldChar")
    fc3.set(qn("w:fldCharType"), "end")
    re_run._r.append(fc3)

    doc.add_page_break()


def _policy_meta_table(doc: Document, pol: dict):
    """Small metadata table at the top of each policy (matches template)."""
    rows = [
        ("Policy ID",      pol.get("policy_id", "")),
        ("Framework",      pol.get("framework", "")),
        ("Version",        pol.get("version", "1.0")),
        ("Effective Date", pol.get("effective_date", "")),
        ("Review Date",    pol.get("review_date", "")),
        ("Classification", pol.get("classification", "Internal")),
        ("Owner",          pol.get("owner", "")),
        ("Applicable To",  pol.get("applicable_to", "")),
    ]
    tbl = doc.add_table(rows=len(rows), cols=2)
    tbl.style = "Table Grid"
    for i, (k, v) in enumerate(rows):
        _set_cell_bg(tbl.rows[i].cells[0], LIGHT_BLUE)
        _cell_text(tbl.rows[i].cells[0], k, bold=True, size=10, colour=DARK_BLUE)
        _cell_text(tbl.rows[i].cells[1], v, size=10)
    doc.add_paragraph()


def _add_inline_runs(paragraph, text: str, size: int = 10):
    """Parse **bold** and *italic* markdown inline and emit separate runs."""
    import re
    pattern = re.compile(r'(\*{2}.+?\*{2}|\*[^*]+?\*)')
    for part in pattern.split(text):
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('*') and part.endswith('*'):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part:
            run = paragraph.add_run(part)
        else:
            continue
        run.font.size = Pt(size)


def _write_policy(doc: Document, pol: dict, org_name: str):
    """Write a single policy document into the doc."""
    # Title
    h = doc.add_heading(pol.get("title", "Policy"), level=2)
    for run in h.runs:
        run.font.color.rgb = MID_BLUE
        run.font.size = Pt(14)

    _policy_meta_table(doc, pol)
    _add_horizontal_rule(doc)
    doc.add_paragraph()

    # Sections
    for sec in pol.get("sections", []):
        # Section heading
        sh = doc.add_heading(sec.get("title", ""), level=3)
        for r in sh.runs:
            r.font.color.rgb = DARK_BLUE
            r.font.size = Pt(11)

        # Content — parse line-by-line with bullet/numbered/plain detection
        import re
        content = sec.get("content", "").strip()
        # Strip any trailing "References:" block the LLM may embed in content
        content = re.split(r'\n?\s*references?\s*:', content, flags=re.IGNORECASE)[0]

        # Guard: if content is empty or a known placeholder, write a visible notice
        placeholder_patterns = [
            r'^\s*$',
            r'^(tbd|to be determined|n/a|placeholder|coming soon|not provided)\.?$',
        ]
        is_placeholder = any(re.match(p, content, re.IGNORECASE) for p in placeholder_patterns)
        if is_placeholder or len(content) < 20:
            notice_p = doc.add_paragraph()
            notice_r = notice_p.add_run("[Content to be completed during policy review process.]")
            notice_r.italic = True
            notice_r.font.size = Pt(10)
            notice_r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
            doc.add_paragraph()
            continue

        for line in content.split("\n"):
            line = line.rstrip()
            if not line:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(2)
                continue
            # Markdown heading inside content → sub-heading
            if re.match(r'^#{1,6}\s+', line):
                text = re.sub(r'^#{1,6}\s+', '', line).strip()
                sub = doc.add_heading(text, level=4)
                for r in sub.runs:
                    r.font.color.rgb = MID_BLUE
                    r.font.size = Pt(10)
            elif re.match(r'^[-*+]\s+', line):
                bp = doc.add_paragraph(style='List Bullet')
                bp.paragraph_format.left_indent = Inches(0.3)
                bp.paragraph_format.space_after  = Pt(3)
                _add_inline_runs(bp, re.sub(r'^[-*+]\s+', '', line))
            elif re.match(r'^\d+\.\s+', line):
                np = doc.add_paragraph(style='List Number')
                np.paragraph_format.left_indent = Inches(0.3)
                np.paragraph_format.space_after  = Pt(3)
                _add_inline_runs(np, re.sub(r'^\d+\.\s+', '', line))
            else:
                pp = doc.add_paragraph()
                pp.paragraph_format.space_after = Pt(4)
                _add_inline_runs(pp, line)

        # References
        refs = sec.get("references", [])
        if refs:
            rp = doc.add_paragraph()
            rr = rp.add_run("References: " + ", ".join(refs))
            rr.font.size = Pt(9)
            rr.italic = True
            rr.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

        doc.add_paragraph()

    doc.add_paragraph()


def _procedure_meta_table(doc: Document, proc: dict):
    """Metadata header table for a procedure."""
    rows = [
        ("Procedure ID", proc.get("procedure_id", "")),
        ("Framework",    proc.get("framework", "")),
        ("Frequency",    proc.get("frequency", "")),
        ("Owner",        proc.get("owner", "")),
    ]
    tbl = doc.add_table(rows=len(rows), cols=2)
    tbl.style = "Table Grid"
    for i, (k, v) in enumerate(rows):
        _set_cell_bg(tbl.rows[i].cells[0], LIGHT_BLUE)
        _cell_text(tbl.rows[i].cells[0], k, bold=True, size=10, colour=DARK_BLUE)
        _cell_text(tbl.rows[i].cells[1], v, size=10)
    doc.add_paragraph()


def _write_procedure(doc: Document, proc: dict, org_name: str):
    """Write a single procedure document into the doc."""
    h = doc.add_heading(proc.get("title", "Procedure"), level=2)
    for run in h.runs:
        run.font.color.rgb = MID_BLUE
        run.font.size = Pt(14)

    _procedure_meta_table(doc, proc)
    _add_horizontal_rule(doc)
    doc.add_paragraph()

    # Purpose / Scope / Escalation
    for label, key in [("Purpose", "purpose"), ("Scope", "scope"),
                       ("Escalation Path", "escalation_path")]:
        val = proc.get(key, "").strip()
        if not val:
            continue
        sh = doc.add_heading(label, level=3)
        for r in sh.runs:
            r.font.color.rgb = DARK_BLUE
            r.font.size = Pt(11)
        pp = doc.add_paragraph(val)
        pp.paragraph_format.space_after = Pt(6)
        for r in pp.runs:
            r.font.size = Pt(10)

    # Steps
    steps = proc.get("steps", [])
    if steps:
        sh = doc.add_heading("Procedure Steps", level=3)
        for r in sh.runs:
            r.font.color.rgb = DARK_BLUE
            r.font.size = Pt(11)

    for step in steps:
        num   = step.get("step_number", "")
        title = step.get("title", "")

        # Step heading row
        sp = doc.add_paragraph()
        r  = sp.add_run(f"Step {num}: {title}")
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = MID_BLUE
        sp.paragraph_format.space_before = Pt(6)
        sp.paragraph_format.space_after  = Pt(2)

        # Step metadata table: Responsible | Timeline | Tools
        step_tbl = doc.add_table(rows=1, cols=3)
        step_tbl.style = "Table Grid"
        hdr = step_tbl.rows[0]
        _set_cell_bg(hdr.cells[0], LIGHT_BLUE)
        _set_cell_bg(hdr.cells[1], LIGHT_BLUE)
        _set_cell_bg(hdr.cells[2], LIGHT_BLUE)
        _cell_text(hdr.cells[0], "Responsible",  bold=True, size=9, colour=DARK_BLUE)
        _cell_text(hdr.cells[1], "Timeline",     bold=True, size=9, colour=DARK_BLUE)
        _cell_text(hdr.cells[2], "Tools",        bold=True, size=9, colour=DARK_BLUE)

        tools_str = ", ".join(step.get("tools_required", [])) or "—"
        dr = step_tbl.add_row()
        _cell_text(dr.cells[0], step.get("responsible_role", ""), size=9)
        _cell_text(dr.cells[1], step.get("timeline", ""), size=9)
        _cell_text(dr.cells[2], tools_str, size=9)

        doc.add_paragraph()

        # Description
        desc = step.get("description", "").strip()
        if desc:
            import re
            for line in desc.split("\n"):
                line = line.rstrip()
                if not line:
                    continue
                if re.match(r'^[-*+]\s+', line):
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.paragraph_format.left_indent = Inches(0.4)
                    bp.paragraph_format.space_after = Pt(3)
                    _add_inline_runs(bp, re.sub(r'^[-*+]\s+', '', line))
                else:
                    dp = doc.add_paragraph()
                    dp.paragraph_format.left_indent = Inches(0.2)
                    dp.paragraph_format.space_after  = Pt(4)
                    _add_inline_runs(dp, line)

        # Documentation note
        docn = step.get("documentation", "")
        if docn:
            np = doc.add_paragraph()
            np.paragraph_format.left_indent = Inches(0.2)
            nr = np.add_run(f"📄 Documentation: {docn}")
            nr.italic = True
            nr.font.size = Pt(9)
            nr.font.color.rgb = RGBColor(0x50, 0x50, 0x50)

        doc.add_paragraph()

    doc.add_paragraph()


def build_compliance_docx(
    org_name: str,
    frameworks: List[str],
    policies: List[dict],
    procedures: List[dict],
    author: str = "GRC AI Platform",
) -> bytes:
    """
    Build a full compliance DOCX package and return raw bytes.

    Args:
        org_name:   Organization name (displayed on cover page)
        frameworks: List of framework IDs used
        policies:   List of policy dicts (from GeneratedPolicy.dict())
        procedures: List of procedure dicts (from GeneratedProcedure.dict())
        author:     Author name for the cover page
    Returns:
        Raw DOCX file bytes, ready to send as a file response.
    """
    doc = Document()

    # ── Page margins + header/footer ──────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)
        section.different_first_page_header_footer = False

        # Header: "Compliance Documentation — <Org>"
        header_p = section.header.paragraphs[0]
        header_p.clear()
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hr = header_p.add_run(f"Compliance Documentation — {org_name}")
        hr.font.size = Pt(8)
        hr.italic    = True
        hr.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

        # Footer: "<Org> Confidential   Page X of Y"
        footer_p = section.footer.paragraphs[0]
        footer_p.clear()
        footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        r1 = footer_p.add_run(f"{org_name} Confidential     ")
        r1.font.size = Pt(8); r1.italic = True
        r1.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

        r2 = footer_p.add_run("Page ")
        r2.font.size = Pt(8)
        r2.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

        # PAGE field
        fld = OxmlElement("w:fldChar"); fld.set(qn("w:fldCharType"), "begin")
        r2._r.append(fld)
        ins = OxmlElement("w:instrText"); ins.text = "PAGE"
        r2._r.append(ins)
        fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
        r2._r.append(fld_end)

        r3 = footer_p.add_run(" of ")
        r3.font.size = Pt(8)
        r3.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

        # NUMPAGES field
        fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "begin")
        r3._r.append(fld2)
        ins2 = OxmlElement("w:instrText"); ins2.text = "NUMPAGES"
        r3._r.append(ins2)
        fld_end2 = OxmlElement("w:fldChar"); fld_end2.set(qn("w:fldCharType"), "end")
        r3._r.append(fld_end2)

    # ── Default body font ─────────────────────────────────────────────────────
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10)

    generated_date = datetime.now().strftime("%d %B %Y")

    # ── 1. Cover page ─────────────────────────────────────────────────────────
    _build_cover_page(doc, org_name, frameworks, generated_date, author)

    # ── 2. Revision History ───────────────────────────────────────────────────
    _build_revision_history(doc, policies, procedures)

    # ── 3. Table of Contents ──────────────────────────────────────────────────
    _build_toc_placeholder(doc, policies, procedures)

    # ── 4. Part I — Compliance Policies ──────────────────────────────────────
    if policies:
        h = doc.add_heading("Part I — Compliance Policies", level=1)
        h.runs[0].font.color.rgb = DARK_BLUE
        doc.add_paragraph()

        # Group by framework
        fw_order: List[str] = []
        fw_map: dict = {}
        for pol in policies:
            fw = pol.get("framework", "Unknown")
            if fw not in fw_map:
                fw_map[fw] = []
                fw_order.append(fw)
            fw_map[fw].append(pol)

        for fw in fw_order:
            # Framework section heading
            fh = doc.add_heading(fw, level=1)
            fh.runs[0].font.color.rgb = MID_BLUE
            _add_horizontal_rule(doc)
            doc.add_paragraph()

            for pol in fw_map[fw]:
                _write_policy(doc, pol, org_name)
                doc.add_page_break()

    # ── 5. Part II — Operational Procedures ──────────────────────────────────
    if procedures:
        h = doc.add_heading("Part II — Operational Procedures", level=1)
        h.runs[0].font.color.rgb = DARK_BLUE
        doc.add_paragraph()

        fw_order_p: List[str] = []
        fw_map_p: dict = {}
        for proc in procedures:
            fw = proc.get("framework", "Unknown")
            if fw not in fw_map_p:
                fw_map_p[fw] = []
                fw_order_p.append(fw)
            fw_map_p[fw].append(proc)

        for fw in fw_order_p:
            fh = doc.add_heading(fw, level=1)
            fh.runs[0].font.color.rgb = MID_BLUE
            _add_horizontal_rule(doc)
            doc.add_paragraph()

            for proc in fw_map_p[fw]:
                _write_procedure(doc, proc, org_name)
                doc.add_page_break()

    # ── Serialise to bytes ────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
