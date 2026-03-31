"""
ComplianceIQ — Chatbot Interface
Conversational wizard: ask questions → personalize → generate → export as .docx
"""

import json
import html
import os
import re
import requests
import streamlit as st
import streamlit.components.v1 as components

API_BASE = "http://localhost:8000"

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ComplianceIQ",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main { background: #0f1117; }

  .hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2d3748; border-radius: 16px;
    padding: 2rem; text-align: center; margin-bottom: 1.5rem;
  }
  .hero h1 { font-size: 2rem; font-weight: 700; color: #f7fafc; margin: 0; }
  .hero p  { color: #a0aec0; font-size: 0.95rem; margin-top: 0.4rem; }

  /* Chat container */
  .chat-container {
    max-height: 280px;
    overflow-y: auto;
    padding: 0.5rem 0.2rem;
    display: flex;
    flex-direction: column;
    scrollbar-width: thin;
    scrollbar-color: #2d3748 transparent;
  }
  .chat-container::-webkit-scrollbar { width: 4px; }
  .chat-container::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 2px; }

  /* Chat bubbles */
  .chat-bot {
    background: #1a2035; border: 1px solid #2d3748;
    border-radius: 14px 14px 14px 2px;
    padding: 0.9rem 1.2rem; margin: 0.5rem 0;
    color: #e2e8f0; font-size: 0.92rem; line-height: 1.6;
    max-width: 85%;
  }
  .chat-user {
    background: linear-gradient(135deg, #3a4a9e, #553a8a);
    border: 1px solid #667eea;
    border-radius: 14px 14px 2px 14px;
    padding: 0.9rem 1.2rem; margin: 0.5rem 0 0.5rem auto;
    color: #f0f4ff; font-size: 0.92rem; line-height: 1.6;
    max-width: 75%; text-align: right;
  }
  .chat-label-bot { color: #667eea; font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.08em; margin-bottom: 2px; }
  .chat-label-user { color: #a0aec0; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.08em; margin-bottom: 2px; text-align: right; }

  /* Progress bar */
  .progress-bar {
    display: flex; gap: 4px; margin-bottom: 1.5rem; align-items: center;
  }
  .prog-step {
    flex: 1; height: 4px; border-radius: 2px; background: #2d3748;
    transition: background 0.3s;
  }
  .prog-step.done { background: #667eea; }
  .prog-step.active { background: linear-gradient(90deg, #667eea, #764ba2); }
  .prog-label { color: #718096; font-size: 0.72rem; margin-left: 6px; white-space: nowrap; }

  /* Framework cards */
  .fw-card {
    background: #1a202c; border: 2px solid #2d3748;
    border-radius: 12px; padding: 1rem; transition: all 0.2s; height: 100%;
  }
  .fw-card.selected { border-color: #667eea; background: #1e2a4a; }
  .fw-card h4 { color: #e2e8f0; font-size: 0.9rem; margin: 0.3rem 0; }
  .fw-card p  { color: #718096; font-size: 0.78rem; margin: 0; }
  .score-bar { height: 4px; background: #2d3748; border-radius: 2px; margin: 0.5rem 0; }
  .score-fill { height: 4px; border-radius: 2px; background: linear-gradient(90deg, #667eea, #764ba2); }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px;
    font-size: 0.68rem; font-weight: 600; background: #2d3748; color: #a0aec0; margin-bottom: 0.3rem; }
  .badge.mandatory { background: #2d1515; color: #fc8181; }

  /* Doc section */
  .doc-card { background: #13171f; border: 1px solid #2d3748; border-radius: 14px;
    padding: 1.5rem 1.8rem; margin-bottom: 1rem; }
  .doc-card h3 { color: #f0f4ff; font-size: 1.1rem; font-weight: 700; margin: 0 0 0.5rem; }
  .doc-meta-bar { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;
    padding-bottom: 0.8rem; border-bottom: 1px solid #2d3748; }
  .doc-meta-item { background: #1e2535; border: 1px solid #2d3748; border-radius: 6px;
    padding: 3px 10px; font-size: 0.73rem; color: #90a0b7; }
  .doc-meta-item b { color: #c8d6e8; }
  .policy-section { margin: 0.8rem 0; padding: 0.7rem 1rem;
    background: #1a2030; border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; }
  .policy-section-title { color: #667eea; font-size: 0.75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
  .ref-tag { display: inline-block; background: #1a2a4a; color: #7eb8f7;
    border: 1px solid #2b4c7e; border-radius: 4px; padding: 2px 7px;
    font-size: 0.7rem; margin: 3px 2px 0; }
  .step-card { background: #1a202c; border-left: 3px solid #667eea;
    border-radius: 0 8px 8px 0; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }
  .step-card .step-num { color: #667eea; font-weight: 700; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.05em; }
  .step-card h4 { color: #e2e8f0; margin: 0.2rem 0; font-size: 0.9rem; }
  .step-meta { display: flex; gap: 1rem; margin-top: 0.4rem; flex-wrap: wrap; }
  .step-meta span { color: #718096; font-size: 0.76rem; }
  .step-meta span b { color: #a0aec0; }
  .pill { display: inline-block; background: #2d3748; color: #a0aec0;
    border-radius: 999px; padding: 2px 9px; font-size: 0.76rem; margin: 2px; }
  .summary-box { background: #1a2a1a; border: 1px solid #2f855a; border-radius: 10px;
    padding: 0.8rem 1.1rem; color: #68d391; font-size: 0.85rem; margin-bottom: 1rem; }
  hr { border-color: #2d3748; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; }
  [data-testid="collapsedControl"] { display: block !important; visibility: visible !important; }
  section[data-testid="stSidebar"] { display: block !important; visibility: visible !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ─── Session State Init ───────────────────────────────────────────────────────
DEFAULTS = {
    "chat_phase": "intro",  # intro | org_name | org_desc | website | country | analyzing | frameworks | policy_types | proc_types | generating | done
    "messages": [],
    "org_name": "",
    "org_description": "",
    "org_website": "",
    "org_country": "",
    "profile": None,
    "selected_frameworks": [],
    "policy_types": ["data_protection", "incident_response", "access_control"],
    "procedure_types": ["incident_response", "data_breach", "access_review"],
    "policies": None,
    "procedures": None,
    "session_id": None,
    "page": "chat",
    "gen_framework": None,
    "gen_frameworks": [],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

POLICY_TYPES_MAP = {
    "data_protection": "Data Protection & Privacy",
    "incident_response": "Incident Response",
    "access_control": "Access Control & IAM",
    "data_retention": "Data Retention & Disposal",
    "third_party_risk": "Third-Party Risk Management",
    "acceptable_use": "Acceptable Use",
    "business_continuity": "Business Continuity & DR",
    "encryption": "Encryption & Key Management",
}
PROCEDURE_TYPES_MAP = {
    "incident_response": "Security Incident Response",
    "data_breach": "Data Breach Notification",
    "access_review": "Periodic Access Review",
    "vendor_assessment": "Vendor Due Diligence",
    "data_subject_request": "Data Subject Rights Request",
    "risk_assessment": "Risk Assessment",
    "backup_recovery": "Backup & Recovery Testing",
    "security_awareness": "Security Awareness Training",
    "change_management": "Change Management",
    "vulnerability_management": "Vulnerability Management",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def api(method, path, **kwargs):
    try:
        r = getattr(requests, method)(f"{API_BASE}{path}", timeout=120, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return (
            None,
            "Cannot connect to backend. Make sure the FastAPI server is running on port 8000.",
        )
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as e:
        return None, str(e)


def bot_msg(text):
    st.session_state.messages.append({"role": "bot", "content": text})


def user_msg(text):
    st.session_state.messages.append({"role": "user", "content": text})


def score_color(score):
    if score >= 0.8:
        return "#68d391"
    if score >= 0.6:
        return "#f6e05e"
    return "#fc8181"


# ─── Progress Indicator ───────────────────────────────────────────────────────
PHASE_ORDER = [
    "intro",
    "org_name",
    "org_desc",
    "website",
    "country",
    "analyzing",
    "frameworks",
    "policy_types",
    "proc_types",
    "generating",
    "done",
]


def render_progress():
    phase = st.session_state.chat_phase
    steps = [
        "Organization Info",
        "Framework Selection",
        "Policy & Procedure Types",
        "Generate & Export",
    ]
    phase_groups = [
        ["intro", "org_name", "org_desc", "website", "country", "analyzing"],
        ["frameworks"],
        ["policy_types", "proc_types"],
        ["generating", "done"],
    ]
    current_group = next((i for i, g in enumerate(phase_groups) if phase in g), 0)
    pills = ""
    for i, (step, group) in enumerate(zip(steps, phase_groups)):
        if i < current_group:
            cls = "done"
        elif i == current_group:
            cls = "active"
        else:
            cls = ""
        pills += f'<div class="prog-step {cls}"></div>'
    st.markdown(
        f'<div class="progress-bar">{pills}<span class="prog-label">Step {current_group+1}/4 · {steps[current_group]}</span></div>',
        unsafe_allow_html=True,
    )


# ─── Chat Renderer ────────────────────────────────────────────────────────────
def _md_to_html(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = text.replace('\n', '<br>')
    return text

def render_chat():
    msgs_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "bot":
            msgs_html += f'<div class="chat-label-bot">🛡️ ComplianceIQ</div><div class="chat-bot">{_md_to_html(msg["content"])}</div>'
        else:
            msgs_html += f'<div class="chat-label-user">You</div><div class="chat-user">{html.escape(msg["content"])}</div>'
    st.markdown(
        f'<div class="chat-container" id="chat-box">{msgs_html}</div>',
        unsafe_allow_html=True,
    )
    components.html(
        '<script>'
        'function scrollChat(){'
        '  var els=window.parent.document.querySelectorAll(".chat-container");'
        '  if(els.length){els[els.length-1].scrollTop=els[els.length-1].scrollHeight;}'
        '  else{setTimeout(scrollChat,150);}'
        '}'
        'setTimeout(scrollChat,100);'
        '</script>',
        height=1,
    )


# ─── DOCX Generation ─────────────────────────────────────────────────────────
def generate_docx(payload: dict, out_path: str) -> str | None:
    """Generate a .docx from policy/procedure payload. Returns error string or None."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from datetime import datetime

        doc = Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1.2)
            section.right_margin = Inches(1.2)

        def set_color(run, hex_color):
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            run.font.color.rgb = RGBColor(r, g, b)

        def add_heading1(text):
            p = doc.add_heading(text, level=1)
            p.runs[0].font.size = Pt(18)
            set_color(p.runs[0], "1a1a2e")

        def add_heading2(text):
            p = doc.add_heading(text, level=2)
            p.runs[0].font.size = Pt(14)
            set_color(p.runs[0], "2d3a6e")

        def add_heading3(text):
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.bold = True
            run.font.size = Pt(11)
            set_color(run, "4a5fa8")

        def add_meta(label, value):
            if not value:
                return
            p = doc.add_paragraph()
            r1 = p.add_run(f"{label}: ")
            r1.bold = True
            r1.font.size = Pt(9)
            set_color(r1, "444444")
            r2 = p.add_run(value)
            r2.font.size = Pt(9)
            set_color(r2, "555555")
            p.paragraph_format.space_after = Pt(2)

        def clean_inline(text):
            """Strip markdown inline markers and return plain text with bold/italic runs."""
            # Remove any remaining * or _ markers cleanly
            text = re.sub(r'\*{3}(.+?)\*{3}', r'\1', text)  # ***bold italic***
            text = re.sub(r'\*{2}(.+?)\*{2}', r'\1', text)  # **bold**
            text = re.sub(r'\*(.+?)\*', r'\1', text)         # *italic*
            text = re.sub(r'_{2}(.+?)_{2}', r'\1', text)     # __bold__
            text = re.sub(r'_(.+?)_', r'\1', text)           # _italic_
            text = re.sub(r'`(.+?)`', r'\1', text)           # `code`
            text = re.sub(r'^#{1,6}\s*', '', text)           # ### headings
            return text.strip()

        def add_inline_runs(paragraph, text):
            """Add runs to a paragraph, rendering **bold** and *italic* properly."""
            # Pattern: **bold**, *italic*, plain
            pattern = re.compile(r'(\*{2}.+?\*{2}|\*[^*]+?\*)')
            parts = pattern.split(text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = paragraph.add_run(part[2:-2])
                    run.bold = True
                    run.font.size = Pt(10)
                elif part.startswith('*') and part.endswith('*'):
                    run = paragraph.add_run(part[1:-1])
                    run.italic = True
                    run.font.size = Pt(10)
                elif part:
                    run = paragraph.add_run(part)
                    run.font.size = Pt(10)

        def add_body(text):
            if not text:
                return
            for line in text.split("\n"):
                line = line.rstrip()
                if not line:
                    doc.add_paragraph().paragraph_format.space_after = Pt(2)
                    continue
                # Heading lines → heading3 style
                if re.match(r'^#{1,6}\s+', line):
                    heading_text = re.sub(r'^#{1,6}\s+', '', line).strip()
                    add_heading3(clean_inline(heading_text))
                # Bullet lines
                elif re.match(r'^[-*+]\s+', line):
                    bullet_text = re.sub(r'^[-*+]\s+', '', line).strip()
                    p = doc.add_paragraph(style='List Bullet')
                    add_inline_runs(p, bullet_text)
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.left_indent = Inches(0.25)
                # Numbered list
                elif re.match(r'^\d+\.\s+', line):
                    num_text = re.sub(r'^\d+\.\s+', '', line).strip()
                    p = doc.add_paragraph(style='List Number')
                    add_inline_runs(p, num_text)
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.left_indent = Inches(0.25)
                # Normal paragraph
                else:
                    p = doc.add_paragraph()
                    add_inline_runs(p, line)
                    p.paragraph_format.space_after = Pt(4)
                    p.paragraph_format.space_before = Pt(0)

        def add_divider():
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)

        org_name = payload.get("org_name", "Your Organization")
        framework = payload.get("framework", "")
        policies = payload.get("policies", [])
        procedures = payload.get("procedures", [])

        # ── Cover ──
        doc.add_paragraph()
        cover_title = doc.add_paragraph("Compliance Documentation")
        cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cover_title.runs[0]
        run.bold = True
        run.font.size = Pt(28)
        set_color(run, "1a1a2e")

        p = doc.add_paragraph(org_name)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.size = Pt(18)
        set_color(p.runs[0], "4a5fa8")

        p = doc.add_paragraph(f"Framework: {framework}")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].italic = True
        p.runs[0].font.size = Pt(12)
        set_color(p.runs[0], "718096")

        p = doc.add_paragraph(f"Generated: {datetime.now().strftime('%d %B %Y')}")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.size = Pt(10)
        set_color(p.runs[0], "718096")

        p = doc.add_paragraph("CONFIDENTIAL — INTERNAL USE ONLY")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(9)
        set_color(p.runs[0], "c0392b")

        # ── Policies ──
        if policies:
            doc.add_page_break()
            add_heading1("Part I — Compliance Policies")
            for p in policies:
                doc.add_page_break()
                add_heading2(p.get("title", ""))
                add_meta("Policy ID", p.get("policy_id"))
                add_meta("Version", p.get("version"))
                add_meta("Effective Date", p.get("effective_date"))
                add_meta("Review Date", p.get("review_date"))
                add_meta("Classification", p.get("classification"))
                add_meta("Owner", p.get("owner"))
                add_meta("Applicable To", p.get("applicable_to"))
                add_divider()
                for sec in p.get("sections", []):
                    add_heading3(sec.get("title", ""))
                    add_body(sec.get("content", ""))
                    refs = sec.get("references", [])
                    if refs:
                        rp = doc.add_paragraph(f"References: {' · '.join(refs)}")
                        rp.runs[0].italic = True
                        rp.runs[0].font.size = Pt(8)
                        set_color(rp.runs[0], "4a7ab5")

        # ── Procedures ──
        if procedures:
            doc.add_page_break()
            add_heading1("Part II — Operational Procedures")
            for p in procedures:
                doc.add_page_break()
                add_heading2(p.get("title", ""))
                add_meta("Procedure ID", p.get("procedure_id"))
                add_meta("Frequency", p.get("frequency"))
                add_meta("Owner", p.get("owner"))
                add_meta("Framework", p.get("framework"))
                add_divider()
                for label, key in [("Purpose", "purpose"), ("Scope", "scope"), ("Escalation Path", "escalation_path")]:
                    if p.get(key):
                        add_heading3(label)
                        add_body(p[key])
                if p.get("steps"):
                    add_heading3("Procedure Steps")
                    for step in p["steps"]:
                        sp = doc.add_paragraph()
                        r1 = sp.add_run(f"Step {step.get('step_number')}: ")
                        r1.bold = True
                        r1.font.size = Pt(10)
                        set_color(r1, "4a5fa8")
                        r2 = sp.add_run(step.get("title", ""))
                        r2.bold = True
                        r2.font.size = Pt(10)
                        add_meta("Responsible", step.get("responsible_role"))
                        add_meta("Timeline", step.get("timeline"))
                        tools = ", ".join(step.get("tools_required", []))
                        add_meta("Tools", tools or None)
                        add_body(step.get("description", ""))

        doc.save(out_path)
        return None
    except Exception as e:
        return str(e)


def render_policy(p, dl_key, show_docx=True):
    h = html
    meta_items = "".join(
        [
            f"<span class='doc-meta-item'><b>ID</b> {h.escape(p.get('policy_id',''))}</span>",
            f"<span class='doc-meta-item'><b>v{h.escape(p.get('version',''))}</b></span>",
            f"<span class='doc-meta-item'><b>Effective</b> {h.escape(p.get('effective_date','') or '')}</span>",
            f"<span class='doc-meta-item'><b>Review</b> {h.escape(p.get('review_date','') or '')}</span>",
            f"<span class='doc-meta-item'>{h.escape(p.get('classification','') or '')}</span>",
        ]
    )
    st.markdown(
        f"""
    <div class="doc-card">
      <h3>{h.escape(p.get('title',''))}</h3>
      <div class="doc-meta-bar">{meta_items}</div>
      <div class="doc-meta-bar" style="border-bottom:none;padding-bottom:0;margin-bottom:0">
        <span class="doc-meta-item"><b>Owner</b> {h.escape(p.get('owner','') or '')}</span>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    for sec in p.get("sections", []):
        refs_html = " ".join(
            f'<span class="ref-tag">{h.escape(r)}</span>'
            for r in sec.get("references", [])
        )
        st.markdown(
            f'<div class="policy-section"><div class="policy-section-title">{h.escape(sec.get("title",""))}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(sec.get("content", ""))
        if refs_html:
            st.markdown(
                f'<div style="margin-top:0.3rem;margin-bottom:0.6rem">{refs_html}</div>',
                unsafe_allow_html=True,
            )
    st.download_button(
        "⬇ Download JSON",
        data=json.dumps(p, indent=2),
        file_name=f"{p.get('policy_id','policy')}.json",
        mime="application/json",
        key=dl_key,
    )


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ ComplianceIQ")
    st.markdown("---")
    sidebar_sel = st.radio(
        "Navigation",
        ["chat", "history"],
        index=0 if st.session_state.page == "chat" else 1,
        format_func=lambda x: "💬 Chat Wizard" if x == "chat" else "🗂️ History",
        label_visibility="collapsed",
    )
    if sidebar_sel != st.session_state.page:
        st.session_state.page = sidebar_sel
        st.rerun()
    st.markdown("---")
    st.caption("Backend: `localhost:8000`")
    try:
        r = requests.get(f"{API_BASE}/status", timeout=3)
        if r.status_code == 200:
            s = r.json()
            st.success("Backend online")
            st.caption(f"Groq slots: {s.get('groq_total_slots','?')}")
            st.caption(f"Tavily: {'✅' if s.get('tavily_available') else '❌'}")
        else:
            st.error("Backend error")
    except Exception:
        st.error("Backend offline")

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <h1>🛡️ ComplianceIQ</h1>
  <p>AI-powered compliance intelligence — chat your way to personalized policies & procedures</p>
</div>
""",
    unsafe_allow_html=True,
)

# ─── HISTORY PAGE ─────────────────────────────────────────────────────────────
if st.session_state.page == "history":
    col_nav1, col_nav2, _ = st.columns([1, 1, 6])
    with col_nav1:
        if st.button("💬 Chat", use_container_width=True, type="secondary"):
            st.session_state.page = "chat"
            st.rerun()
    with col_nav2:
        st.button("🗂️ History", use_container_width=True, type="primary")

    st.subheader("Past Compliance Sessions")
    data, err = api("get", "/history?limit=100")
    if err:
        st.error(f"❌ {err}")
    elif not data["sessions"]:
        st.info(
            "No sessions yet. Start a chat to generate your first compliance documents."
        )
    else:
        sessions = data["sessions"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Sessions", len(sessions))
        c2.metric("Total Policies", sum(s["policy_count"] for s in sessions))
        c3.metric("Total Procedures", sum(s["procedure_count"] for s in sessions))
        st.markdown("---")
        for s in sessions:
            with st.expander(
                f"🏢 {s['org_name']}  ·  {s['created_at'][:10]}  ·  {s['policy_count']} policies  ·  {s['procedure_count']} procedures",
                expanded=False,
            ):
                col1, col2 = st.columns([3, 1])
                with col1:
                    fw_pills = (
                        " ".join(
                            f'<span class="pill">{f}</span>'
                            for f in s["selected_frameworks"]
                        )
                        or '<span class="pill">none selected</span>'
                    )
                    st.markdown(
                        f"""
                    <div class="doc-card">
                      <h3>{html.escape(s['org_name'])}</h3>
                      <div class="doc-meta-bar">
                        <span class="doc-meta-item">{s.get('org_country') or '—'}</span>
                        <span class="doc-meta-item"><b>Session</b> #{s['session_id']}</span>
                      </div>
                      <div>{fw_pills}</div>
                    </div>""",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(
                        "📂 View Detail",
                        key=f"load_{s['session_id']}",
                        use_container_width=True,
                    ):
                        st.session_state["history_detail_id"] = s["session_id"]
                    if st.button(
                        "🗑️ Delete",
                        key=f"del_{s['session_id']}",
                        use_container_width=True,
                    ):
                        _, err2 = api("delete", f"/history/{s['session_id']}")
                        if err2:
                            st.error(err2)
                        else:
                            st.success("Deleted")
                            st.rerun()

                if st.session_state.get("history_detail_id") == s["session_id"]:
                    detail, err3 = api("get", f"/history/{s['session_id']}")
                    if err3:
                        st.error(err3)
                    else:
                        # DOCX export from history
                        if detail["policies"] or detail["procedures"]:
                            frameworks_used = list(
                                {
                                    p.get("framework", "")
                                    for p in detail["policies"] + detail["procedures"]
                                    if p.get("framework")
                                }
                            )
                            docx_payload = {
                                "org_name": detail["org_name"],
                                "framework": ", ".join(frameworks_used),
                                "policies": detail["policies"],
                                "procedures": detail["procedures"],
                            }
                            docx_out = os.path.join(os.environ.get("TEMP", "/tmp"), f"hist_{s['session_id']}.docx")
                            docx_err = generate_docx(docx_payload, docx_out)
                            if not docx_err and os.path.exists(docx_out):
                                with open(docx_out, "rb") as f:
                                    st.download_button(
                                        "📄 Download Full Compliance Document (.docx)",
                                        data=f.read(),
                                        file_name=f"{detail['org_name'].replace(' ','_')}_compliance.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key=f"hist_docx_{s['session_id']}",
                                        use_container_width=True,
                                    )
                                os.unlink(docx_out)
                        if detail["policies"]:
                            st.markdown(f"**Policies ({len(detail['policies'])})**")
                            for pi, p in enumerate(detail["policies"]):
                                with st.expander(f"📄 {p['title']}", expanded=False):
                                    render_policy(p, f"dl_pol_{s['session_id']}_{pi}")
                        if detail.get("procedures"):
                            st.markdown(f"**Procedures ({len(detail['procedures'])})**")
                            for pi, proc in enumerate(detail["procedures"]):
                                with st.expander(f"📋 {proc['title']}", expanded=False):
                                    h = html
                                    st.markdown(
                                        f"""
                                    <div class="doc-card">
                                      <h3>{h.escape(proc.get('title',''))}</h3>
                                      <div class="doc-meta-bar">
                                        <span class="doc-meta-item"><b>ID</b> {h.escape(proc.get('procedure_id',''))}</span>
                                        <span class="doc-meta-item"><b>Frequency</b> {h.escape(proc.get('frequency','') or '')}</span>
                                        <span class="doc-meta-item"><b>Owner</b> {h.escape(proc.get('owner','') or '')}</span>
                                      </div>
                                    </div>""",
                                        unsafe_allow_html=True,
                                    )
                                    for label, key in [("Purpose", "purpose"), ("Scope", "scope"), ("Escalation Path", "escalation_path")]:
                                        if proc.get(key):
                                            st.markdown(f'<div class="policy-section"><div class="policy-section-title">{label}</div></div>', unsafe_allow_html=True)
                                            st.markdown(proc[key])
                                    for step in proc.get("steps", []):
                                        st.markdown(
                                            f'<div class="step-card"><div class="step-num">Step {step["step_number"]}</div><h4>{h.escape(step.get("title",""))}</h4><div class="step-meta"><span>👤 <b>{h.escape(step.get("responsible_role",""))}</b></span><span>⏱ <b>{h.escape(step.get("timeline",""))}</b></span></div></div>',
                                            unsafe_allow_html=True,
                                        )
                                        st.markdown(step.get("description", ""))
                                    st.download_button(
                                        "⬇ Download JSON",
                                        data=json.dumps(proc, indent=2),
                                        file_name=f"{proc.get('procedure_id','procedure')}.json",
                                        mime="application/json",
                                        key=f"dl_proc_{s['session_id']}_{pi}",
                                    )
    st.stop()

# ─── CHAT PAGE ────────────────────────────────────────────────────────────────
col_nav1, col_nav2, _ = st.columns([1, 1, 6])
with col_nav1:
    st.button("💬 Chat", use_container_width=True, type="primary")
with col_nav2:
    if st.button("🗂️ History", use_container_width=True, type="secondary"):
        st.session_state.page = "history"
        st.rerun()

render_progress()

phase = st.session_state.chat_phase

# ─── Initialize conversation on first load ───────────────────────────────────
if phase == "intro" and not st.session_state.messages:
    bot_msg(
        "👋 Welcome to ComplianceIQ! I'll guide you through creating personalized compliance documents step by step."
    )
    bot_msg(
        "Let's start with your organization name. What is your company or organization called?"
    )
    st.session_state.chat_phase = "org_name"
    st.rerun()

render_chat()
st.markdown("<br>", unsafe_allow_html=True)

phase = st.session_state.chat_phase

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: org_name
# ══════════════════════════════════════════════════════════════════════════════
if phase == "org_name":
    with st.form("form_org_name", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            val = st.text_input(
                "Organization name",
                placeholder="e.g. NatSteel Holdings Pte Ltd",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button(
                "Send →", use_container_width=True, type="primary"
            )
        if submitted and val.strip():
            user_msg(val.strip())
            st.session_state.org_name = val.strip()
            bot_msg(f"Great, **{val.strip()}** noted! 🏢")
            bot_msg(
                "Now, please describe your organization in a few words — industry, region, type. For example: *Indian healthcare SaaS startup* or *EU fintech payment processor*."
            )
            st.session_state.chat_phase = "org_desc"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: org_desc
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "org_desc":
    examples = [
        "Indian healthcare SaaS startup",
        "US fintech payment processor",
        "EU ecommerce retail company",
        "Global manufacturing enterprise",
    ]
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        with col:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                user_msg(ex)
                st.session_state.org_description = ex
                bot_msg(f"Got it — *{ex}*.")
                bot_msg(
                    "Do you have a **website URL**? It helps our AI do a deeper analysis. Type it or press **Skip** to continue."
                )
                st.session_state.chat_phase = "website"
                st.rerun()

    with st.form("form_org_desc", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            val = st.text_input(
                "Organization description",
                placeholder="e.g. Indian healthcare SaaS startup",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button(
                "Send →", use_container_width=True, type="primary"
            )
        if submitted and val.strip():
            user_msg(val.strip())
            st.session_state.org_description = val.strip()
            bot_msg(f"Got it — *{val.strip()}*.")
            bot_msg(
                "Do you have a **website URL**? It helps our AI do a deeper analysis. Type it or press **Skip** to continue."
            )
            st.session_state.chat_phase = "website"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: website
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "website":
    with st.form("form_website", clear_on_submit=True):
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            val = st.text_input(
                "Website URL",
                placeholder="https://example.com",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button(
                "Send →", use_container_width=True, type="primary"
            )
        with col3:
            skipped = st.form_submit_button("Skip ⟶", use_container_width=True)
        if submitted and val.strip():
            user_msg(val.strip())
            st.session_state.org_website = val.strip()
            bot_msg(f"Website noted: `{val.strip()}`")
            bot_msg(
                "Which **country** is your organization headquartered in? (e.g. India, USA, Germany, Singapore)"
            )
            st.session_state.chat_phase = "country"
            st.rerun()
        if skipped:
            user_msg("(Skipping website)")
            bot_msg(
                "No problem! Which **country** is your organization headquartered in?"
            )
            st.session_state.chat_phase = "country"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: country
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "country":
    country_suggestions = ["India", "USA", "Germany", "Singapore", "UK", "Australia"]
    cols = st.columns(len(country_suggestions))
    for col, c in zip(cols, country_suggestions):
        with col:
            if st.button(c, key=f"country_{c}", use_container_width=True):
                user_msg(c)
                st.session_state.org_country = c
                bot_msg(
                    f"**{c}** — perfect. Now let me analyze your organization with our AI agents. This takes about 30–60 seconds. ⚙️"
                )
                st.session_state.chat_phase = "analyzing"
                st.rerun()

    with st.form("form_country", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            val = st.text_input(
                "Country",
                placeholder="e.g. India, USA, Germany",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button(
                "Send →", use_container_width=True, type="primary"
            )
        if submitted and val.strip():
            user_msg(val.strip())
            st.session_state.org_country = val.strip()
            bot_msg(
                f"**{val.strip()}** — perfect. Now let me analyze your organization with our AI agents. This takes about 30–60 seconds. ⚙️"
            )
            st.session_state.chat_phase = "analyzing"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: analyzing
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "analyzing":
    with st.spinner("🤖 AI agents analyzing your organization..."):
        data, err = api(
            "post",
            "/profile",
            json={
                "description": st.session_state.org_description,
                "website": st.session_state.org_website or None,
                "country": st.session_state.org_country or None,
            },
        )
    if err:
        bot_msg(
            f"❌ Analysis failed: {err}. Please check the backend is running and try again."
        )
        st.session_state.chat_phase = "org_name"
        st.rerun()
    else:
        st.session_state.profile = data
        st.session_state.session_id = data.get("session_id")
        st.session_state.selected_frameworks = [
            fw["id"]
            for fw in data["recommended_frameworks"]
            if fw["relevance_score"] >= 0.7
        ]
        industries = ", ".join(data.get("industries_detected", [])) or "—"
        regions = ", ".join(data.get("regions_detected", [])) or "—"
        fw_count = len(data.get("recommended_frameworks", []))
        bot_msg(
            f"✅ Analysis complete!\n\n**{data.get('org_type','')}** detected.\n\n📌 *{data.get('analysis_summary','')}*\n\n🏭 Industries: **{industries}** | 🌍 Regions: **{regions}**\n\nI found **{fw_count} applicable compliance frameworks**. Let me show them to you so you can select which ones to use."
        )
        st.session_state.chat_phase = "frameworks"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: frameworks
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "frameworks":
    profile = st.session_state.profile
    frameworks = profile.get("recommended_frameworks", [])
    selected = st.session_state.selected_frameworks

    st.markdown("**Select the compliance frameworks that apply to your organization:**")
    st.caption(
        "Cards pre-selected based on AI recommendations (≥70% relevance). Click to toggle."
    )

    for row_start in range(0, len(frameworks), 3):
        row = frameworks[row_start : row_start + 3]
        cols = st.columns(3)
        for col, fw in zip(cols, row):
            with col:
                is_sel = fw["id"] in selected
                badge = (
                    '<span class="badge mandatory">MANDATORY</span>'
                    if fw["is_mandatory"]
                    else '<span class="badge">RECOMMENDED</span>'
                )
                score_pct = int(fw["relevance_score"] * 100)
                color = score_color(fw["relevance_score"])
                card_class = "fw-card selected" if is_sel else "fw-card"
                st.markdown(
                    f"""
                <div class="{card_class}">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.4rem">{fw['icon']}</span>{badge}
                  </div>
                  <h4>{fw['id']} — {fw['name'][:28]}{'…' if len(fw['name'])>28 else ''}</h4>
                  <div class="score-bar"><div class="score-fill" style="width:{score_pct}%;background:{color}"></div></div>
                  <p style="color:{color};font-weight:600;font-size:0.76rem">{score_pct}% relevance</p>
                  <p style="margin-top:0.3rem">{fw['relevance_reason'][:90]}{'…' if len(fw['relevance_reason'])>90 else ''}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                label = "✓ Selected" if is_sel else "+ Select"
                btn_type = "primary" if is_sel else "secondary"
                if st.button(
                    label, key=f"fw_{fw['id']}", use_container_width=True, type=btn_type
                ):
                    if is_sel:
                        st.session_state.selected_frameworks.remove(fw["id"])
                    else:
                        st.session_state.selected_frameworks.append(fw["id"])
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    sel_count = len(st.session_state.selected_frameworks)
    if st.button(
        f"✅ Confirm {sel_count} Framework{'s' if sel_count != 1 else ''} →",
        type="primary",
        use_container_width=True,
        disabled=sel_count == 0,
    ):
        user_msg(
            f"Selected frameworks: {', '.join(st.session_state.selected_frameworks)}"
        )
        if st.session_state.get("session_id"):
            api(
                "patch",
                f"/history/{st.session_state.session_id}/frameworks",
                json={"selected_frameworks": st.session_state.selected_frameworks},
            )
        fw_str = ", ".join(f"**{f}**" for f in st.session_state.selected_frameworks)
        bot_msg(f"Excellent! You've selected {fw_str}.")
        bot_msg(
            "Now let's choose which **policy types** to generate. Select all that apply to your organization:"
        )
        st.session_state.chat_phase = "policy_types"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: policy_types
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "policy_types":
    st.markdown(
        "**Which policies do you need?** (pre-selected defaults shown — adjust as needed)"
    )
    selected_pol_types = st.multiselect(
        "Policy Types",
        options=list(POLICY_TYPES_MAP.keys()),
        default=st.session_state.policy_types,
        format_func=lambda x: POLICY_TYPES_MAP[x],
        label_visibility="collapsed",
    )
    fw_choices = st.multiselect(
        "Generate for frameworks",
        options=st.session_state.selected_frameworks,
        default=st.session_state.selected_frameworks,
        format_func=lambda x: x,
        label_visibility="visible",
    )

    if st.button(
        "Next: Choose Procedure Types →", type="primary", use_container_width=True
    ):
        if not selected_pol_types:
            st.warning("Please select at least one policy type.")
        elif not fw_choices:
            st.warning("Please select at least one framework.")
        else:
            st.session_state.policy_types = selected_pol_types
            st.session_state.gen_frameworks = fw_choices
            user_msg(
                f"Policy types: {', '.join(POLICY_TYPES_MAP[t] for t in selected_pol_types)} | Frameworks: {', '.join(fw_choices)}"
            )
            bot_msg(
                f"Got it — **{len(selected_pol_types)} policies** for **{', '.join(fw_choices)}**."
            )
            bot_msg("Now choose which **operational procedures** to generate:")
            st.session_state.chat_phase = "proc_types"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: proc_types
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "proc_types":
    st.markdown("**Which procedures do you need?**")
    selected_proc_types = st.multiselect(
        "Procedure Types",
        options=list(PROCEDURE_TYPES_MAP.keys()),
        default=st.session_state.procedure_types,
        format_func=lambda x: PROCEDURE_TYPES_MAP[x],
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Policy Types", use_container_width=True):
            st.session_state.chat_phase = "policy_types"
            st.rerun()
    with col2:
        if st.button(
            "⚡ Generate Everything →", type="primary", use_container_width=True
        ):
            if not selected_proc_types:
                st.warning("Please select at least one procedure type.")
            else:
                st.session_state.procedure_types = selected_proc_types
                user_msg(
                    f"Procedure types: {', '.join(PROCEDURE_TYPES_MAP[t] for t in selected_proc_types)}"
                )
                bot_msg(
                    f"Perfect! Generating **{len(st.session_state.policy_types)} policies** and **{len(selected_proc_types)} procedures** for **{', '.join(st.session_state.gen_frameworks)}**. This may take a minute or two… ⚙️"
                )
                st.session_state.chat_phase = "generating"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: generating
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "generating":
    frameworks_to_gen = st.session_state.gen_frameworks or st.session_state.selected_frameworks
    all_policies = []
    all_procedures = []
    failed = []

    for fw in frameworks_to_gen:
        with st.spinner(f"🤖 Generating policies for {fw}..."):
            pol_data, pol_err = api(
                "post", "/policies/generate",
                json={
                    "org_description": st.session_state.org_description,
                    "org_name": st.session_state.org_name,
                    "framework": fw,
                    "policy_types": st.session_state.policy_types,
                },
            )
        if pol_err:
            failed.append(f"{fw} policies: {pol_err}")
        else:
            all_policies.extend(pol_data.get("policies", []))

        with st.spinner(f"🤖 Generating procedures for {fw}..."):
            proc_data, proc_err = api(
                "post", "/procedures/generate",
                json={
                    "org_description": st.session_state.org_description,
                    "org_name": st.session_state.org_name,
                    "framework": fw,
                    "procedure_types": st.session_state.procedure_types,
                },
            )
        if proc_err:
            failed.append(f"{fw} procedures: {proc_err}")
        else:
            all_procedures.extend(proc_data.get("procedures", []))

    if failed:
        bot_msg(f"⚠️ Some generations failed:\n" + "\n".join(failed))

    st.session_state.policies = {"policies": all_policies, "summary": f"Generated {len(all_policies)} policies across {', '.join(frameworks_to_gen)}."}
    st.session_state.procedures = {"procedures": all_procedures, "summary": f"Generated {len(all_procedures)} procedures across {', '.join(frameworks_to_gen)}."}
    bot_msg(
        f"✅ All documents generated!\n\n📋 **{len(all_policies)} Policies** · 📑 **{len(all_procedures)} Procedures** across **{', '.join(frameworks_to_gen)}**\n\nDownload the full compliance document below or review each document."
    )
    st.session_state.chat_phase = "done"
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: done — show results + docx export
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "done":
    pol_data = st.session_state.policies
    proc_data = st.session_state.procedures
    framework = "_".join(st.session_state.gen_frameworks) if st.session_state.gen_frameworks else (
        st.session_state.selected_frameworks[0] if st.session_state.selected_frameworks else ""
    )

    st.markdown("---")

    # ── DOCX Export ──────────────────────────────────────────────────────────
    st.markdown("### 📄 Export Full Compliance Document")
    docx_payload = {
        "org_name": st.session_state.org_name or st.session_state.org_description,
        "framework": framework,
        "policies": pol_data.get("policies", []) if pol_data else [],
        "procedures": proc_data.get("procedures", []) if proc_data else [],
    }
    docx_out_path = os.path.join(os.environ.get("TEMP", "/tmp"), "compliance_export.docx")
    docx_err = generate_docx(docx_payload, docx_out_path)
    if not docx_err and os.path.exists(docx_out_path):
        with open(docx_out_path, "rb") as f:
            docx_bytes = f.read()
        os.unlink(docx_out_path)
        fname = f"{(st.session_state.org_name or 'Compliance').replace(' ','_')}_{framework}_compliance.docx"
        st.download_button(
            "📄 Download Full Compliance Document (.docx)",
            data=docx_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            type="primary",
        )
        st.caption(
            "Contains cover page, all policies, and all procedures — formatted and ready to use."
        )
    else:
        st.warning(
            f"⚠️ DOCX export failed: {docx_err}. You can still download JSON below."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Policies ─────────────────────────────────────────────────────────────
    if pol_data and pol_data.get("policies"):
        st.markdown(
            f'<div class="summary-box">✅ {html.escape(pol_data.get("summary",""))}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇ Download Policies JSON",
            data=json.dumps(pol_data, indent=2),
            file_name=f"{framework}_policies.json",
            mime="application/json",
            use_container_width=True,
        )
        st.markdown(f"#### 📋 Policies ({len(pol_data['policies'])})")
        for pi, policy in enumerate(pol_data["policies"]):
            with st.expander(f"📄 {policy['title']}", expanded=False):
                render_policy(policy, f"dl_pol_done_{pi}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Procedures ───────────────────────────────────────────────────────────
    if proc_data and proc_data.get("procedures"):
        st.markdown(
            f'<div class="summary-box">✅ {html.escape(proc_data.get("summary",""))}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇ Download Procedures JSON",
            data=json.dumps(proc_data, indent=2),
            file_name=f"{framework}_procedures.json",
            mime="application/json",
            use_container_width=True,
        )
        st.markdown(f"#### 📑 Procedures ({len(proc_data['procedures'])})")
        for pi, proc in enumerate(proc_data["procedures"]):
            with st.expander(f"📋 {proc['title']}", expanded=False):
                h = html
                st.markdown(
                    f"""
                <div class="doc-card">
                  <h3>{h.escape(proc.get('title',''))}</h3>
                  <div class="doc-meta-bar">
                    <span class="doc-meta-item"><b>ID</b> {h.escape(proc.get('procedure_id',''))}</span>
                    <span class="doc-meta-item"><b>Frequency</b> {h.escape(proc.get('frequency','') or '')}</span>
                    <span class="doc-meta-item"><b>Owner</b> {h.escape(proc.get('owner','') or '')}</span>
                  </div>
                </div>""",
                    unsafe_allow_html=True,
                )
                for label, key in [
                    ("Purpose", "purpose"),
                    ("Scope", "scope"),
                    ("Escalation Path", "escalation_path"),
                ]:
                    if proc.get(key):
                        st.markdown(
                            f'<div class="policy-section"><div class="policy-section-title">{label}</div></div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(proc[key])
                st.markdown(f"**Steps ({len(proc.get('steps',[]))})**")
                for step in proc.get("steps", []):
                    tools_html = "".join(
                        f'<span class="pill">{h.escape(t)}</span>'
                        for t in step.get("tools_required", [])
                    )
                    st.markdown(
                        f"""
                    <div class="step-card">
                      <div class="step-num">Step {step['step_number']}</div>
                      <h4>{h.escape(step.get('title',''))}</h4>
                      <div class="step-meta">
                        <span>👤 <b>{h.escape(step.get('responsible_role',''))}</b></span>
                        <span>⏱ <b>{h.escape(step.get('timeline',''))}</b></span>
                      </div>
                      {f'<div style="margin-top:0.4rem">{tools_html}</div>' if tools_html else ''}
                    </div>""",
                        unsafe_allow_html=True,
                    )
                    st.markdown(step.get("description", ""))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 Start New Compliance Run", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()
