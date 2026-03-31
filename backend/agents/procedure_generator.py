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

from backend.config.llm_config import get_llm_with_fallback, get_fresh_llm, get_tavily_key
from backend.config.frameworks import FRAMEWORKS
from backend.models.schemas import (
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
        from crewai_tools import TavilySearchResults
        tavily_key = get_tavily_key()
        tools = [TavilySearchResults(api_key=tavily_key, max_results=3)]
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
        llm=get_llm_with_fallback(temperature=0.2),
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

    context_str = ""
    if org_context:
        context_str = f"\nOrganization Context: {json.dumps(org_context, indent=2)}"

    return Task(
        description=f"""Generate a detailed {framework} {proc_meta['title']} for:

Organization: {org_name}
Description: {org_description}
Framework: {framework} — {fw_meta.get('name', '')}
Procedure Type: {proc_type} — {proc_meta['description']}
Frequency: {proc_meta['frequency']}
{context_str}

Generate a COMPLETE, DETAILED procedure with 8-15 specific steps covering:
- Detection/Trigger (how is this procedure initiated?)
- Initial assessment and triage
- Containment or execution steps
- Notification and communication
- Documentation requirements
- Resolution and closure
- Post-incident review (if applicable)

Each step MUST include:
- A clear title
- Detailed description of exactly what to do
- Who is responsible (role title)
- Timeline (how long should this take)
- Tools/systems required
- What documentation to create/update

The procedure MUST reference {framework} requirements: {', '.join(fw_meta.get('key_articles', []))}

Return ONLY valid JSON:
{{
  "procedure_id": "PROC-{framework}-{proc_type.upper()[:4]}-001",
  "procedure_type": "{proc_type}",
  "title": "{proc_meta['title']}",
  "purpose": "One sentence explaining why this procedure exists and what it achieves",
  "scope": "Who and what systems this procedure applies to",
  "frequency": "{proc_meta['frequency']}",
  "owner": "Role title of procedure owner",
  "escalation_path": "Step-by-step escalation path if procedure fails or escalation needed",
  "steps": [
    {{
      "step_number": 1,
      "title": "Step title",
      "description": "Detailed description of exactly what to do",
      "responsible_role": "Job title responsible for this step",
      "timeline": "e.g., Within 1 hour of detection",
      "tools_required": ["Slack", "JIRA", "Splunk"],
      "documentation": "What to document/record for this step"
    }}
  ]
}}
""",
        expected_output=f"Valid JSON procedure document for {framework} {proc_type}",
        agent=agent,
    )


def _sanitize_json(text: str) -> str:
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
        if in_string and ch in ('\n', '\r', '\t'):
            result.append(repr(ch)[1:-1])
        elif in_string and ord(ch) < 0x20:
            result.append(f"\\u{ord(ch):04x}")
        else:
            result.append(ch)
    cleaned = "".join(result)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _parse_procedure(raw: str, framework: str, proc_type: str) -> Optional[GeneratedProcedure]:
    """Parse LLM output into GeneratedProcedure."""
    try:
        clean = re.sub(r"```json\s*", "", raw)
        clean = re.sub(r"```\s*$", "", clean)
        clean = re.sub(r"Thought:.*?(\{)", r"\1", clean, flags=re.DOTALL)

        json_match = re.search(r"\{[\s\S]*\}", clean)
        if not json_match:
            return None

        data = json.loads(_sanitize_json(json_match.group(0)))

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
        logger.error(f"Procedure parse error: {e}")
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
                )
                result = crew.kickoff()
                procedure = _parse_procedure(str(result), framework, proc_type)

                if procedure:
                    generated_procedures.append(procedure)
                    logger.info(f"✓ Generated {proc_type} procedure")
                    success = True
                    break
                else:
                    raise ValueError("Failed to parse procedure JSON")

            except Exception as e:
                logger.warning(f"Procedure {proc_type} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + random.uniform(0, 1))

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


AVAILABLE_PROCEDURE_TYPES = list(PROCEDURE_TYPES.keys())
PROCEDURE_TYPE_DETAILS = PROCEDURE_TYPES
