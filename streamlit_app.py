"""
ComplianceIQ — Streamlit Frontend
4-step wizard: Profile → Frameworks → Policies → Procedures
"""

import json
import html
import requests
import streamlit as st

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

  /* Hero */
  .hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
  }
  .hero h1 { font-size: 2.4rem; font-weight: 700; color: #f7fafc; margin: 0; }
  .hero p  { color: #a0aec0; font-size: 1.05rem; margin-top: 0.5rem; }

  /* Step indicator */
  .steps {
    display: flex;
    justify-content: center;
    gap: 0;
    margin-bottom: 2rem;
  }
  .step {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1.2rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #718096;
    background: #1a202c;
    border: 1px solid #2d3748;
    margin: 0 4px;
  }
  .step.active {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-color: transparent;
  }
  .step.done { background: #1a3a2a; color: #68d391; border-color: #2f855a; }

  /* Cards */
  .fw-card {
    background: #1a202c;
    border: 2px solid #2d3748;
    border-radius: 12px;
    padding: 1.2rem;
    cursor: pointer;
    transition: all 0.2s;
    height: 100%;
  }
  .fw-card.selected {
    border-color: #667eea;
    background: #1e2a4a;
  }
  .fw-card:hover { border-color: #4a5568; }
  .fw-card .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    background: #2d3748;
    color: #a0aec0;
    margin-bottom: 0.5rem;
  }
  .fw-card .badge.mandatory { background: #2d1515; color: #fc8181; }
  .fw-card h4 { color: #e2e8f0; font-size: 0.95rem; margin: 0.3rem 0; }
  .fw-card .score-bar {
    height: 4px;
    background: #2d3748;
    border-radius: 2px;
    margin: 0.6rem 0;
  }
  .fw-card .score-fill {
    height: 4px;
    border-radius: 2px;
    background: linear-gradient(90deg, #667eea, #764ba2);
  }
  .fw-card p { color: #718096; font-size: 0.8rem; margin: 0; }

  /* Policy / Procedure cards */
  .doc-card {
    background: #13171f;
    border: 1px solid #2d3748;
    border-radius: 14px;
    padding: 1.8rem 2rem;
    margin-bottom: 1rem;
  }
  .doc-card h3 { color: #f0f4ff; font-size: 1.15rem; font-weight: 700; margin: 0 0 0.5rem; }
  .doc-meta-bar {
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    margin-bottom: 1.2rem; padding-bottom: 1rem;
    border-bottom: 1px solid #2d3748;
  }
  .doc-meta-item {
    background: #1e2535;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #90a0b7;
  }
  .doc-meta-item b { color: #c8d6e8; }
  .policy-section {
    margin: 1rem 0 0;
    padding: 0.8rem 1.2rem;
    background: #1a2030;
    border-left: 3px solid #667eea;
    border-radius: 0 8px 8px 0;
  }
  .policy-section-title {
    color: #667eea;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
  }
  .ref-tag {
    display: inline-block;
    background: #1a2a4a;
    color: #7eb8f7;
    border: 1px solid #2b4c7e;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.72rem;
    margin: 3px 2px 0;
  }

  /* Step card */
  .step-card {
    background: #1a202c;
    border-left: 3px solid #667eea;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
  }
  .step-card .step-num {
    color: #667eea;
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .step-card h4 { color: #e2e8f0; margin: 0.2rem 0; font-size: 0.95rem; }
  .step-card p  { color: #a0aec0; font-size: 0.85rem; margin: 0.3rem 0 0; }
  .step-meta { display: flex; gap: 1rem; margin-top: 0.5rem; flex-wrap: wrap; }
  .step-meta span { color: #718096; font-size: 0.78rem; }
  .step-meta span b { color: #a0aec0; }

  /* Summary box */
  .summary-box {
    background: #1a2a1a;
    border: 1px solid #2f855a;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #68d391;
    font-size: 0.88rem;
    margin-bottom: 1.5rem;
  }

  /* Pill tags */
  .pill {
    display: inline-block;
    background: #2d3748;
    color: #a0aec0;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.78rem;
    margin: 2px;
  }

  /* Divider */
  hr { border-color: #2d3748; }

  /* Hide streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; }

  /* Ensure sidebar toggle is always visible */
  [data-testid="collapsedControl"] { display: block !important; visibility: visible !important; }
  section[data-testid="stSidebar"] { display: block !important; visibility: visible !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
for key, default in {
    "step": 1,
    "profile": None,
    "selected_frameworks": [],
    "policies": None,
    "procedures": None,
    "org_name": "",
    "org_description": "",
    "org_website": "",
    "org_country": "",
    "session_id": None,
    "page": "new",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ─── Helpers ──────────────────────────────────────────────────────────────────
def api(method, path, **kwargs):
    try:
        r = getattr(requests, method)(f"{API_BASE}{path}", timeout=120, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Make sure the FastAPI server is running on port 8000."
    except requests.exceptions.Timeout:
        return None, "Request timed out. The AI agents are taking longer than expected."
    except Exception as e:
        return None, str(e)


def step_indicator():
    labels = ["1 · Profile", "2 · Frameworks", "3 · Policies", "4 · Procedures"]
    classes = []
    for i in range(1, 5):
        if i < st.session_state.step:
            classes.append("done")
        elif i == st.session_state.step:
            classes.append("active")
        else:
            classes.append("")
    html_str = '<div class="steps">' + "".join(
        f'<div class="step {c}">{l}</div>' for l, c in zip(labels, classes)
    ) + "</div>"
    st.markdown(html_str, unsafe_allow_html=True)


def render_policy(p, dl_key):
    import html as h
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
    </div>
    """, unsafe_allow_html=True)
    for sec in p.get("sections", []):
        import html as h
        refs_html = " ".join(
            f'<span class="ref-tag">{h.escape(r)}</span>' for r in sec.get("references", [])
        )
        st.markdown(
            f'<div class="policy-section"><div class="policy-section-title">{h.escape(sec.get("title",""))}</div></div>',
            unsafe_allow_html=True
        )
        st.markdown(sec.get("content", ""))
        if refs_html:
            st.markdown(f'<div style="margin-top:0.3rem;margin-bottom:0.6rem">{refs_html}</div>', unsafe_allow_html=True)
    st.download_button(
        "⬇ Download JSON", data=json.dumps(p, indent=2),
        file_name=f"{p.get('policy_id','policy')}.json",
        mime="application/json", key=dl_key,
    )


def score_color(score):
    if score >= 0.8:
        return "#68d391"
    if score >= 0.6:
        return "#f6e05e"
    return "#fc8181"


# ─── Sidebar nav ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ ComplianceIQ")
    st.markdown("---")
    sidebar_sel = st.radio(
        "Navigation",
        ["new", "history"],
        index=0 if st.session_state.page == "new" else 1,
        format_func=lambda x: "✨ New Compliance Run" if x == "new" else "🗂️ History",
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
            st.caption(f"Gemini slots: {s['gemini_total_slots']}")
            st.caption(f"Groq slots: {s['groq_total_slots']}")
            st.caption(f"Tavily: {'✅' if s['tavily_available'] else '❌'}")
        else:
            st.error("Backend error")
    except Exception:
        st.error("Backend offline")

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🛡️ ComplianceIQ</h1>
  <p>AI-powered compliance intelligence — profile your org, select frameworks, generate policies & procedures</p>
</div>
""", unsafe_allow_html=True)

col_nav1, col_nav2, col_spacer = st.columns([1, 1, 6])
with col_nav1:
    if st.button("✨ New Run", use_container_width=True,
                 type="primary" if st.session_state.page == "new" else "secondary"):
        st.session_state.page = "new"
        st.rerun()
with col_nav2:
    if st.button("🗂️ History", use_container_width=True,
                 type="primary" if st.session_state.page == "history" else "secondary"):
        st.session_state.page = "history"
        st.rerun()

if st.session_state.page == "history":
    st.subheader("Past Compliance Sessions")
    data, err = api("get", "/history?limit=100")
    if err:
        st.error(f"❌ {err}")
    elif not data["sessions"]:
        st.info("No sessions yet. Run a compliance analysis first.")
    else:
        sessions = data["sessions"]
        # ── Summary metrics ──
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Sessions", len(sessions))
        c2.metric("Total Policies",    sum(s["policy_count"]    for s in sessions))
        c3.metric("Total Procedures",  sum(s["procedure_count"] for s in sessions))
        st.markdown("---")

        for s in sessions:
            fw_pills = " ".join(
                f'<span class="pill">{f}</span>' for f in s["selected_frameworks"]
            ) or '<span class="pill">none selected</span>'
            with st.expander(
                f"🏢 {s['org_name']}  ·  {s['created_at'][:10]}  "
                f"·  {s['policy_count']} policies  ·  {s['procedure_count']} procedures",
                expanded=False,
            ):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class="doc-card">
                      <h3>{s['org_name']}</h3>
                      <div class="doc-meta-bar">
                        <span class="doc-meta-item">{s.get('org_country') or '—'}</span>
                        <span class="doc-meta-item">{s.get('org_website') or '—'}</span>
                        <span class="doc-meta-item"><b>Session</b> #{s['session_id']}</span>
                      </div>
                      <div class="policy-section-title">Summary</div>
                      <div style="color:#a0aec0;font-size:0.85rem;margin:0.4rem 0 0.8rem">{s.get('summary') or '—'}</div>
                      <div>
                        <b style="color:#a0aec0;font-size:0.8rem">Selected Frameworks</b><br>
                        {fw_pills}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📂 Load Full Detail", key=f"load_{s['session_id']}", use_container_width=True):
                        st.session_state["history_detail_id"] = s["session_id"]
                    if st.button("🗑️ Delete", key=f"del_{s['session_id']}", use_container_width=True):
                        _, err = api("delete", f"/history/{s['session_id']}")
                        if err:
                            st.error(err)
                        else:
                            st.success("Deleted")
                            st.rerun()

                # ── Inline detail ──
                if st.session_state.get("history_detail_id") == s["session_id"]:
                    detail, err = api("get", f"/history/{s['session_id']}")
                    if err:
                        st.error(err)
                    else:
                        if detail["policies"]:
                            st.markdown(f"**Policies ({len(detail['policies'])})**")
                            for pi, p in enumerate(detail["policies"]):
                                with st.expander(f"📄 {p['title']}", expanded=False):
                                    render_policy(p, f"dl_pol_{s['session_id']}_{pi}")

                        if detail["procedures"]:
                            st.markdown(f"**Procedures ({len(detail['procedures'])})**")
                            for pri, p in enumerate(detail["procedures"]):
                                with st.expander(f"📋 {p['title']}", expanded=False):
                                    import html as h
                                    st.markdown(f"""
                                    <div class="doc-card">
                                      <h3>{h.escape(p.get('title',''))}</h3>
                                      <div class="doc-meta-bar">
                                        <span class="doc-meta-item"><b>ID</b> {h.escape(p.get('procedure_id',''))}</span>
                                        <span class="doc-meta-item"><b>Frequency</b> {h.escape(p.get('frequency','') or '')}</span>
                                        <span class="doc-meta-item"><b>Owner</b> {h.escape(p.get('owner','') or '')}</span>
                                      </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    for label, key in [("Purpose", "purpose"), ("Scope", "scope"), ("Escalation Path", "escalation_path")]:
                                        if p.get(key):
                                            st.markdown(f'<div class="policy-section"><div class="policy-section-title">{label}</div></div>', unsafe_allow_html=True)
                                            st.markdown(p[key])
                                    for step in p.get("steps", []):
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
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.markdown(step.get("description", ""))
                                    st.download_button(
                                        "⬇ Download JSON", data=json.dumps(p, indent=2),
                                        file_name=f"{p.get('procedure_id','proc')}.json",
                                        mime="application/json",
                                        key=f"dl_proc_{s['session_id']}_{pri}",
                                    )
    st.stop()  # Don't render the wizard below

step_indicator()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — ORG PROFILE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.subheader("Tell us about your organization")
    st.caption("Describe your org in 3-4 words and our AI will identify applicable compliance frameworks.")

    col1, col2 = st.columns([2, 1])
    with col1:
        desc = st.text_input(
            "Organization Description *",
            placeholder="e.g. Indian healthcare SaaS startup",
            value=st.session_state.org_description,
            help="3-4 words describing your org type, industry, and region",
        )
        name = st.text_input(
            "Organization Name",
            placeholder="e.g. MedTech Solutions Pvt Ltd",
            value=st.session_state.org_name,
        )
    with col2:
        website = st.text_input(
            "Website (optional)",
            placeholder="https://example.com",
            value=st.session_state.org_website,
        )
        country = st.text_input(
            "Country",
            placeholder="e.g. India, USA, Germany",
            value=st.session_state.org_country,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    examples = ["Indian healthcare SaaS startup", "US fintech payment processor",
                 "EU ecommerce retail company", "Federal government cloud provider",
                 "Global manufacturing enterprise"]
    st.caption("💡 Examples:")
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        with col:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.org_description = ex
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Analyze Organization →", type="primary", use_container_width=True):
        if not desc.strip():
            st.error("Please enter an organization description.")
        else:
            st.session_state.org_description = desc
            st.session_state.org_name = name or desc
            st.session_state.org_website = website
            st.session_state.org_country = country

            with st.spinner("🤖 AI agents analyzing your organization..."):
                data, err = api("post", "/profile", json={
                    "description": desc,
                    "website": website or None,
                    "country": country or None,
                })

            if err:
                st.error(f"❌ {err}")
            else:
                st.session_state.profile = data
                st.session_state.session_id = data.get("session_id")
                st.session_state.selected_frameworks = [
                    fw["id"] for fw in data["recommended_frameworks"]
                    if fw["relevance_score"] >= 0.7
                ]
                st.session_state.step = 2
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — FRAMEWORK SELECTION
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    profile = st.session_state.profile

    # Summary
    industries = " · ".join(profile.get("industries_detected", []))
    regions = " · ".join(profile.get("regions_detected", []))
    st.markdown(f"""
    <div class="summary-box">
      ✅ <b>{profile.get('org_type', '')}</b><br>
      {profile.get('analysis_summary', '')}<br><br>
      <b>Industries:</b> {industries or '—'} &nbsp;|&nbsp; <b>Regions:</b> {regions or '—'}
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Select Compliance Frameworks")
    st.caption("Click cards to select/deselect. Pre-selected based on AI recommendations.")

    frameworks = profile.get("recommended_frameworks", [])
    selected = st.session_state.selected_frameworks

    # Render framework cards in rows of 3
    for row_start in range(0, len(frameworks), 3):
        row = frameworks[row_start:row_start + 3]
        cols = st.columns(3)
        for col, fw in zip(cols, row):
            with col:
                is_sel = fw["id"] in selected
                badge = '<span class="badge mandatory">MANDATORY</span>' if fw["is_mandatory"] else '<span class="badge">RECOMMENDED</span>'
                score_pct = int(fw["relevance_score"] * 100)
                color = score_color(fw["relevance_score"])
                card_class = "fw-card selected" if is_sel else "fw-card"

                st.markdown(f"""
                <div class="{card_class}">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.5rem">{fw['icon']}</span>
                    {badge}
                  </div>
                  <h4>{fw['id']} — {fw['name'][:30]}{'…' if len(fw['name'])>30 else ''}</h4>
                  <div class="score-bar"><div class="score-fill" style="width:{score_pct}%;background:{color}"></div></div>
                  <p style="color:{color};font-weight:600;font-size:0.78rem">{score_pct}% relevance</p>
                  <p style="margin-top:0.4rem">{fw['relevance_reason'][:100]}{'…' if len(fw['relevance_reason'])>100 else ''}</p>
                  <p style="margin-top:0.4rem;color:#4a5568;font-size:0.75rem">Fine: {fw['max_fine']}</p>
                </div>
                """, unsafe_allow_html=True)

                label = "✓ Selected" if is_sel else "+ Select"
                btn_type = "primary" if is_sel else "secondary"
                if st.button(label, key=f"fw_{fw['id']}", use_container_width=True, type=btn_type):
                    if is_sel:
                        st.session_state.selected_frameworks.remove(fw["id"])
                    else:
                        st.session_state.selected_frameworks.append(fw["id"])
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col2:
        sel_count = len(st.session_state.selected_frameworks)
        if st.button(
            f"Generate Policies for {sel_count} Framework{'s' if sel_count != 1 else ''} →",
            type="primary", use_container_width=True,
            disabled=sel_count == 0,
        ):
            # Save selected frameworks to DB
            if st.session_state.get("session_id"):
                api("patch", f"/history/{st.session_state.session_id}/frameworks",
                    json={"selected_frameworks": st.session_state.selected_frameworks})
            st.session_state.step = 3
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — POLICY GENERATION
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    POLICY_TYPES = {
        "data_protection": "Data Protection & Privacy",
        "incident_response": "Incident Response",
        "access_control": "Access Control & IAM",
        "data_retention": "Data Retention & Disposal",
        "third_party_risk": "Third-Party Risk Management",
        "acceptable_use": "Acceptable Use",
        "business_continuity": "Business Continuity & DR",
        "encryption": "Encryption & Key Management",
    }

    st.subheader("Generate Compliance Policies")

    col_cfg, col_out = st.columns([1, 2])

    with col_cfg:
        st.markdown("**Configuration**")
        framework = st.selectbox(
            "Framework",
            st.session_state.selected_frameworks,
            key="pol_framework",
        )
        selected_types = st.multiselect(
            "Policy Types",
            options=list(POLICY_TYPES.keys()),
            default=["data_protection", "incident_response", "access_control"],
            format_func=lambda x: POLICY_TYPES[x],
        )
        org_name_input = st.text_input("Org Name", value=st.session_state.org_name)

        if st.button("⚡ Generate Policies", type="primary", use_container_width=True):
            if not selected_types:
                st.error("Select at least one policy type.")
            else:
                with st.spinner(f"🤖 Generating {len(selected_types)} {framework} policies..."):
                    data, err = api("post", "/policies/generate", json={
                        "org_description": st.session_state.org_description,
                        "org_name": org_name_input,
                        "framework": framework,
                        "policy_types": selected_types,
                    })
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state.policies = data
                    st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("Procedures →", use_container_width=True, type="secondary"):
                st.session_state.step = 4
                st.rerun()

    with col_out:
        if st.session_state.policies:
            pol_data = st.session_state.policies
            st.markdown(f'<div class="summary-box">✅ {pol_data["summary"]}</div>', unsafe_allow_html=True)

            # Download
            st.download_button(
                "⬇ Download Policies JSON",
                data=json.dumps(pol_data, indent=2),
                file_name=f"{pol_data['framework']}_policies.json",
                mime="application/json",
                use_container_width=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            for pi, policy in enumerate(pol_data["policies"]):
                with st.expander(f"📄 {policy['title']}", expanded=False):
                    render_policy(policy, f"dl_pol_live_{pi}")
        else:
            st.info("👈 Configure and generate policies using the panel on the left.")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — PROCEDURE GENERATION
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    PROCEDURE_TYPES = {
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

    st.subheader("Generate Operational Procedures")

    col_cfg, col_out = st.columns([1, 2])

    with col_cfg:
        st.markdown("**Configuration**")
        framework = st.selectbox(
            "Framework",
            st.session_state.selected_frameworks,
            key="proc_framework",
        )
        selected_types = st.multiselect(
            "Procedure Types",
            options=list(PROCEDURE_TYPES.keys()),
            default=["incident_response", "data_breach", "access_review"],
            format_func=lambda x: PROCEDURE_TYPES[x],
        )
        org_name_input = st.text_input("Org Name", value=st.session_state.org_name, key="proc_org")

        if st.button("⚡ Generate Procedures", type="primary", use_container_width=True):
            if not selected_types:
                st.error("Select at least one procedure type.")
            else:
                with st.spinner(f"🤖 Generating {len(selected_types)} {framework} procedures..."):
                    data, err = api("post", "/procedures/generate", json={
                        "org_description": st.session_state.org_description,
                        "org_name": org_name_input,
                        "framework": framework,
                        "procedure_types": selected_types,
                    })
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state.procedures = data
                    st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Policies", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("🔄 Start Over", use_container_width=True):
                for k in ["step", "profile", "selected_frameworks", "policies", "procedures",
                          "org_name", "org_description", "org_website", "org_country", "session_id"]:
                    st.session_state[k] = 1 if k == "step" else ([] if k == "selected_frameworks" else None if k in ["profile","policies","procedures","session_id"] else "")
                st.rerun()

    with col_out:
        if st.session_state.procedures:
            proc_data = st.session_state.procedures
            st.markdown(f'<div class="summary-box">✅ {proc_data["summary"]}</div>', unsafe_allow_html=True)

            st.download_button(
                "⬇ Download Procedures JSON",
                data=json.dumps(proc_data, indent=2),
                file_name=f"{proc_data['framework']}_procedures.json",
                mime="application/json",
                use_container_width=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            for pi, proc in enumerate(proc_data["procedures"]):
                with st.expander(f"📋 {proc['title']}", expanded=False):
                    import html as h
                    st.markdown(f"""
                    <div class="doc-card">
                      <h3>{h.escape(proc.get('title',''))}</h3>
                      <div class="doc-meta-bar">
                        <span class="doc-meta-item"><b>ID</b> {h.escape(proc.get('procedure_id',''))}</span>
                        <span class="doc-meta-item"><b>Frequency</b> {h.escape(proc.get('frequency','') or '')}</span>
                        <span class="doc-meta-item"><b>Owner</b> {h.escape(proc.get('owner','') or '')}</span>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    for label, key in [("Purpose", "purpose"), ("Scope", "scope"), ("Escalation Path", "escalation_path")]:
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
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(step.get("description", ""))
        else:
            st.info("👈 Configure and generate procedures using the panel on the left.")
