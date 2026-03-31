"""
ComplianceIQ — Chatbot Interface
Conversational wizard: profile → frameworks → AI-generated personalization questions → generate → export .docx
"""

import json
import html
import os
import re
import requests
import streamlit as st
from backend.config.llm_config import get_llm_with_fallback
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
st.markdown("""
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
    max-height: 320px; overflow-y: auto;
    padding: 0.5rem 0.2rem; display: flex; flex-direction: column;
    scrollbar-width: thin; scrollbar-color: #2d3748 transparent;
  }
  .chat-container::-webkit-scrollbar { width: 4px; }
  .chat-container::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 2px; }

  .chat-bot {
    background: #1a2035; border: 1px solid #2d3748;
    border-radius: 14px 14px 14px 2px;
    padding: 0.9rem 1.2rem; margin: 0.5rem 0;
    color: #e2e8f0; font-size: 0.92rem; line-height: 1.6; max-width: 85%;
  }
  .chat-user {
    background: linear-gradient(135deg, #3a4a9e, #553a8a);
    border: 1px solid #667eea; border-radius: 14px 14px 2px 14px;
    padding: 0.9rem 1.2rem; margin: 0.5rem 0 0.5rem auto;
    color: #f0f4ff; font-size: 0.92rem; line-height: 1.6;
    max-width: 75%; text-align: right;
  }
  .chat-label-bot { color: #667eea; font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.08em; margin-bottom: 2px; }
  .chat-label-user { color: #a0aec0; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.08em; margin-bottom: 2px; text-align: right; }

  /* Question card for personalization phase */
  .q-card {
    background: #141824; border: 1px solid #2d3748; border-radius: 12px;
    padding: 1.2rem 1.4rem; margin-bottom: 0.8rem;
  }
  .q-label { color: #667eea; font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }
  .q-hint { color: #718096; font-size: 0.78rem; margin-top: 0.3rem; }

  /* Progress bar */
  .progress-bar { display: flex; gap: 4px; margin-bottom: 1.5rem; align-items: center; }
  .prog-step { flex: 1; height: 4px; border-radius: 2px; background: #2d3748; transition: background 0.3s; }
  .prog-step.done { background: #667eea; }
  .prog-step.active { background: linear-gradient(90deg, #667eea, #764ba2); }
  .prog-label { color: #718096; font-size: 0.72rem; margin-left: 6px; white-space: nowrap; }

  /* Framework cards */
  .fw-card { background: #1a202c; border: 2px solid #2d3748; border-radius: 12px; padding: 1rem; transition: all 0.2s; height: 100%; }
  .fw-card.selected { border-color: #667eea; background: #1e2a4a; }
  .fw-card h4 { color: #e2e8f0; font-size: 0.9rem; margin: 0.3rem 0; }
  .fw-card p  { color: #718096; font-size: 0.78rem; margin: 0; }
  .score-bar { height: 4px; background: #2d3748; border-radius: 2px; margin: 0.5rem 0; }
  .score-fill { height: 4px; border-radius: 2px; background: linear-gradient(90deg, #667eea, #764ba2); }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.68rem; font-weight: 600; background: #2d3748; color: #a0aec0; margin-bottom: 0.3rem; }
  .badge.mandatory { background: #2d1515; color: #fc8181; }

  /* Doc section */
  .doc-card { background: #13171f; border: 1px solid #2d3748; border-radius: 14px; padding: 1.5rem 1.8rem; margin-bottom: 1rem; }
  .doc-card h3 { color: #f0f4ff; font-size: 1.1rem; font-weight: 700; margin: 0 0 0.5rem; }
  .doc-meta-bar { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 1px solid #2d3748; }
  .doc-meta-item { background: #1e2535; border: 1px solid #2d3748; border-radius: 6px; padding: 3px 10px; font-size: 0.73rem; color: #90a0b7; }
  .doc-meta-item b { color: #c8d6e8; }
  .policy-section { margin: 0.8rem 0; padding: 0.7rem 1rem; background: #1a2030; border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; }
  .policy-section-title { color: #667eea; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
  .ref-tag { display: inline-block; background: #1a2a4a; color: #7eb8f7; border: 1px solid #2b4c7e; border-radius: 4px; padding: 2px 7px; font-size: 0.7rem; margin: 3px 2px 0; }
  .step-card { background: #1a202c; border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }
  .step-card .step-num { color: #667eea; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
  .step-card h4 { color: #e2e8f0; margin: 0.2rem 0; font-size: 0.9rem; }
  .step-meta { display: flex; gap: 1rem; margin-top: 0.4rem; flex-wrap: wrap; }
  .step-meta span { color: #718096; font-size: 0.76rem; }
  .step-meta span b { color: #a0aec0; }
  .pill { display: inline-block; background: #2d3748; color: #a0aec0; border-radius: 999px; padding: 2px 9px; font-size: 0.76rem; margin: 2px; }
  .summary-box { background: #1a2a1a; border: 1px solid #2f855a; border-radius: 10px; padding: 0.8rem 1.1rem; color: #68d391; font-size: 0.85rem; margin-bottom: 1rem; }
  .info-box { background: #1a2535; border: 1px solid #2b4c7e; border-radius: 10px; padding: 0.8rem 1.1rem; color: #7eb8f7; font-size: 0.85rem; margin-bottom: 1rem; }
  hr { border-color: #2d3748; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; }
  [data-testid="collapsedControl"] { display: block !important; visibility: visible !important; }
  section[data-testid="stSidebar"] { display: block !important; visibility: visible !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
DEFAULTS = {
    "chat_phase": "intro",
    # intro | org_name | org_desc | website | country | analyzing |
    # frameworks | doc_types | personalizing | q_index | generating | done
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
    "gen_frameworks": [],
    # personalization
    "personalization_questions": [],   # list of {key, label, hint, type, options}
    "personalization_answers": {},     # key → answer string
    "q_index": 0,                      # current question index
    "org_context": {},                 # final context dict passed to API
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
        return None, "Cannot connect to backend. Make sure the FastAPI server is running on port 8000."
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as e:
        return None, str(e)


def bot_msg(text):
    st.session_state.messages.append({"role": "bot", "content": text})


def user_msg(text):
    st.session_state.messages.append({"role": "user", "content": text})


def score_color(score):
    if score >= 0.8: return "#68d391"
    if score >= 0.6: return "#f6e05e"
    return "#fc8181"


def _md_to_html(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = text.replace('\n', '<br>')
    return text


# ─── Dynamic Question Generator (via Anthropic API) ──────────────────────────
def generate_personalization_questions(
    org_name: str,
    org_description: str,
    org_country: str,
    frameworks: list[str],
    policy_types: list[str],
    procedure_types: list[str],
) -> list[dict]:
    """
    Call the Anthropic API to generate relevant personalization questions
    based on the selected org profile, frameworks, policies, and procedures.
    Returns a list of question dicts: {key, label, hint, type, options (optional)}.
    """

    policy_names  = [POLICY_TYPES_MAP.get(p, p) for p in policy_types]
    proc_names    = [PROCEDURE_TYPES_MAP.get(p, p) for p in procedure_types]

    system_prompt = """You are a compliance documentation specialist. Your job is to generate a SHORT, focused list of personalization questions to collect the specific details needed to make compliance policies and procedures completely tailored to an organization — replacing all generic placeholders with real values.

You MUST return ONLY a valid JSON array. No explanation, no markdown, no preamble. Just the JSON array.

Each question object must have:
- "key": snake_case unique identifier (e.g. "ciso_email")
- "label": the question text shown to the user (clear, concise)
- "hint": example answer or explanation shown as placeholder/helper
- "type": one of "text", "email", "phone", "textarea", "select"
- "options": array of strings (ONLY if type is "select", otherwise omit)
- "category": one of "contacts", "tools", "roles", "processes", "legal", "technical"

Rules:
- Generate 8–14 questions total. Quality over quantity.
- Group related topics — don't ask for "CISO name" and "CISO email" as two questions; combine as "CISO contact details" (name + email in one textarea).
- Ask about: key contact roles with emails/phones, internal tools actually used (SIEM, ticketing, backup, etc.), regulatory registration numbers if applicable, specific timelines the org uses, data classification levels, retention periods, external DPA/legal contacts.
- Tailor questions to the SPECIFIC frameworks selected. E.g. GDPR → ask for DPA registration number & DPO contact; HIPAA → ask for covered entity type & Privacy Officer; PCI-DSS → ask for merchant level & acquiring bank.
- Tailor questions to the SPECIFIC policy/procedure types. E.g. incident_response → ask for SIEM tool, IR email alias; data_breach → ask for supervisory authority contact; access_review → ask for IAM tool used.
- Make questions feel like a smart compliance consultant is asking them, not a generic form.
- Skip obvious things already known (org name, country, industry — already collected).
"""

    user_prompt = f"""Generate personalization questions for:

Organization: {org_name}
Description: {org_description}
Country/Region: {org_country}
Selected Frameworks: {', '.join(frameworks)}
Policies to generate: {', '.join(policy_names)}
Procedures to generate: {', '.join(proc_names)}

Return ONLY the JSON array of question objects."""

    try:
        llm = get_llm_with_fallback(temperature=0.3)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        raw = llm.call([{"role": "user", "content": full_prompt}])
        if hasattr(raw, "content"):
            raw = raw.content
        raw = str(raw).strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        questions = json.loads(raw)
        if isinstance(questions, list) and questions:
            return questions
    except Exception:
        pass  # Fall back to static questions below

    # ── Static fallback (framework-aware) ─────────────────────────────────────
    base_questions = [
        {"key": "ciso_contact", "label": "CISO / Security Officer — name and email", "hint": "e.g. Jane Smith, ciso@acme.com", "type": "text", "category": "contacts"},
        {"key": "dpo_contact", "label": "Data Protection Officer — name and email", "hint": "e.g. John Doe, dpo@acme.com", "type": "text", "category": "contacts"},
        {"key": "incident_email", "label": "Security incident reporting email / alias", "hint": "e.g. security@acme.com or incidents@acme.com", "type": "email", "category": "contacts"},
        {"key": "legal_contact", "label": "Legal / Compliance counsel contact", "hint": "e.g. General Counsel or external firm name + email", "type": "text", "category": "contacts"},
        {"key": "siem_tool", "label": "SIEM / log monitoring tool used", "hint": "e.g. Splunk, Microsoft Sentinel, Datadog, IBM QRadar", "type": "text", "category": "tools"},
        {"key": "ticketing_tool", "label": "Incident & task ticketing system", "hint": "e.g. JIRA, ServiceNow, Freshdesk, Linear", "type": "text", "category": "tools"},
        {"key": "iam_tool", "label": "Identity & Access Management (IAM) tool", "hint": "e.g. Okta, Azure AD, Google Workspace, AWS IAM", "type": "text", "category": "tools"},
        {"key": "backup_tool", "label": "Backup & recovery tool", "hint": "e.g. Veeam, AWS Backup, Acronis, Commvault", "type": "text", "category": "tools"},
        {"key": "data_classification", "label": "Data classification levels your org uses", "hint": "e.g. Public, Internal, Confidential, Restricted", "type": "text", "category": "processes"},
        {"key": "retention_period", "label": "Standard data retention period", "hint": "e.g. 3 years for customer data, 7 years for financial records", "type": "text", "category": "processes"},
        {"key": "incident_response_sla", "label": "Incident response SLA / notification window", "hint": "e.g. 72 hours for breach notification (GDPR), 60 days (HIPAA)", "type": "text", "category": "processes"},
        {"key": "employee_count", "label": "Approximate employee count", "hint": "e.g. 50, 200–500, 1000+", "type": "text", "category": "technical"},
    ]
    if "GDPR" in frameworks:
        base_questions.insert(2, {"key": "dpa_registration", "label": "ICO / DPA registration number (if applicable)", "hint": "e.g. ZA123456 (UK ICO) or leave blank if not yet registered", "type": "text", "category": "legal"})
    if "HIPAA" in frameworks:
        base_questions.insert(2, {"key": "covered_entity_type", "label": "HIPAA covered entity type", "hint": "e.g. Healthcare Provider, Health Plan, Business Associate", "type": "select", "options": ["Healthcare Provider", "Health Plan", "Health Clearinghouse", "Business Associate"], "category": "legal"})
    if "PCI-DSS" in frameworks:
        base_questions.insert(2, {"key": "merchant_level", "label": "PCI-DSS merchant / service provider level", "hint": "e.g. Level 1 (>6M transactions/yr), Level 2, Level 3, Level 4", "type": "select", "options": ["Level 1", "Level 2", "Level 3", "Level 4", "Service Provider Level 1", "Service Provider Level 2"], "category": "legal"})
    return base_questions


# ─── Progress Indicator ───────────────────────────────────────────────────────
def render_progress():
    phase = st.session_state.chat_phase
    steps = ["Org Info", "Frameworks", "Doc Types", "Personalize", "Generate"]
    phase_groups = [
        ["intro", "org_name", "org_desc", "website", "country", "analyzing"],
        ["frameworks"],
        ["doc_types"],
        ["personalizing", "q_index"],
        ["generating", "done"],
    ]
    current_group = next((i for i, g in enumerate(phase_groups) if phase in g), 0)
    pills = ""
    for i, step in enumerate(steps):
        if i < current_group:   cls = "done"
        elif i == current_group: cls = "active"
        else:                    cls = ""
        pills += f'<div class="prog-step {cls}"></div>'
    st.markdown(
        f'<div class="progress-bar">{pills}'
        f'<span class="prog-label">Step {current_group+1}/5 · {steps[current_group]}</span></div>',
        unsafe_allow_html=True,
    )


# ─── Chat Renderer ────────────────────────────────────────────────────────────
def render_chat():
    msgs_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "bot":
            msgs_html += f'<div class="chat-label-bot">🛡️ ComplianceIQ</div><div class="chat-bot">{_md_to_html(msg["content"])}</div>'
        else:
            msgs_html += f'<div class="chat-label-user">You</div><div class="chat-user">{html.escape(msg["content"])}</div>'
    st.markdown(f'<div class="chat-container" id="chat-box">{msgs_html}</div>', unsafe_allow_html=True)
    components.html(
        '<script>'
        'function s(){var e=window.parent.document.querySelectorAll(".chat-container");'
        'if(e.length){e[e.length-1].scrollTop=e[e.length-1].scrollHeight;}else{setTimeout(s,150);}}'
        'setTimeout(s,100);</script>',
        height=1,
    )


# ─── DOCX Generation ─────────────────────────────────────────────────────────
def generate_docx(payload: dict, out_path: str) -> str | None:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from datetime import datetime as dt

        doc = Document()
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1.2)
            section.right_margin = Inches(1.2)

        def sc(run, hex_c):
            r, g, b = int(hex_c[0:2],16), int(hex_c[2:4],16), int(hex_c[4:6],16)
            run.font.color.rgb = RGBColor(r, g, b)

        def h1(t):
            p = doc.add_heading(t, level=1)
            p.runs[0].font.size = Pt(18); sc(p.runs[0], "1a1a2e")

        def h2(t):
            p = doc.add_heading(t, level=2)
            p.runs[0].font.size = Pt(14); sc(p.runs[0], "2d3a6e")

        def h3(t):
            p = doc.add_paragraph()
            run = p.add_run(t); run.bold = True; run.font.size = Pt(11); sc(run, "4a5fa8")

        def meta(label, value):
            if not value: return
            p = doc.add_paragraph()
            r1 = p.add_run(f"{label}: "); r1.bold = True; r1.font.size = Pt(9); sc(r1, "444444")
            r2 = p.add_run(value); r2.font.size = Pt(9); sc(r2, "555555")
            p.paragraph_format.space_after = Pt(2)

        def clean_inline(text):
            text = re.sub(r'\*{3}(.+?)\*{3}', r'\1', text)
            text = re.sub(r'\*{2}(.+?)\*{2}', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'_{2}(.+?)_{2}', r'\1', text)
            text = re.sub(r'_(.+?)_', r'\1', text)
            text = re.sub(r'`(.+?)`', r'\1', text)
            text = re.sub(r'^#{1,6}\s*', '', text)
            return text.strip()

        def add_inline_runs(paragraph, text):
            pattern = re.compile(r'(\*{2}.+?\*{2}|\*[^*]+?\*)')
            for part in pattern.split(text):
                if part.startswith('**') and part.endswith('**'):
                    run = paragraph.add_run(part[2:-2]); run.bold = True; run.font.size = Pt(10)
                elif part.startswith('*') and part.endswith('*'):
                    run = paragraph.add_run(part[1:-1]); run.italic = True; run.font.size = Pt(10)
                elif part:
                    run = paragraph.add_run(part); run.font.size = Pt(10)

        def body(text):
            if not text: return
            for line in text.split("\n"):
                line = line.rstrip()
                if not line:
                    doc.add_paragraph().paragraph_format.space_after = Pt(2); continue
                if re.match(r'^#{1,6}\s+', line):
                    h3(clean_inline(re.sub(r'^#{1,6}\s+', '', line)))
                elif re.match(r'^[-*+]\s+', line):
                    p = doc.add_paragraph(style='List Bullet')
                    add_inline_runs(p, re.sub(r'^[-*+]\s+', '', line))
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.left_indent = Inches(0.25)
                elif re.match(r'^\d+\.\s+', line):
                    p = doc.add_paragraph(style='List Number')
                    add_inline_runs(p, re.sub(r'^\d+\.\s+', '', line))
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.left_indent = Inches(0.25)
                else:
                    p = doc.add_paragraph()
                    add_inline_runs(p, line)
                    p.paragraph_format.space_after = Pt(4)

        org_name   = payload.get("org_name", "Your Organization")
        framework  = payload.get("framework", "")
        policies   = payload.get("policies", [])
        procedures = payload.get("procedures", [])

        # Cover
        doc.add_paragraph()
        cp = doc.add_paragraph("Compliance Documentation")
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.runs[0].bold = True; cp.runs[0].font.size = Pt(28); sc(cp.runs[0], "1a1a2e")
        p = doc.add_paragraph(org_name); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.size = Pt(18); sc(p.runs[0], "4a5fa8")
        p = doc.add_paragraph(f"Framework: {framework}"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].italic = True; p.runs[0].font.size = Pt(12); sc(p.runs[0], "718096")
        p = doc.add_paragraph(f"Generated: {dt.now().strftime('%d %B %Y')}"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.size = Pt(10); sc(p.runs[0], "718096")
        p = doc.add_paragraph("CONFIDENTIAL — INTERNAL USE ONLY"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True; p.runs[0].font.size = Pt(9); sc(p.runs[0], "c0392b")

        if policies:
            doc.add_page_break(); h1("Part I — Compliance Policies")
            for pol in policies:
                doc.add_page_break(); h2(pol.get("title", ""))
                meta("Policy ID", pol.get("policy_id")); meta("Version", pol.get("version"))
                meta("Effective Date", pol.get("effective_date")); meta("Review Date", pol.get("review_date"))
                meta("Classification", pol.get("classification")); meta("Owner", pol.get("owner"))
                meta("Applicable To", pol.get("applicable_to"))
                doc.add_paragraph().paragraph_format.space_after = Pt(4)
                for sec in pol.get("sections", []):
                    h3(sec.get("title", "")); body(sec.get("content", ""))
                    refs = sec.get("references", [])
                    if refs:
                        rp = doc.add_paragraph(f"References: {' · '.join(refs)}")
                        rp.runs[0].italic = True; rp.runs[0].font.size = Pt(8); sc(rp.runs[0], "4a7ab5")

        if procedures:
            doc.add_page_break(); h1("Part II — Operational Procedures")
            for proc in procedures:
                doc.add_page_break(); h2(proc.get("title", ""))
                meta("Procedure ID", proc.get("procedure_id")); meta("Frequency", proc.get("frequency"))
                meta("Owner", proc.get("owner")); meta("Framework", proc.get("framework"))
                doc.add_paragraph().paragraph_format.space_after = Pt(4)
                for label, key in [("Purpose","purpose"),("Scope","scope"),("Escalation Path","escalation_path")]:
                    if proc.get(key): h3(label); body(proc[key])
                if proc.get("steps"):
                    h3("Procedure Steps")
                    for step in proc["steps"]:
                        sp = doc.add_paragraph()
                        r1 = sp.add_run(f"Step {step.get('step_number')}: "); r1.bold = True; r1.font.size = Pt(10); sc(r1, "4a5fa8")
                        r2 = sp.add_run(step.get("title", "")); r2.bold = True; r2.font.size = Pt(10)
                        meta("Responsible", step.get("responsible_role"))
                        meta("Timeline", step.get("timeline"))
                        tools = ", ".join(step.get("tools_required", []))
                        meta("Tools", tools or None)
                        body(step.get("description", ""))

        doc.save(out_path)
        return None
    except Exception as e:
        return str(e)


def render_policy(p, dl_key):
    h = html
    meta_items = "".join([
        f"<span class='doc-meta-item'><b>ID</b> {h.escape(p.get('policy_id',''))}</span>",
        f"<span class='doc-meta-item'><b>v{h.escape(p.get('version',''))}</b></span>",
        f"<span class='doc-meta-item'><b>Effective</b> {h.escape(p.get('effective_date','') or '')}</span>",
        f"<span class='doc-meta-item'><b>Review</b> {h.escape(p.get('review_date','') or '')}</span>",
        f"<span class='doc-meta-item'>{h.escape(p.get('classification','') or '')}</span>",
    ])
    st.markdown(f"""
    <div class="doc-card">
      <h3>{h.escape(p.get('title',''))}</h3>
      <div class="doc-meta-bar">{meta_items}</div>
      <div class="doc-meta-bar" style="border-bottom:none;padding-bottom:0;margin-bottom:0">
        <span class="doc-meta-item"><b>Owner</b> {h.escape(p.get('owner','') or '')}</span>
      </div>
    </div>""", unsafe_allow_html=True)
    for sec in p.get("sections", []):
        refs_html = " ".join(f'<span class="ref-tag">{h.escape(r)}</span>' for r in sec.get("references", []))
        st.markdown(f'<div class="policy-section"><div class="policy-section-title">{h.escape(sec.get("title",""))}</div></div>', unsafe_allow_html=True)
        st.markdown(sec.get("content", ""))
        if refs_html:
            st.markdown(f'<div style="margin-top:0.3rem;margin-bottom:0.6rem">{refs_html}</div>', unsafe_allow_html=True)
    st.download_button("⬇ Download JSON", data=json.dumps(p, indent=2),
        file_name=f"{p.get('policy_id','policy')}.json", mime="application/json", key=dl_key)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ ComplianceIQ")
    st.markdown("---")
    sidebar_sel = st.radio("Navigation", ["chat", "history"],
        index=0 if st.session_state.page == "chat" else 1,
        format_func=lambda x: "💬 Chat Wizard" if x == "chat" else "🗂️ History",
        label_visibility="collapsed")
    if sidebar_sel != st.session_state.page:
        st.session_state.page = sidebar_sel; st.rerun()
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
st.markdown("""
<div class="hero">
  <h1>🛡️ ComplianceIQ</h1>
  <p>AI-powered compliance intelligence — chat your way to deeply personalized policies & procedures</p>
</div>
""", unsafe_allow_html=True)

# ─── HISTORY PAGE ─────────────────────────────────────────────────────────────
if st.session_state.page == "history":
    col_nav1, col_nav2, _ = st.columns([1, 1, 6])
    with col_nav1:
        if st.button("💬 Chat", use_container_width=True, type="secondary"):
            st.session_state.page = "chat"; st.rerun()
    with col_nav2:
        st.button("🗂️ History", use_container_width=True, type="primary")
    st.subheader("Past Compliance Sessions")
    data, err = api("get", "/history?limit=100")
    if err:
        st.error(f"❌ {err}")
    elif not data["sessions"]:
        st.info("No sessions yet. Start a chat to generate your first compliance documents.")
    else:
        sessions = data["sessions"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Sessions", len(sessions))
        c2.metric("Total Policies",    sum(s["policy_count"]    for s in sessions))
        c3.metric("Total Procedures",  sum(s["procedure_count"] for s in sessions))
        st.markdown("---")
        for s in sessions:
            with st.expander(f"🏢 {s['org_name']}  ·  {s['created_at'][:10]}  ·  {s['policy_count']} policies  ·  {s['procedure_count']} procedures", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    fw_pills = " ".join(f'<span class="pill">{f}</span>' for f in s["selected_frameworks"]) or '<span class="pill">none selected</span>'
                    st.markdown(f"""<div class="doc-card"><h3>{html.escape(s['org_name'])}</h3>
                      <div class="doc-meta-bar"><span class="doc-meta-item">{s.get('org_country') or '—'}</span>
                      <span class="doc-meta-item"><b>Session</b> #{s['session_id']}</span></div>
                      <div>{fw_pills}</div></div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📂 View Detail", key=f"load_{s['session_id']}", use_container_width=True):
                        st.session_state["history_detail_id"] = s["session_id"]
                    if st.button("🗑️ Delete", key=f"del_{s['session_id']}", use_container_width=True):
                        _, err2 = api("delete", f"/history/{s['session_id']}")
                        if err2: st.error(err2)
                        else: st.success("Deleted"); st.rerun()
                if st.session_state.get("history_detail_id") == s["session_id"]:
                    detail, err3 = api("get", f"/history/{s['session_id']}")
                    if err3:
                        st.error(err3)
                    else:
                        if detail["policies"] or detail["procedures"]:
                            frameworks_used = list({p.get("framework","") for p in detail["policies"]+detail["procedures"] if p.get("framework")})
                            docx_payload = {"org_name": detail["org_name"], "framework": ", ".join(frameworks_used), "policies": detail["policies"], "procedures": detail["procedures"]}
                            docx_out = os.path.join(os.environ.get("TEMP", "/tmp"), f"hist_{s['session_id']}.docx")
                            docx_err = generate_docx(docx_payload, docx_out)
                            if not docx_err and os.path.exists(docx_out):
                                with open(docx_out, "rb") as f:
                                    st.download_button("📄 Download Full Compliance Document (.docx)", data=f.read(),
                                        file_name=f"{detail['org_name'].replace(' ','_')}_compliance.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key=f"hist_docx_{s['session_id']}", use_container_width=True)
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
                                    st.markdown(f"""
                                    <div class="doc-card">
                                      <h3>{h.escape(proc.get('title',''))}</h3>
                                      <div class="doc-meta-bar">
                                        <span class="doc-meta-item"><b>ID</b> {h.escape(proc.get('procedure_id',''))}</span>
                                        <span class="doc-meta-item"><b>Frequency</b> {h.escape(proc.get('frequency','') or '')}</span>
                                        <span class="doc-meta-item"><b>Owner</b> {h.escape(proc.get('owner','') or '')}</span>
                                      </div>
                                    </div>""", unsafe_allow_html=True)
                                    for label, key in [("Purpose","purpose"),("Scope","scope"),("Escalation Path","escalation_path")]:
                                        if proc.get(key):
                                            st.markdown(f'<div class="policy-section"><div class="policy-section-title">{label}</div></div>', unsafe_allow_html=True)
                                            st.markdown(proc[key])
                                    for step in proc.get("steps", []):
                                        st.markdown(f'<div class="step-card"><div class="step-num">Step {step["step_number"]}</div><h4>{h.escape(step.get("title",""))}</h4><div class="step-meta"><span>👤 <b>{h.escape(step.get("responsible_role",""))}</b></span><span>⏱ <b>{h.escape(step.get("timeline",""))}</b></span></div></div>', unsafe_allow_html=True)
                                        st.markdown(step.get("description", ""))
                                    st.download_button("⬇ Download JSON", data=json.dumps(proc, indent=2),
                                        file_name=f"{proc.get('procedure_id','procedure')}.json",
                                        mime="application/json", key=f"dl_proc_{s['session_id']}_{pi}")
    st.stop()

# ─── CHAT PAGE ────────────────────────────────────────────────────────────────
col_nav1, col_nav2, _ = st.columns([1, 1, 6])
with col_nav1:
    st.button("💬 Chat", use_container_width=True, type="primary")
with col_nav2:
    if st.button("🗂️ History", use_container_width=True, type="secondary"):
        st.session_state.page = "history"; st.rerun()

render_progress()
phase = st.session_state.chat_phase

# ─── Initialize ───────────────────────────────────────────────────────────────
if phase == "intro" and not st.session_state.messages:
    bot_msg("👋 Welcome to **ComplianceIQ**! I'll guide you through creating deeply personalized compliance documents step by step.")
    bot_msg("Let's start with your **organization name**. What is your company called?")
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
            val = st.text_input("Organization name", placeholder="e.g. NatSteel Holdings Pte Ltd", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Send →", use_container_width=True, type="primary")
        if submitted and val.strip():
            user_msg(val.strip())
            st.session_state.org_name = val.strip()
            bot_msg(f"Great, **{val.strip()}** noted! 🏢")
            bot_msg("Now describe your organization in a few words — industry, region, type. For example: *Indian healthcare SaaS startup* or *EU fintech payment processor*.")
            st.session_state.chat_phase = "org_desc"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: org_desc
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "org_desc":
    examples = ["Indian healthcare SaaS startup", "US fintech payment processor", "EU ecommerce retail company", "Global manufacturing enterprise"]
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        with col:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                user_msg(ex); st.session_state.org_description = ex
                bot_msg(f"Got it — *{ex}*.")
                bot_msg("Do you have a **website URL**? It helps our AI do a deeper analysis. Type it or press **Skip**.")
                st.session_state.chat_phase = "website"; st.rerun()
    with st.form("form_org_desc", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            val = st.text_input("Organization description", placeholder="e.g. Indian healthcare SaaS startup", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Send →", use_container_width=True, type="primary")
        if submitted and val.strip():
            user_msg(val.strip()); st.session_state.org_description = val.strip()
            bot_msg(f"Got it — *{val.strip()}*.")
            bot_msg("Do you have a **website URL**? Type it or press **Skip**.")
            st.session_state.chat_phase = "website"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: website
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "website":
    with st.form("form_website", clear_on_submit=True):
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            val = st.text_input("Website URL", placeholder="https://example.com", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Send →", use_container_width=True, type="primary")
        with col3:
            skipped = st.form_submit_button("Skip ⟶", use_container_width=True)
        if submitted and val.strip():
            user_msg(val.strip()); st.session_state.org_website = val.strip()
            bot_msg(f"Website noted: `{val.strip()}`")
            bot_msg("Which **country** is your organization headquartered in?")
            st.session_state.chat_phase = "country"; st.rerun()
        if skipped:
            user_msg("(Skipping website)")
            bot_msg("No problem! Which **country** is your organization headquartered in?")
            st.session_state.chat_phase = "country"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: country
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "country":
    suggestions = ["India", "USA", "Germany", "Singapore", "UK", "Australia"]
    cols = st.columns(len(suggestions))
    for col, c in zip(cols, suggestions):
        with col:
            if st.button(c, key=f"country_{c}", use_container_width=True):
                user_msg(c); st.session_state.org_country = c
                bot_msg(f"**{c}** — perfect. Analyzing your organization now… ⚙️")
                st.session_state.chat_phase = "analyzing"; st.rerun()
    with st.form("form_country", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            val = st.text_input("Country", placeholder="e.g. India, USA, Germany", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Send →", use_container_width=True, type="primary")
        if submitted and val.strip():
            user_msg(val.strip()); st.session_state.org_country = val.strip()
            bot_msg(f"**{val.strip()}** — perfect. Analyzing your organization now… ⚙️")
            st.session_state.chat_phase = "analyzing"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: analyzing
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "analyzing":
    with st.spinner("🤖 AI agents analyzing your organization..."):
        data, err = api("post", "/profile", json={
            "description": st.session_state.org_description,
            "website": st.session_state.org_website or None,
            "country": st.session_state.org_country or None,
        })
    if err:
        bot_msg(f"❌ Analysis failed: {err}")
        st.session_state.chat_phase = "org_name"; st.rerun()
    else:
        st.session_state.profile = data
        st.session_state.session_id = data.get("session_id")
        st.session_state.selected_frameworks = [fw["id"] for fw in data["recommended_frameworks"] if fw["relevance_score"] >= 0.7]
        industries = ", ".join(data.get("industries_detected", [])) or "—"
        regions    = ", ".join(data.get("regions_detected", []))    or "—"
        fw_count   = len(data.get("recommended_frameworks", []))
        bot_msg(f"✅ Analysis complete!\n\n**{data.get('org_type','')}** detected.\n\n📌 *{data.get('analysis_summary','')}*\n\n🏭 Industries: **{industries}** | 🌍 Regions: **{regions}**\n\nFound **{fw_count} applicable compliance frameworks**. Select which ones to use:")
        st.session_state.chat_phase = "frameworks"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: frameworks
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "frameworks":
    profile    = st.session_state.profile
    frameworks = profile.get("recommended_frameworks", [])
    selected   = st.session_state.selected_frameworks

    st.markdown("**Select the compliance frameworks that apply to your organization:**")
    st.caption("Pre-selected based on AI recommendations (≥70% relevance). Click to toggle.")

    for row_start in range(0, len(frameworks), 3):
        row  = frameworks[row_start:row_start+3]
        cols = st.columns(3)
        for col, fw in zip(cols, row):
            with col:
                is_sel     = fw["id"] in selected
                badge      = '<span class="badge mandatory">MANDATORY</span>' if fw["is_mandatory"] else '<span class="badge">RECOMMENDED</span>'
                score_pct  = int(fw["relevance_score"] * 100)
                color      = score_color(fw["relevance_score"])
                card_class = "fw-card selected" if is_sel else "fw-card"
                st.markdown(f"""
                <div class="{card_class}">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.4rem">{fw['icon']}</span>{badge}
                  </div>
                  <h4>{fw['id']} — {fw['name'][:28]}{'…' if len(fw['name'])>28 else ''}</h4>
                  <div class="score-bar"><div class="score-fill" style="width:{score_pct}%;background:{color}"></div></div>
                  <p style="color:{color};font-weight:600;font-size:0.76rem">{score_pct}% relevance</p>
                  <p style="margin-top:0.3rem">{fw['relevance_reason'][:90]}{'…' if len(fw['relevance_reason'])>90 else ''}</p>
                </div>""", unsafe_allow_html=True)
                label    = "✓ Selected" if is_sel else "+ Select"
                btn_type = "primary" if is_sel else "secondary"
                if st.button(label, key=f"fw_{fw['id']}", use_container_width=True, type=btn_type):
                    if is_sel: st.session_state.selected_frameworks.remove(fw["id"])
                    else:      st.session_state.selected_frameworks.append(fw["id"])
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    sel_count = len(st.session_state.selected_frameworks)
    if st.button(f"✅ Confirm {sel_count} Framework{'s' if sel_count != 1 else ''} →", type="primary",
                 use_container_width=True, disabled=sel_count == 0):
        user_msg(f"Selected frameworks: {', '.join(st.session_state.selected_frameworks)}")
        if st.session_state.get("session_id"):
            api("patch", f"/history/{st.session_state.session_id}/frameworks",
                json={"selected_frameworks": st.session_state.selected_frameworks})
        fw_str = ", ".join(f"**{f}**" for f in st.session_state.selected_frameworks)
        bot_msg(f"Excellent! You've selected {fw_str}.")
        bot_msg("Now choose which **policies** and **procedures** to generate:")
        st.session_state.chat_phase = "doc_types"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: doc_types — choose policies + procedures together
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "doc_types":
    col_pol, col_proc = st.columns(2)
    with col_pol:
        st.markdown("**📋 Policies to generate**")
        selected_pol_types = st.multiselect(
            "Policy Types", options=list(POLICY_TYPES_MAP.keys()),
            default=st.session_state.policy_types,
            format_func=lambda x: POLICY_TYPES_MAP[x], label_visibility="collapsed")
    with col_proc:
        st.markdown("**📑 Procedures to generate**")
        selected_proc_types = st.multiselect(
            "Procedure Types", options=list(PROCEDURE_TYPES_MAP.keys()),
            default=st.session_state.procedure_types,
            format_func=lambda x: PROCEDURE_TYPES_MAP[x], label_visibility="collapsed")

    fw_choices = st.multiselect(
        "Generate for frameworks",
        options=st.session_state.selected_frameworks,
        default=st.session_state.selected_frameworks,
        label_visibility="visible")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Next: Personalize Details →", type="primary", use_container_width=True):
        if not selected_pol_types and not selected_proc_types:
            st.warning("Please select at least one policy or procedure type.")
        elif not fw_choices:
            st.warning("Please select at least one framework.")
        else:
            st.session_state.policy_types    = selected_pol_types
            st.session_state.procedure_types = selected_proc_types
            st.session_state.gen_frameworks  = fw_choices
            pol_str  = ", ".join(POLICY_TYPES_MAP[t]     for t in selected_pol_types)
            proc_str = ", ".join(PROCEDURE_TYPES_MAP[t]  for t in selected_proc_types)
            user_msg(f"Policies: {pol_str or 'none'} | Procedures: {proc_str or 'none'} | Frameworks: {', '.join(fw_choices)}")
            bot_msg(f"Got it — **{len(selected_pol_types)} policies** and **{len(selected_proc_types)} procedures** for **{', '.join(fw_choices)}**.")
            bot_msg("Now I'll ask you a few targeted questions so the documents use your **real contacts, tools, and processes** instead of generic placeholders. Generating questions… 🔍")
            st.session_state.chat_phase = "personalizing"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: personalizing — generate questions via AI then ask them one-by-one
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "personalizing":
    # Generate questions if not already done
    if not st.session_state.personalization_questions:
        with st.spinner("🤖 Generating personalized questions for your setup…"):
            questions = generate_personalization_questions(
                org_name        = st.session_state.org_name,
                org_description = st.session_state.org_description,
                org_country     = st.session_state.org_country,
                frameworks      = st.session_state.gen_frameworks,
                policy_types    = st.session_state.policy_types,
                procedure_types = st.session_state.procedure_types,
            )
        st.session_state.personalization_questions = questions
        st.session_state.q_index = 0
        st.session_state.personalization_answers = {}
        n = len(questions)
        bot_msg(f"I have **{n} questions** for you. Answer as many as you can — or press **Skip** if something doesn't apply. The more you fill in, the more personalized your documents will be.")
        st.rerun()

    questions = st.session_state.personalization_questions
    q_idx     = st.session_state.q_index
    answers   = st.session_state.personalization_answers
    total     = len(questions)

    # ── Progress within personalization ──────────────────────────────────────
    answered = len(answers)
    st.markdown(
        f'<div class="info-box">📝 Question <b>{min(q_idx+1, total)}</b> of <b>{total}</b> &nbsp;·&nbsp; '
        f'<b>{answered}</b> answered so far</div>',
        unsafe_allow_html=True,
    )

    if q_idx < total:
        q = questions[q_idx]
        q_key     = q.get("key", f"q_{q_idx}")
        q_label   = q.get("label", "")
        q_hint    = q.get("hint", "")
        q_type    = q.get("type", "text")
        q_options = q.get("options", [])
        q_cat     = q.get("category", "")

        cat_icons = {"contacts":"👤","tools":"🔧","roles":"👥","processes":"⚙️","legal":"⚖️","technical":"💻"}
        cat_icon  = cat_icons.get(q_cat, "📌")

        st.markdown(
            f'<div class="q-card"><div class="q-label">{cat_icon} {q_cat.upper()}</div>'
            f'<b style="color:#e2e8f0;font-size:0.95rem">{html.escape(q_label)}</b>'
            f'<div class="q-hint">💡 {html.escape(q_hint)}</div></div>',
            unsafe_allow_html=True,
        )

        with st.form(f"form_q_{q_idx}", clear_on_submit=True):
            if q_type == "select" and q_options:
                val = st.selectbox("Answer", options=["— Select one —"] + q_options, label_visibility="collapsed")
                invalid = val == "— Select one —"
            elif q_type == "textarea":
                val = st.text_area("Answer", placeholder=q_hint, height=100, label_visibility="collapsed")
                invalid = False
            else:
                placeholder = q_hint if len(q_hint) < 60 else q_hint[:57] + "…"
                val = st.text_input("Answer", placeholder=placeholder, label_visibility="collapsed")
                invalid = False

            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("Save & Next →", use_container_width=True, type="primary")
            with col2:
                skipped = st.form_submit_button("Skip ⟶", use_container_width=True)

            if submitted and not invalid and val and str(val).strip():
                answer = str(val).strip()
                user_msg(f"{q_label}: {answer}")
                st.session_state.personalization_answers[q_key] = answer
                # Brief bot acknowledgment every 3 questions
                if (q_idx + 1) % 3 == 0 and (q_idx + 1) < total:
                    remaining = total - q_idx - 1
                    bot_msg(f"Great, making progress! **{remaining} more question{'s' if remaining > 1 else ''}** to go.")
                st.session_state.q_index = q_idx + 1; st.rerun()
            if skipped:
                user_msg(f"(Skipped: {q_label})")
                st.session_state.q_index = q_idx + 1; st.rerun()

    else:
        # All questions answered/skipped — compile org_context and move on
        answered_count = len(st.session_state.personalization_answers)
        bot_msg(f"✅ All done! You provided **{answered_count}** personalization details. Generating your tailored compliance documents now — this takes 1–3 minutes… ⚙️")

        # Build org_context from answers
        ctx = dict(st.session_state.personalization_answers)
        ctx["org_name"]        = st.session_state.org_name
        ctx["org_description"] = st.session_state.org_description
        ctx["org_country"]     = st.session_state.org_country
        st.session_state.org_context = ctx
        st.session_state.chat_phase  = "generating"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: generating
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "generating":
    frameworks_to_gen = st.session_state.gen_frameworks or st.session_state.selected_frameworks
    org_context       = st.session_state.org_context
    all_policies      = []
    all_procedures    = []
    failed            = []

    for fw in frameworks_to_gen:
        if st.session_state.policy_types:
            with st.spinner(f"🤖 Generating {len(st.session_state.policy_types)} policies for **{fw}**…"):
                pol_data, pol_err = api("post", "/policies/generate", json={
                    "org_description": st.session_state.org_description,
                    "org_name":        st.session_state.org_name,
                    "framework":       fw,
                    "policy_types":    st.session_state.policy_types,
                    "org_context":     org_context,
                })
            if pol_err: failed.append(f"{fw} policies: {pol_err}")
            else:       all_policies.extend(pol_data.get("policies", []))

        if st.session_state.procedure_types:
            with st.spinner(f"🤖 Generating {len(st.session_state.procedure_types)} procedures for **{fw}**…"):
                proc_data, proc_err = api("post", "/procedures/generate", json={
                    "org_description": st.session_state.org_description,
                    "org_name":        st.session_state.org_name,
                    "framework":       fw,
                    "procedure_types": st.session_state.procedure_types,
                    "org_context":     org_context,
                })
            if proc_err: failed.append(f"{fw} procedures: {proc_err}")
            else:        all_procedures.extend(proc_data.get("procedures", []))

    if failed:
        bot_msg(f"⚠️ Some generations failed:\n" + "\n".join(failed))

    # Deduplicate across frameworks by policy_id / procedure_id
    seen_pol, seen_proc = set(), set()
    unique_policies   = [p for p in all_policies   if p.get("policy_id")    not in seen_pol  and not seen_pol.add(p.get("policy_id"))]
    unique_procedures = [p for p in all_procedures if p.get("procedure_id") not in seen_proc and not seen_proc.add(p.get("procedure_id"))]

    st.session_state.policies   = {"policies":   unique_policies,   "summary": f"Generated {len(unique_policies)} policies across {', '.join(frameworks_to_gen)}."}
    st.session_state.procedures = {"procedures": unique_procedures, "summary": f"Generated {len(unique_procedures)} procedures across {', '.join(frameworks_to_gen)}."}
    bot_msg(
        f"✅ All documents generated and personalized!\n\n"
        f"📋 **{len(unique_policies)} Policies** · 📑 **{len(unique_procedures)} Procedures** across **{', '.join(frameworks_to_gen)}**\n\n"
        f"Your real contacts, tools, and processes have been woven into every document. Download the full Word document below or review each item."
    )
    st.session_state.chat_phase = "done"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: done — results + export
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "done":
    pol_data  = st.session_state.policies
    proc_data = st.session_state.procedures
    framework = "_".join(st.session_state.gen_frameworks) if st.session_state.gen_frameworks else (
        st.session_state.selected_frameworks[0] if st.session_state.selected_frameworks else "")

    st.markdown("---")

    # ── Personalization summary ───────────────────────────────────────────────
    if st.session_state.personalization_answers:
        with st.expander("🔍 Personalization details used", expanded=False):
            for q in st.session_state.personalization_questions:
                key = q.get("key","")
                val = st.session_state.personalization_answers.get(key)
                if val:
                    st.markdown(f"**{q.get('label','')}:** {val}")

    # ── DOCX Export ──────────────────────────────────────────────────────────
    st.markdown("### 📄 Export Full Compliance Document")
    docx_payload = {
        "org_name":   st.session_state.org_name or st.session_state.org_description,
        "framework":  framework,
        "policies":   pol_data.get("policies",   []) if pol_data   else [],
        "procedures": proc_data.get("procedures", []) if proc_data else [],
    }
    docx_out_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"compliance_export_{framework}.docx")
    docx_err = generate_docx(docx_payload, docx_out_path)
    if not docx_err and os.path.exists(docx_out_path):
        with open(docx_out_path, "rb") as f:
            docx_bytes = f.read()
        os.unlink(docx_out_path)
        fname = f"{(st.session_state.org_name or 'Compliance').replace(' ','_')}_{framework}_compliance.docx"
        st.download_button(
            "📄 Download Full Compliance Document (.docx)",
            data=docx_bytes, file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True, type="primary",
        )
        st.caption("Contains cover page, all policies & procedures — formatted, personalized, ready to use.")
    else:
        st.warning(f"⚠️ DOCX export failed: {docx_err}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Policies ─────────────────────────────────────────────────────────────
    if pol_data and pol_data.get("policies"):
        st.markdown(f'<div class="summary-box">✅ {html.escape(pol_data.get("summary",""))}</div>', unsafe_allow_html=True)
        st.download_button("⬇ Download Policies JSON", data=json.dumps(pol_data, indent=2),
            file_name=f"{framework}_policies.json", mime="application/json", use_container_width=True)
        st.markdown(f"#### 📋 Policies ({len(pol_data['policies'])})")
        for pi, policy in enumerate(pol_data["policies"]):
            with st.expander(f"📄 {policy['title']}", expanded=False):
                render_policy(policy, f"dl_pol_done_{pi}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Procedures ───────────────────────────────────────────────────────────
    if proc_data and proc_data.get("procedures"):
        st.markdown(f'<div class="summary-box">✅ {html.escape(proc_data.get("summary",""))}</div>', unsafe_allow_html=True)
        st.download_button("⬇ Download Procedures JSON", data=json.dumps(proc_data, indent=2),
            file_name=f"{framework}_procedures.json", mime="application/json", use_container_width=True)
        st.markdown(f"#### 📑 Procedures ({len(proc_data['procedures'])})")
        for pi, proc in enumerate(proc_data["procedures"]):
            with st.expander(f"📋 {proc['title']}", expanded=False):
                h = html
                st.markdown(f"""
                <div class="doc-card">
                  <h3>{h.escape(proc.get('title',''))}</h3>
                  <div class="doc-meta-bar">
                    <span class="doc-meta-item"><b>ID</b> {h.escape(proc.get('procedure_id',''))}</span>
                    <span class="doc-meta-item"><b>Frequency</b> {h.escape(proc.get('frequency','') or '')}</span>
                    <span class="doc-meta-item"><b>Owner</b> {h.escape(proc.get('owner','') or '')}</span>
                  </div>
                </div>""", unsafe_allow_html=True)
                for label, key in [("Purpose","purpose"),("Scope","scope"),("Escalation Path","escalation_path")]:
                    if proc.get(key):
                        st.markdown(f'<div class="policy-section"><div class="policy-section-title">{label}</div></div>', unsafe_allow_html=True)
                        st.markdown(proc[key])
                st.markdown(f"**Steps ({len(proc.get('steps',[]))})**")
                for step in proc.get("steps", []):
                    tools_html = "".join(f'<span class="pill">{h.escape(t)}</span>' for t in step.get("tools_required", []))
                    st.markdown(f"""
                    <div class="step-card">
                      <div class="step-num">Step {step['step_number']}</div>
                      <h4>{h.escape(step.get('title',''))}</h4>
                      <div class="step-meta">
                        <span>👤 <b>{h.escape(step.get('responsible_role',''))}</b></span>
                        <span>⏱ <b>{h.escape(step.get('timeline',''))}</b></span>
                      </div>
                      {f'<div style="margin-top:0.4rem">{tools_html}</div>' if tools_html else ''}
                    </div>""", unsafe_allow_html=True)
                    st.markdown(step.get("description", ""))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 Start New Compliance Run", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()