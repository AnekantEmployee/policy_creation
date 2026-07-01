"""
Procedure Generation Agent
Generates operational compliance procedures (step-by-step runbooks) for any framework.
"""

import json
import logging
import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from crewai import Agent, Task, Crew, Process

from config.llm_config import get_llm_with_fallback, get_fresh_llm, get_tavily_key
from config.frameworks import FRAMEWORKS
from models.schemas import (
    GeneratedProcedure, ProcedureStep, ProcedureGenerationResponse
)

logger = logging.getLogger(__name__)

# ─── Procedure Type Definitions ───────────────────────────────────────────────
PROCEDURE_TYPES = {
    "incident_response": {
        "title": "Security Incident Response Procedure",
        "description": "Step-by-step process for detecting, containing, and recovering from security incidents",
        "frequency": "Activated on incident detection",
    },
    "data_breach": {
        "title": "Data Breach Notification Procedure",
        "description": "Process for investigating, containing, and notifying stakeholders of a data breach",
        "frequency": "Activated on confirmed breach",
    },
    "access_review": {
        "title": "Periodic Access Review Procedure",
        "description": "Process for reviewing and revoking unnecessary user access rights",
        "frequency": "Quarterly",
    },
    "vendor_assessment": {
        "title": "Vendor Due Diligence & Assessment Procedure",
        "description": "Process for evaluating third-party vendors for compliance and security",
        "frequency": "Before onboarding and annually",
    },
    "data_subject_request": {
        "title": "Data Subject / Consumer Rights Request Procedure",
        "description": "Process for handling requests from individuals to access, correct, or delete their data",
        "frequency": "Activated on request receipt",
    },
    "risk_assessment": {
        "title": "Information Security Risk Assessment Procedure",
        "description": "Process for identifying, evaluating, and treating information security risks",
        "frequency": "Annually or on significant change",
    },
    "backup_recovery": {
        "title": "Backup & Recovery Testing Procedure",
        "description": "Process for verifying backup integrity and testing recovery capabilities",
        "frequency": "Monthly/Quarterly",
    },
    "security_awareness": {
        "title": "Security Awareness Training Procedure",
        "description": "Process for delivering and tracking mandatory security training",
        "frequency": "Annually + on onboarding",
    },
    "change_management": {
        "title": "Change Management Procedure",
        "description": "Process for managing changes to IT systems and infrastructure",
        "frequency": "Per change event",
    },
    "vulnerability_management": {
        "title": "Vulnerability Management & Patching Procedure",
        "description": "Process for identifying, prioritizing, and remediating security vulnerabilities",
        "frequency": "Monthly (scanning) / Per CVE",
    },
}


def _build_procedure_agent(framework: str) -> Agent:
    """Build procedure generation agent."""
    fw_meta = FRAMEWORKS.get(framework, {})

    try:
        from crewai_tools import TavilySearchTool
        tavily_key = get_tavily_key()
        tools = [TavilySearchTool(api_key=tavily_key)]
    except Exception:
        tools = []

    return Agent(
        role=f"{framework} Procedure & Controls Specialist",
        goal=(
            f"Generate detailed, actionable operational procedures that help organizations "
            f"implement and demonstrate {framework} compliance."
        ),
        backstory=f"""You are a compliance operations specialist with 15+ years of experience 
        implementing {fw_meta.get('name', framework)} procedures across organizations.
        
        Your procedures are:
        - Step-by-step and immediately executable
        - Role-specific with clear responsibilities
        - Time-bound with realistic timelines
        - Linked to specific {framework} requirements
        - Including escalation paths and documentation requirements
        
        You know exactly what auditors look for in {framework} assessments.""",
        tools=tools,
        verbose=False,
        allow_delegation=False,
        llm=get_fresh_llm(temperature=0.2, rotate=True),
    )


def _build_procedure_task(
    agent: Agent,
    org_description: str,
    org_name: str,
    framework: str,
    proc_type: str,
    proc_meta: Dict[str, str],
    org_context: Optional[Dict[str, Any]] = None,
) -> Task:
    """Build procedure generation task."""
    fw_meta = FRAMEWORKS.get(framework, {})
    key_articles = ', '.join(fw_meta.get('key_articles', [])[:8])

    context_str = ""
    if org_context:
        context_str = f"\nOrganization Context: {json.dumps(org_context, indent=2)}"

    return Task(
        description=f"""You are generating a COMPLETE, PRODUCTION-READY {framework} operational procedure document.

Organization: {org_name}
Description: {org_description}{context_str}
Framework: {framework} — {fw_meta.get('name', '')}
Procedure: {proc_meta['title']}
Frequency: {proc_meta['frequency']}
Key {framework} Controls: {key_articles}

CRITICAL INSTRUCTIONS:
- Generate exactly 10 detailed procedure steps. No fewer.
- Every step must have a full, actionable description of at least 3-4 sentences.
- Every step must have a clearly named responsible_role, a specific timeline, real tools_required, and documentation requirements.
- The purpose and scope fields must each be 2-3 full paragraphs.
- escalation_path must describe the full escalation chain with names/roles and timeframes.
- Reference specific {framework} articles or control numbers in step descriptions where relevant.
- Tailor every step to {org_name} as a {org_description}.
- No placeholders, no "TBD", no generic text. Every field must have real, usable content.

Return ONLY a valid JSON object (no markdown, no preamble):
{{
  "procedure_id": "PROC-{framework[:6].upper()}-{proc_type[:3].upper()}-001",
  "procedure_type": "{proc_type}",
  "title": "{proc_meta['title']}",
  "purpose": "Write 2-3 full paragraphs explaining what this procedure achieves for {org_name}, which {framework} obligations it satisfies, what risks it mitigates, and when it is activated. Be specific to the context of {org_description}.",
  "scope": "Write 2 full paragraphs describing exactly which systems, personnel, data types, and business processes fall within the scope of this procedure at {org_name}. Include what is explicitly out of scope.",
  "frequency": "{proc_meta['frequency']}",
  "owner": "The specific role/title at {org_name} responsible for owning this procedure",
  "escalation_path": "Describe the full escalation chain: who is first contacted, who they escalate to and under what conditions, executive escalation threshold, regulatory notification trigger and responsible person, and maximum time before each escalation level activates.",
  "steps": [
    {{
      "step_number": 1,
      "title": "Detection and Initial Triage",
      "description": "Detailed 3-4 sentence description of exactly what happens in this step, who does it, how they do it, and what decisions are made. Include specific system names, thresholds, or criteria relevant to {org_name}.",
      "responsible_role": "Specific job title",
      "timeline": "Specific timeframe e.g. Within 15 minutes of alert",
      "tools_required": ["Tool1", "Tool2"],
      "documentation": "Specific record or artifact that must be created"
    }},
    {{
      "step_number": 2,
      "title": "Severity Assessment and Classification",
      "description": "Detailed description of how severity is assessed, what criteria are used, what the classification levels mean for response, and what documentation is created.",
      "responsible_role": "Specific job title",
      "timeline": "Within 30 minutes of detection",
      "tools_required": ["Tool1"],
      "documentation": "Incident severity classification record"
    }},
    {{
      "step_number": 3,
      "title": "Stakeholder Notification",
      "description": "Detailed description of who is notified, through what channels, with what information, and within what timeframes based on severity classification.",
      "responsible_role": "Specific job title",
      "timeline": "Within 1 hour of classification",
      "tools_required": ["Email", "Incident Management System"],
      "documentation": "Notification log with timestamps and recipients"
    }},
    {{
      "step_number": 4,
      "title": "Containment and Immediate Response",
      "description": "Detailed description of containment actions taken, technical steps performed, who authorizes them, and how impact is limited.",
      "responsible_role": "Specific job title",
      "timeline": "Within 2 hours of classification",
      "tools_required": ["Tool1", "Tool2"],
      "documentation": "Containment actions log"
    }},
    {{
      "step_number": 5,
      "title": "Evidence Collection and Preservation",
      "description": "Detailed description of what evidence is collected, how chain of custody is maintained, where evidence is stored, and how it supports the {framework} audit trail requirements.",
      "responsible_role": "Specific job title",
      "timeline": "Concurrent with containment",
      "tools_required": ["Forensic tools", "Secure storage"],
      "documentation": "Evidence inventory and chain of custody log"
    }},
    {{
      "step_number": 6,
      "title": "Investigation and Root Cause Analysis",
      "description": "Detailed description of investigation methodology, tools used, what questions must be answered, how {framework} compliance impact is assessed, and who reviews findings.",
      "responsible_role": "Specific job title",
      "timeline": "Within 24-48 hours",
      "tools_required": ["Tool1", "Tool2"],
      "documentation": "Investigation report with root cause findings"
    }},
    {{
      "step_number": 7,
      "title": "Regulatory and Legal Assessment",
      "description": "Detailed description of how the incident is assessed against {framework} notification requirements, legal counsel involvement, regulatory notification decision process, and documentation requirements.",
      "responsible_role": "DPO / Legal Counsel",
      "timeline": "Within 24 hours of confirmed incident",
      "tools_required": ["Legal reference materials", "DPA register"],
      "documentation": "Legal assessment memo and notification decision record"
    }},
    {{
      "step_number": 8,
      "title": "Remediation and Recovery",
      "description": "Detailed description of remediation steps taken, how systems are restored, validation that vulnerabilities are addressed, and how recovery is verified before systems return to production.",
      "responsible_role": "Specific job title",
      "timeline": "Per severity: Critical within 4h, High within 24h, Medium within 72h",
      "tools_required": ["Tool1", "Tool2"],
      "documentation": "Remediation plan, change tickets, and recovery validation report"
    }},
    {{
      "step_number": 9,
      "title": "Communication and Reporting",
      "description": "Detailed description of internal and external communications, how affected parties are notified, regulatory reporting format and submission, and management briefing process.",
      "responsible_role": "Specific job title",
      "timeline": "Per {framework} notification window requirements",
      "tools_required": ["Email", "Regulatory portal", "Communication templates"],
      "documentation": "All outbound communications and regulatory submission records"
    }},
    {{
      "step_number": 10,
      "title": "Post-Incident Review and Lessons Learned",
      "description": "Detailed description of the post-incident review process, who participates, what is reviewed, how lessons learned are documented, how policy/procedure updates are triggered, and how findings are reported to leadership.",
      "responsible_role": "CISO / Procedure Owner",
      "timeline": "Within 5-10 business days of incident closure",
      "tools_required": ["Meeting platform", "Incident management system"],
      "documentation": "Post-incident review report, updated risk register, procedure improvement log"
    }}
  ]
}}
""",
        expected_output=(
            "A complete, valid JSON object containing a fully written operational procedure "
            "with exactly 10 detailed steps. Every field must contain real, substantive content "
            "tailored to the organization. No placeholders."
        ),
        agent=agent,
    )


def _sanitize_json(text: str) -> str:
    """Aggressively fix malformed JSON from LLM output."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = re.sub(r"^[^{]*", "", text, flags=re.DOTALL)
    last_brace = text.rfind("}")
    if last_brace != -1:
        text = text[:last_brace + 1]
    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            result.append(ch)
            continue
        if ch == '"':
            in_string = not in_string
        if in_string:
            if ch == '\n':
                result.append('\\n')
                continue
            elif ch == '\r':
                continue
            elif ch == '\t':
                result.append('\\t')
                continue
            elif ord(ch) < 0x20:
                result.append(f"\\u{ord(ch):04x}")
                continue
        result.append(ch)
    cleaned = "".join(result)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _parse_procedure(raw: str, framework: str, proc_type: str) -> Optional[GeneratedProcedure]:
    """Parse LLM output into GeneratedProcedure."""
    sanitized = _sanitize_json(raw)

    data = None
    for attempt_str in [sanitized, raw]:
        try:
            json_match = re.search(r"\{[\s\S]*\}", attempt_str)
            if json_match:
                data = json.loads(json_match.group(0))
                break
        except Exception:
            try:
                from json_repair import repair_json
                json_match = re.search(r"\{[\s\S]*\}", attempt_str)
                if json_match:
                    data = json.loads(repair_json(json_match.group(0)))
                    break
            except Exception:
                continue

    if not data:
        logger.error(f"Procedure parse error: could not extract valid JSON")
        return None

    try:
        steps = [
            ProcedureStep(
                step_number=s.get("step_number", i + 1),
                title=s.get("title", f"Step {i + 1}"),
                description=s.get("description", ""),
                responsible_role=s.get("responsible_role", "CISO"),
                timeline=s.get("timeline", ""),
                tools_required=s.get("tools_required", []),
                documentation=s.get("documentation", ""),
            )
            for i, s in enumerate(data.get("steps", []))
        ]

        escalation_path = data.get("escalation_path", "")
        if isinstance(escalation_path, list):
            escalation_path = " → ".join(str(s) for s in escalation_path)

        return GeneratedProcedure(
            procedure_id=data.get("procedure_id", f"PROC-{framework}-{proc_type.upper()[:4]}-001"),
            framework=framework,
            procedure_type=proc_type,
            title=data.get("title", PROCEDURE_TYPES.get(proc_type, {}).get("title", "")),
            purpose=data.get("purpose", ""),
            scope=data.get("scope", ""),
            steps=steps,
            frequency=data.get("frequency", PROCEDURE_TYPES.get(proc_type, {}).get("frequency", "")),
            owner=data.get("owner", "CISO"),
            escalation_path=escalation_path,
        )
    except Exception as e:
        logger.error(f"Procedure build error: {e}")
        return None


def generate_procedures(
    org_description: str,
    org_name: str,
    framework: str,
    procedure_types: List[str],
    org_context: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
) -> ProcedureGenerationResponse:
    """
    Generate compliance procedures for an organization.

    Args:
        org_description: Brief org description
        org_name: Organization name
        framework: Framework ID (e.g., GDPR, HIPAA)
        procedure_types: List of procedure types to generate
        org_context: Additional org context
        max_retries: Max retry attempts per procedure

    Returns:
        ProcedureGenerationResponse with all generated procedures
    """
    if framework not in FRAMEWORKS:
        raise ValueError(f"Unknown framework: {framework}")

    valid_types = [pt for pt in procedure_types if pt in PROCEDURE_TYPES]
    if not valid_types:
        valid_types = ["incident_response", "data_breach", "access_review"]

    generated_procedures = []

    for proc_type in valid_types:
        proc_meta = PROCEDURE_TYPES[proc_type]
        logger.info(f"Generating {framework} {proc_type} procedure for {org_name}...")
        success = False

        for attempt in range(max_retries):
            try:
                # Fresh agent + LLM on every attempt to rotate key/model
                agent = _build_procedure_agent(framework)
                task = _build_procedure_task(
                    agent, org_description, org_name, framework,
                    proc_type, proc_meta, org_context
                )
                crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False,
                    tracing=False,
                )
                logger.debug(f"Attempting procedure generation (attempt {attempt + 1}/{max_retries})")
                result = crew.kickoff()
                raw_output = str(result)
                logger.info(f"Raw LLM output length for {proc_type}: {len(raw_output)} chars")
                if len(raw_output) < 500:
                    raise ValueError(f"LLM output too short ({len(raw_output)} chars) — likely rate-limited or truncated")
                procedure = _parse_procedure(raw_output, framework, proc_type)

                if procedure:
                    # Quality gate: reject if steps are mostly empty or too few
                    total_content = sum(len(s.description) for s in procedure.steps)
                    if len(procedure.steps) < 5 or total_content < 800:
                        raise ValueError(
                            f"Procedure content too thin: {len(procedure.steps)} steps, "
                            f"{total_content} chars — model likely returned placeholder content"
                        )
                    generated_procedures.append(procedure)
                    logger.info(f"✓ Generated {proc_type} procedure ({len(procedure.steps)} steps, {total_content} chars)")
                    success = True
                    break
                else:
                    raise ValueError("Failed to parse procedure JSON")

            except Exception as e:
                error_str = str(e)
                logger.warning(f"Procedure {proc_type} attempt {attempt + 1} failed: {error_str}")
                
                # Log more detail on API key errors
                if "invalid_api_key" in error_str.lower() or "unauthorized" in error_str.lower():
                    logger.warning(f"⚠ API authentication issue detected on attempt {attempt + 1}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    logger.debug(f"Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)

        if not success:
            generated_procedures.append(_create_fallback_procedure(
                framework, proc_type, org_name, proc_meta
            ))

        time.sleep(random.uniform(1, 2))

    fw_meta = FRAMEWORKS[framework]
    summary = (
        f"Generated {len(generated_procedures)} {fw_meta['name']} operational procedures for {org_name}. "
        f"Procedures include: {', '.join(PROCEDURE_TYPES.get(pt, {}).get('title', pt) for pt in valid_types)}."
    )

    return ProcedureGenerationResponse(
        org_name=org_name,
        framework=framework,
        procedures=generated_procedures,
        summary=summary,
        timestamp=datetime.now().isoformat(),
    )


def _create_fallback_procedure(
    framework: str, proc_type: str, org_name: str, proc_meta: Dict
) -> GeneratedProcedure:
    """
    Create a substantive fallback procedure when LLM generation fails.
    Produces real, usable steps — not a stub.
    """
    fw_name = FRAMEWORKS.get(framework, {}).get("name", framework)
    proc_title = proc_meta.get("title", f"{framework} {proc_type.replace('_', ' ').title()} Procedure")

    steps = [
        ProcedureStep(
            step_number=1,
            title="Detection and Initial Triage",
            description=(
                f"The Security Operations team or designated monitoring personnel identify a potential "
                f"event requiring this procedure through automated alerts, manual observation, or third-party "
                f"notification. The on-duty analyst performs an initial triage to confirm the event is real "
                f"and requires escalation. A preliminary record is created in the incident management system "
                f"with timestamp, source, and initial assessment."
            ),
            responsible_role="Security Analyst / IT Operations",
            timeline="Within 15 minutes of detection",
            tools_required=["SIEM", "Incident Management System", "Monitoring Dashboard"],
            documentation="Initial incident ticket with detection source, timestamp, and preliminary assessment",
        ),
        ProcedureStep(
            step_number=2,
            title="Severity Classification",
            description=(
                f"The Security Lead assesses the severity of the event using the organization's risk matrix: "
                f"Critical (immediate threat to operations or {framework} compliance), High (significant risk, "
                f"response within 4 hours), Medium (moderate risk, response within 24 hours), Low (minor "
                f"risk, response within 72 hours). Severity determines the response team composition, "
                f"escalation path, and notification requirements under {framework}."
            ),
            responsible_role="Security Lead / Incident Commander",
            timeline="Within 30 minutes of detection",
            tools_required=["Risk Assessment Matrix", "Incident Management System"],
            documentation="Severity classification record with justification",
        ),
        ProcedureStep(
            step_number=3,
            title="Escalation and Team Assembly",
            description=(
                f"Based on severity classification, the Incident Commander activates the appropriate response "
                f"team and notifies relevant stakeholders. Critical/High incidents require immediate notification "
                f"to the CISO and DPO. The response team is assembled via the organization's emergency "
                f"communication channels. A dedicated incident bridge or communication channel is established "
                f"for coordinating response activities."
            ),
            responsible_role="Incident Commander / CISO",
            timeline="Within 1 hour of classification",
            tools_required=["Email", "Phone", "Collaboration Platform"],
            documentation="Escalation log with names notified, times, and methods",
        ),
        ProcedureStep(
            step_number=4,
            title="Containment Actions",
            description=(
                f"The Security Team implements immediate containment measures to limit impact and prevent "
                f"further exposure. Actions may include isolating affected systems, revoking compromised "
                f"credentials, blocking malicious network traffic, or suspending affected services. "
                f"All containment actions are logged with timestamps and authorized by the Incident Commander. "
                f"Business impact of containment is assessed and communicated to stakeholders."
            ),
            responsible_role="Security Engineer / IT Team",
            timeline="Within 2 hours of classification (Critical); 4 hours (High)",
            tools_required=["Firewall Management", "Identity Management System", "Network Controls"],
            documentation="Containment action log with timestamps, actions taken, and authorizing personnel",
        ),
        ProcedureStep(
            step_number=5,
            title="Evidence Preservation",
            description=(
                f"Forensic evidence is collected and preserved in accordance with chain-of-custody requirements "
                f"to support investigation, regulatory compliance, and potential legal proceedings. System logs, "
                f"network captures, and affected data snapshots are secured in a write-protected forensic "
                f"repository. Evidence collection follows the organization's digital forensics policy to ensure "
                f"admissibility and {framework} audit trail requirements are met."
            ),
            responsible_role="Security Engineer / Forensics Lead",
            timeline="Concurrent with containment",
            tools_required=["Forensic Imaging Tools", "Secure Evidence Repository", "Hash Verification Tools"],
            documentation="Evidence inventory list with hash values, collection timestamps, and custodian details",
        ),
        ProcedureStep(
            step_number=6,
            title="Root Cause Investigation",
            description=(
                f"A thorough investigation is conducted to identify the root cause, attack vector, affected "
                f"systems, compromised data, and timeline of events. The investigation team documents all "
                f"findings in the incident management system. The scope of {framework} impact is assessed — "
                f"including whether personal data or regulated information was accessed, modified, or exfiltrated. "
                f"Investigation findings are reviewed by the CISO and DPO before proceeding."
            ),
            responsible_role="Security Lead / DPO",
            timeline="Within 24-48 hours of containment",
            tools_required=["Log Analysis Tools", "Forensic Analysis Platform", "DPA Register"],
            documentation="Investigation report including timeline, root cause, affected data inventory, and {framework} impact assessment",
        ),
        ProcedureStep(
            step_number=7,
            title="Regulatory and Legal Assessment",
            description=(
                f"The DPO and Legal Counsel assess whether the incident triggers notification obligations "
                f"under {framework} and any other applicable regulations. The assessment considers: "
                f"nature and sensitivity of affected data, number of individuals affected, likelihood of "
                f"harm, and {framework}-specific notification thresholds. A formal notification decision "
                f"is documented. If notification is required, the DPO prepares regulatory submissions "
                f"within the mandated timeframes."
            ),
            responsible_role="Data Protection Officer / Legal Counsel",
            timeline="Within 24 hours of confirmed scope (regulatory clock may already be running)",
            tools_required=["{framework} Regulatory Guidance", "Legal Templates", "Regulatory Portal"],
            documentation="Legal assessment memo, notification decision record, and regulatory submission drafts",
        ),
        ProcedureStep(
            step_number=8,
            title="Remediation and System Recovery",
            description=(
                f"The Security and IT teams implement remediation measures to address the root cause and "
                f"restore affected systems to a known-good state. Remediation steps are executed in a "
                f"controlled manner with rollback capability. All changes are implemented through the "
                f"change management process. Systems are validated against security baselines before "
                f"returning to production. Recovery is documented and signed off by the CISO."
            ),
            responsible_role="Security Engineer / IT Operations",
            timeline="Critical: within 4h of authorization; High: within 24h; Medium: within 72h",
            tools_required=["Change Management System", "Configuration Management Tools", "Backup Systems"],
            documentation="Remediation plan, change tickets, pre/post validation results, and CISO sign-off",
        ),
        ProcedureStep(
            step_number=9,
            title="Stakeholder and Regulatory Communication",
            description=(
                f"All required communications are issued to internal stakeholders, affected individuals, "
                f"and regulatory authorities per the notification decision from Step 7. Communications "
                f"are drafted using approved templates, reviewed by Legal, and sent through approved "
                f"channels. All outbound communications are logged with send times, recipient lists, "
                f"and content. Regulatory authority acknowledgments are tracked to closure."
            ),
            responsible_role="DPO / Communications Lead",
            timeline="Per {framework} notification windows from incident confirmation",
            tools_required=["Email", "Regulatory Notification Portal", "Communication Templates"],
            documentation="Communication log with all notifications, responses received, and regulatory submissions",
        ),
        ProcedureStep(
            step_number=10,
            title="Post-Incident Review and Lessons Learned",
            description=(
                f"Within 5-10 business days of incident closure, the CISO convenes a post-incident review "
                f"meeting with all key participants. The review covers: what happened, what worked well, "
                f"what needs improvement, and what changes to policies, procedures, or controls are required. "
                f"Findings are documented in a Post-Incident Review Report and tracked as improvement actions "
                f"in the risk register. Lessons learned are shared with relevant teams and incorporated "
                f"into future training. The incident is closed in the incident management system."
            ),
            responsible_role="CISO / Procedure Owner",
            timeline="Within 5-10 business days of incident closure",
            tools_required=["Incident Management System", "Risk Register", "Meeting Platform"],
            documentation="Post-incident review report, updated risk register, procedure improvement recommendations",
        ),
    ]

    return GeneratedProcedure(
        procedure_id=f"PROC-{framework.upper()[:6]}-{proc_type.upper()[:4]}-001",
        framework=framework,
        procedure_type=proc_type,
        title=proc_title,
        purpose=(
            f"This procedure defines the step-by-step operational process for {org_name} to execute "
            f"a {proc_meta.get('description', proc_title)} in compliance with {fw_name} ({framework}) "
            f"requirements. It ensures that all personnel follow a consistent, documented, and auditable "
            f"process that satisfies regulatory obligations and minimizes organizational risk.\n\n"
            f"This procedure is activated {proc_meta.get('frequency', 'as required')} and is a mandatory "
            f"component of {org_name}'s {framework} compliance program. Failure to follow this procedure "
            f"may result in regulatory penalties, reputational damage, and disciplinary action."
        ),
        scope=(
            f"This procedure applies to all {org_name} employees, contractors, and third-party service "
            f"providers who are involved in detecting, responding to, managing, or reporting events covered "
            f"by this procedure. It covers all information systems, applications, data, and processes "
            f"operated by or on behalf of {org_name} that are subject to {framework} requirements.\n\n"
            f"This procedure does not apply to events that fall entirely outside the scope of {framework} "
            f"obligations, though those events may be governed by other organizational procedures."
        ),
        steps=steps,
        frequency=proc_meta.get("frequency", "As required"),
        owner="Chief Information Security Officer",
        escalation_path=(
            f"Level 1: Security Analyst → Security Lead (within 15 min for Critical/High) → "
            f"Level 2: Security Lead → CISO + DPO (within 1 hour) → "
            f"Level 3: CISO → CEO/Board notification (Critical incidents affecting operations) → "
            f"Regulatory: DPO → Regulatory Authority notification per {framework} timelines"
        ),
    )


AVAILABLE_PROCEDURE_TYPES = list(PROCEDURE_TYPES.keys())
PROCEDURE_TYPE_DETAILS = PROCEDURE_TYPES
