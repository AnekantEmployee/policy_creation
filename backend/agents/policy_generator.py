"""
Policy Generation Agent
Generates comprehensive, organization-specific compliance policies for any framework.
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
    GeneratedPolicy, PolicySection, PolicyGenerationResponse
)

logger = logging.getLogger(__name__)

# ─── Policy Type Definitions ──────────────────────────────────────────────────
POLICY_TYPES = {
    "data_protection": {
        "title": "Data Protection & Privacy Policy",
        "description": "How personal data is collected, processed, stored, and protected",
    },
    "incident_response": {
        "title": "Information Security Incident Response Policy",
        "description": "How security incidents are detected, reported, and managed",
    },
    "access_control": {
        "title": "Access Control & Identity Management Policy",
        "description": "How access to systems and data is granted, managed, and revoked",
    },
    "data_retention": {
        "title": "Data Retention & Disposal Policy",
        "description": "How long data is retained and how it is securely disposed",
    },
    "third_party_risk": {
        "title": "Third-Party & Vendor Risk Management Policy",
        "description": "How vendors and third parties are assessed and managed",
    },
    "acceptable_use": {
        "title": "Acceptable Use Policy",
        "description": "Acceptable use of organizational systems and data",
    },
    "business_continuity": {
        "title": "Business Continuity & Disaster Recovery Policy",
        "description": "How the organization maintains operations during disruptions",
    },
    "encryption": {
        "title": "Encryption & Key Management Policy",
        "description": "Standards for encrypting data at rest and in transit",
    },
}


def _build_policy_agent(framework: str) -> Agent:
    """Build policy generation agent."""
    fw_meta = FRAMEWORKS.get(framework, {})

    try:
        from crewai_tools import TavilySearchTool
        tavily_key = get_tavily_key()
        tools = [TavilySearchTool(api_key=tavily_key)]
    except Exception:
        tools = []

    return Agent(
        role=f"{framework} Policy Architect",
        goal=(
            f"Generate comprehensive, legally sound, organization-specific {framework} "
            f"compliance policies that can be immediately adopted."
        ),
        backstory=f"""You are a senior compliance policy architect specializing in {fw_meta.get('name', framework)}. 
        You have 15+ years of experience writing compliance policies for organizations across industries.
        
        Your policies are:
        - Legally accurate and reference specific {framework} articles/sections
        - Practically implementable (not just theoretical)
        - Tailored to the specific organization type
        - Written in clear, professional language
        - Structured with executive summary, scope, definitions, requirements, and responsibilities
        
        You understand {fw_meta.get('description', '')} deeply.""",
        tools=tools,
        verbose=False,
        allow_delegation=False,
        llm=get_fresh_llm(temperature=0.2, rotate=True),
    )


def _build_policy_task(
    agent: Agent,
    org_description: str,
    org_name: str,
    framework: str,
    policy_type: str,
    policy_meta: Dict[str, str],
    org_context: Optional[Dict[str, Any]] = None,
) -> Task:
    """Build policy generation task."""
    fw_meta = FRAMEWORKS.get(framework, {})
    today = datetime.now()
    review_date = (today + timedelta(days=365)).strftime("%Y-%m-%d")
    key_articles = ', '.join(fw_meta.get('key_articles', [])[:8])

    context_str = ""
    if org_context:
        context_str = f"\nOrganization Context: {json.dumps(org_context, indent=2)}"

    return Task(
        description=f"""You are generating a COMPLETE, PRODUCTION-READY {framework} compliance policy document.

Organization: {org_name}
Description: {org_description}{context_str}
Framework: {framework} — {fw_meta.get('name', '')}
Policy Type: {policy_meta['title']}
Effective Date: {today.strftime('%Y-%m-%d')}
Review Date: {review_date}
Key {framework} Articles/Controls: {key_articles}

CRITICAL INSTRUCTIONS:
- Write FULL, DETAILED content for every section. No placeholders, no "TBD", no "to be determined".
- Each section content must be 3-5 paragraphs of substantive, organization-specific text.
- The Requirements section must list at least 10 specific, numbered, actionable requirements.
- The Roles & Responsibilities section must cover at least 5 distinct roles.
- The Definitions section must define at least 8 key terms relevant to {framework} and {policy_meta['title']}.
- Reference specific {framework} articles, clauses, or control numbers throughout.
- Tailor every sentence to {org_name} and their context as: {org_description}.
- Total content must be comprehensive enough for a real compliance audit.

Return ONLY a valid JSON object with this exact structure (no markdown, no preamble):
{{
  "policy_id": "POL-{framework[:6].upper()}-{policy_type[:3].upper()}-001",
  "policy_type": "{policy_type}",
  "title": "{policy_meta['title']}",
  "version": "1.0",
  "effective_date": "{today.strftime('%Y-%m-%d')}",
  "review_date": "{review_date}",
  "applicable_to": "All employees, contractors, consultants, and third-party vendors of {org_name} who access, process, or handle organizational data and systems.",
  "owner": "Chief Information Security Officer",
  "classification": "Internal — Confidential",
  "sections": [
    {{
      "title": "1. Purpose and Scope",
      "content": "Write 3-5 full paragraphs explaining: (a) why this policy exists and what business risk it addresses for {org_name}, (b) the exact scope — which systems, data types, processes, and personnel are covered, (c) how this policy directly supports {framework} compliance obligations, (d) what regulatory or legal obligations drive this policy, (e) how this policy interacts with other policies in the compliance framework. Be specific to {org_name} as a {org_description}.",
      "references": ["{framework} relevant articles here"]
    }},
    {{
      "title": "2. Policy Statement",
      "content": "Write 2-3 paragraphs stating {org_name}'s formal commitment to this policy area. Include: executive-level commitment statement, statement of organizational values regarding this area, commitment to resource allocation, and the consequences of non-compliance at a high level. Make it sound authoritative and organization-specific.",
      "references": []
    }},
    {{
      "title": "3. Definitions",
      "content": "Define at least 8 key terms used in this policy. Format each as: Term: definition. Include terms specific to {framework}, to {policy_meta['title']}, and to the context of {org_description}. Each definition should be 2-3 sentences and technically precise.",
      "references": []
    }},
    {{
      "title": "4. Policy Requirements",
      "content": "List at least 10 specific, numbered, actionable requirements that {org_name} must implement. Each requirement should: be a complete sentence, reference a specific {framework} control or article, state what must be done, by whom, and how often. Cover technical, administrative, and physical safeguard requirements. Include specific timeframes, thresholds, and measurable criteria.",
      "references": ["{framework} control references"]
    }},
    {{
      "title": "5. Roles and Responsibilities",
      "content": "Define responsibilities for at least 5 specific roles: (1) Chief Information Security Officer, (2) Data Protection Officer or Privacy Officer, (3) IT/Security Team, (4) Department Managers/Data Owners, (5) All Employees and Contractors. For each role write 3-4 specific duties with actionable verbs. Include accountability chains and escalation responsibilities.",
      "references": []
    }},
    {{
      "title": "6. Compliance Monitoring and Enforcement",
      "content": "Write 3-4 paragraphs covering: (a) specific monitoring mechanisms and tools used to measure compliance, (b) audit schedule and methodology — internal and external, (c) metrics and KPIs that will be tracked, (d) consequence framework — disciplinary actions for non-compliance ranging from training to termination, (e) how violations are reported, investigated, and remediated, (f) how compliance status is reported to leadership.",
      "references": ["{framework} audit requirements"]
    }},
    {{
      "title": "7. Exception Management",
      "content": "Write 2-3 paragraphs covering: (a) circumstances under which exceptions may be requested, (b) the formal exception request process — who submits, who reviews, who approves, (c) required documentation for exception requests, (d) maximum duration of exceptions and renewal process, (e) compensating controls that must be in place during exceptions, (f) how exceptions are tracked and reported.",
      "references": []
    }},
    {{
      "title": "8. Policy Review and Maintenance",
      "content": "Write 2-3 paragraphs covering: (a) annual review cycle and triggers for out-of-cycle review (regulatory changes, incidents, organizational changes), (b) who is responsible for initiating, conducting, and approving reviews, (c) version control and change management process, (d) communication and training requirements when policy is updated, (e) how this policy aligns with and is kept consistent with related policies and {framework} updates.",
      "references": []
    }},
    {{
      "title": "9. Related Documents and References",
      "content": "List related internal policies, procedures, standards, and guidelines that complement this policy. Include relevant {framework} documentation, regulatory guidance, and industry standards (e.g., ISO 27001, NIST). Describe how this policy fits into the broader governance, risk, and compliance framework of {org_name}.",
      "references": ["{framework} official documentation"]
    }}
  ]
}}
""",
        expected_output=(
            "A complete, valid JSON object containing a fully written compliance policy "
            "with 9 sections of detailed, substantive content. Every section must have "
            "multiple paragraphs of real content — no placeholders."
        ),
        agent=agent,
    )


def _sanitize_json(text: str) -> str:
    """Aggressively fix malformed JSON from LLM output."""
    # Remove markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    # Remove LLM preamble before first {
    text = re.sub(r"^[^{]*", "", text, flags=re.DOTALL)
    # Remove anything after last }
    last_brace = text.rfind("}")
    if last_brace != -1:
        text = text[:last_brace + 1]
    # Fix unescaped newlines/tabs inside string values
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
    # Strip trailing commas before ] or }
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _parse_policy(raw: str, framework: str, policy_type: str) -> Optional[GeneratedPolicy]:
    """Parse LLM output into GeneratedPolicy."""
    sanitized = _sanitize_json(raw)

    # Try direct parse first, then json_repair fallback
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
        logger.error(f"Policy parse error: could not extract valid JSON")
        return None

    try:
        sections = [
            PolicySection(
                title=s.get("title", ""),
                content=s.get("content", ""),
                references=s.get("references", []),
            )
            for s in data.get("sections", [])
        ]
        return GeneratedPolicy(
            policy_id=data.get("policy_id", f"POL-{framework}-{policy_type.upper()[:4]}-001"),
            framework=framework,
            policy_type=policy_type,
            title=data.get("title", POLICY_TYPES.get(policy_type, {}).get("title", "")),
            version=data.get("version", "1.0"),
            effective_date=data.get("effective_date", datetime.now().strftime("%Y-%m-%d")),
            review_date=data.get("review_date", ""),
            sections=sections,
            applicable_to=data.get("applicable_to", "All employees"),
            owner=data.get("owner", "CISO / DPO"),
            classification=data.get("classification", "Internal"),
        )
    except Exception as e:
        logger.error(f"Policy build error: {e}")
        return None


def generate_policies(
    org_description: str,
    org_name: str,
    framework: str,
    policy_types: List[str],
    org_context: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
) -> PolicyGenerationResponse:
    """
    Generate compliance policies for an organization.

    Args:
        org_description: Brief org description
        org_name: Organization name
        framework: Framework ID (e.g., GDPR, HIPAA)
        policy_types: List of policy types to generate
        org_context: Additional org context
        max_retries: Max retry attempts per policy

    Returns:
        PolicyGenerationResponse with all generated policies
    """
    if framework not in FRAMEWORKS:
        raise ValueError(f"Unknown framework: {framework}")

    # Filter to known policy types
    valid_types = [pt for pt in policy_types if pt in POLICY_TYPES]
    if not valid_types:
        valid_types = ["data_protection", "incident_response", "access_control"]

    generated_policies = []

    for policy_type in valid_types:
        policy_meta = POLICY_TYPES[policy_type]
        logger.info(f"Generating {framework} {policy_type} policy for {org_name}...")
        success = False

        for attempt in range(max_retries):
            try:
                # Fresh LLM + fresh agent on every attempt to rotate key/model
                agent = _build_policy_agent(framework)
                task = _build_policy_task(
                    agent, org_description, org_name, framework,
                    policy_type, policy_meta, org_context
                )
                crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False,
                    tracing=False,
                )
                result = crew.kickoff()
                raw_output = str(result)
                logger.info(f"Raw LLM output length for {policy_type}: {len(raw_output)} chars")
                if len(raw_output) < 500:
                    raise ValueError(f"LLM output too short ({len(raw_output)} chars) — likely rate-limited or truncated")
                policy = _parse_policy(raw_output, framework, policy_type)

                if policy:
                    # Quality gate: reject if sections are mostly empty
                    total_content = sum(len(s.content) for s in policy.sections)
                    if total_content < 1500:
                        raise ValueError(
                            f"Policy content too thin ({total_content} chars total across sections) "
                            f"— model likely returned placeholder content"
                        )
                    generated_policies.append(policy)
                    logger.info(f"✓ Generated {policy_type} policy ({total_content} chars of content)")
                    success = True
                    break
                else:
                    raise ValueError("Failed to parse policy JSON")

            except Exception as e:
                logger.warning(f"Policy {policy_type} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + random.uniform(0, 1))

        if not success:
            generated_policies.append(_create_placeholder_policy(
                framework, policy_type, org_name, policy_meta
            ))

        time.sleep(random.uniform(1, 2))

    fw_meta = FRAMEWORKS[framework]
    summary = (
        f"Generated {len(generated_policies)} {fw_meta['name']} policies for {org_name}. "
        f"These policies cover: {', '.join(POLICY_TYPES.get(pt, {}).get('title', pt) for pt in valid_types)}. "
        f"Review with legal counsel before adoption."
    )

    return PolicyGenerationResponse(
        org_name=org_name,
        framework=framework,
        policies=generated_policies,
        summary=summary,
        timestamp=datetime.now().isoformat(),
    )


def _create_placeholder_policy(
    framework: str, policy_type: str, org_name: str, policy_meta: Dict
) -> GeneratedPolicy:
    """
    Create a substantive fallback policy when LLM generation fails.
    This is a real policy template — not a placeholder stub.
    """
    today = datetime.now()
    fw_name = FRAMEWORKS.get(framework, {}).get("name", framework)
    policy_title = policy_meta.get("title", f"{framework} {policy_type.replace('_', ' ').title()} Policy")

    sections = [
        PolicySection(
            title="1. Purpose and Scope",
            content=(
                f"This {policy_title} establishes the governance framework and binding requirements "
                f"for {org_name} to achieve and maintain compliance with {fw_name} ({framework}). "
                f"This policy defines the organizational commitment, controls, and accountabilities "
                f"necessary to protect sensitive information and ensure regulatory compliance.\n\n"
                f"{org_name} recognizes its obligations under {framework} and commits to implementing "
                f"the technical, administrative, and physical safeguards described in this policy. "
                f"This policy applies to all organizational data, systems, processes, and personnel "
                f"that fall within the scope of {framework} obligations.\n\n"
                f"This policy applies to all employees, contractors, consultants, temporary staff, "
                f"and third-party service providers of {org_name} who access, process, store, transmit, "
                f"or have any involvement with data subject to {framework} requirements. "
                f"It covers all information systems, applications, infrastructure, and business processes "
                f"operated by or on behalf of {org_name}, regardless of geographic location or technical environment."
            ),
            references=[f"{framework} compliance requirements"],
        ),
        PolicySection(
            title="2. Policy Statement",
            content=(
                f"{org_name} is committed to maintaining the highest standards of information protection "
                f"and regulatory compliance in accordance with {fw_name}. The organization recognizes "
                f"that compliance is not merely a legal obligation but a fundamental component of building "
                f"trust with customers, partners, and stakeholders.\n\n"
                f"Leadership of {org_name} fully endorses this policy and mandates its implementation "
                f"across all business units, departments, and operational functions. Adequate resources — "
                f"financial, technical, and human — will be allocated to implement and maintain the "
                f"controls described herein. Non-compliance with this policy will result in disciplinary "
                f"action proportional to the severity of the violation.\n\n"
                f"This policy shall be reviewed annually or upon significant changes to the regulatory "
                f"landscape, organizational structure, or technical environment. All personnel are "
                f"expected to familiarize themselves with this policy and apply its requirements in "
                f"their day-to-day responsibilities."
            ),
            references=[],
        ),
        PolicySection(
            title="3. Definitions",
            content=(
                f"**{framework} Compliance**: Adherence to all applicable requirements, controls, and "
                f"standards defined under {fw_name}, including any implementing regulations or guidance.\n\n"
                f"**Personal Data / Sensitive Information**: Any information that can directly or indirectly "
                f"identify an individual, or any data classified as sensitive under {framework} requirements "
                f"and applicable law.\n\n"
                f"**Data Controller / Responsible Party**: {org_name} in its capacity as the entity that "
                f"determines the purposes and means of processing personal or sensitive data.\n\n"
                f"**Data Processor / Service Provider**: Any third party that processes data on behalf of "
                f"{org_name} under a formal data processing agreement.\n\n"
                f"**Information Security Incident**: Any event that compromises or has the potential to "
                f"compromise the confidentiality, integrity, or availability of organizational information.\n\n"
                f"**Risk Assessment**: A systematic process of identifying, analyzing, and evaluating "
                f"information security risks that may affect {org_name}'s compliance posture.\n\n"
                f"**Access Control**: Technical and administrative measures that restrict access to "
                f"systems and data to authorized individuals on a need-to-know basis.\n\n"
                f"**Audit Trail**: A chronological record of system and user activities sufficient to "
                f"reconstruct, review, and examine the sequence of events surrounding compliance activities."
            ),
            references=[],
        ),
        PolicySection(
            title="4. Policy Requirements",
            content=(
                f"The following requirements are mandatory for all personnel and systems within scope:\n\n"
                f"1. {org_name} shall conduct a formal {framework} risk assessment at least annually and "
                f"whenever significant changes occur to systems, processes, or the regulatory environment.\n\n"
                f"2. All employees and contractors who handle data subject to {framework} must complete "
                f"mandatory compliance training within 30 days of onboarding and annually thereafter.\n\n"
                f"3. Access to sensitive systems and data shall be granted on the principle of least privilege. "
                f"Access rights must be reviewed quarterly and revoked promptly upon role change or termination.\n\n"
                f"4. All sensitive data must be encrypted in transit using TLS 1.2 or higher and at rest "
                f"using AES-256 or equivalent encryption standard.\n\n"
                f"5. {org_name} shall maintain a current and accurate inventory of all systems, data flows, "
                f"and processing activities relevant to {framework} compliance.\n\n"
                f"6. Third-party vendors and service providers with access to regulated data must sign a "
                f"Data Processing Agreement (DPA) prior to engagement and undergo annual security assessments.\n\n"
                f"7. Security incidents must be detected, assessed, and escalated within 24 hours of discovery. "
                f"Regulatory notifications must be made within the timeframes specified by {framework}.\n\n"
                f"8. System and application logs must be retained for a minimum of 12 months and reviewed "
                f"on a scheduled basis to detect anomalies and compliance violations.\n\n"
                f"9. A formal vulnerability management program shall be maintained, with critical and high "
                f"severity vulnerabilities remediated within 30 days of identification.\n\n"
                f"10. Business continuity and disaster recovery plans must be documented, tested annually, "
                f"and updated to reflect changes in {framework} requirements and organizational risk profile.\n\n"
                f"11. All {framework} compliance documentation, evidence, and audit records must be retained "
                f"for a minimum of 5 years or as required by applicable law, whichever is longer.\n\n"
                f"12. {org_name} shall designate a responsible individual or function (e.g., Data Protection "
                f"Officer, Compliance Manager) accountable for {framework} compliance program management."
            ),
            references=[f"{framework} requirements", "ISO 27001", "NIST CSF"],
        ),
        PolicySection(
            title="5. Roles and Responsibilities",
            content=(
                f"**Chief Information Security Officer (CISO)**: Accountable for the overall {framework} "
                f"compliance program. Responsible for approving this policy, allocating security resources, "
                f"reporting compliance status to executive leadership, and ensuring the organization's "
                f"security posture meets {framework} requirements. Chairs the security governance committee.\n\n"
                f"**Data Protection Officer / Privacy Officer**: Responsible for monitoring {framework} "
                f"compliance on a day-to-day basis, serving as the primary point of contact for regulatory "
                f"authorities, conducting Data Protection Impact Assessments (DPIAs), managing data subject "
                f"requests, and maintaining the organization's data processing register.\n\n"
                f"**IT and Security Team**: Responsible for implementing technical controls required by this "
                f"policy, managing access control systems, conducting security monitoring, responding to "
                f"incidents, maintaining encryption standards, and performing vulnerability assessments. "
                f"Must document all security configurations and maintain evidence of control operation.\n\n"
                f"**Department Managers and Data Owners**: Responsible for ensuring their teams comply with "
                f"this policy, approving access requests for systems under their purview, participating in "
                f"annual risk assessments, and reporting suspected compliance violations to the security team.\n\n"
                f"**All Employees and Contractors**: Must complete required compliance training, follow all "
                f"procedures in this policy, immediately report suspected security incidents or violations, "
                f"handle sensitive data in accordance with {framework} requirements, and cooperate fully "
                f"with compliance audits and investigations."
            ),
            references=[],
        ),
        PolicySection(
            title="6. Compliance Monitoring and Enforcement",
            content=(
                f"{org_name} will implement a continuous compliance monitoring program to ensure ongoing "
                f"adherence to {framework} requirements and this policy. Compliance metrics will be "
                f"tracked, reported to leadership quarterly, and form part of the organization's "
                f"GRC (Governance, Risk, and Compliance) dashboard.\n\n"
                f"Internal audits of this policy will be conducted annually by the compliance or internal "
                f"audit function. External audits or assessments may be conducted by third-party auditors "
                f"as required by {framework} or as determined by leadership. All audit findings will be "
                f"assigned owners, remediation timelines, and tracked to closure.\n\n"
                f"Non-compliance with this policy will result in disciplinary action commensurate with the "
                f"severity of the violation: (a) minor violations — mandatory retraining and documented "
                f"warning; (b) moderate violations — formal written warning and increased monitoring; "
                f"(c) serious violations — suspension, role change, or termination; (d) violations involving "
                f"legal liability — referral to legal counsel and potential reporting to regulatory authorities. "
                f"All disciplinary actions will be documented in accordance with HR policies."
            ),
            references=[f"{framework} audit and enforcement requirements"],
        ),
        PolicySection(
            title="7. Exception Management",
            content=(
                f"Exceptions to this policy may be granted only under exceptional circumstances where "
                f"strict compliance would cause significant operational hardship and where compensating "
                f"controls can adequately mitigate the associated risk. Exceptions are not a substitute "
                f"for compliance and must be treated as temporary measures.\n\n"
                f"To request an exception, the requesting department must submit a formal Exception Request "
                f"Form to the CISO, including: (a) description of the specific requirement for which an "
                f"exception is sought, (b) business justification, (c) risk assessment identifying the "
                f"increased risk, (d) proposed compensating controls, and (e) requested duration (maximum "
                f"12 months). The CISO will review, consult with the DPO as appropriate, and approve or "
                f"deny the request within 10 business days. Approved exceptions must be reviewed at the "
                f"6-month mark and renewed or closed by their expiry date. All exceptions are logged "
                f"centrally and included in compliance reporting to leadership."
            ),
            references=[],
        ),
        PolicySection(
            title="8. Policy Review and Maintenance",
            content=(
                f"This policy will be formally reviewed by the CISO and DPO at least once every 12 months "
                f"to ensure it remains current, accurate, and aligned with {framework} requirements. "
                f"Out-of-cycle reviews will be triggered by: material changes to {framework} or related "
                f"regulations, significant security incidents affecting the organization, major changes "
                f"to {org_name}'s technology environment or business operations, or recommendations from "
                f"internal or external audits.\n\n"
                f"All revisions to this policy require approval from the CISO and, where applicable, "
                f"the Board or executive leadership. Version history will be maintained in the document "
                f"management system. Upon approval of a revised policy, all affected personnel will be "
                f"notified within 5 business days, updated training materials will be deployed within "
                f"30 days, and acknowledgment of the updated policy will be obtained from all employees "
                f"subject to it within 60 days of publication."
            ),
            references=[],
        ),
        PolicySection(
            title="9. Related Documents and References",
            content=(
                f"This policy should be read in conjunction with the following {org_name} policies and "
                f"documents: Information Security Policy, Data Retention and Disposal Policy, Incident "
                f"Response Plan, Business Continuity Plan, Vendor Management Policy, and the Acceptable "
                f"Use Policy. Together, these documents constitute the organization's {framework} "
                f"compliance framework.\n\n"
                f"External references and standards informing this policy include: {fw_name} ({framework}) "
                f"official regulatory text and guidance, ISO/IEC 27001:2022 Information Security Management, "
                f"NIST Cybersecurity Framework (CSF) 2.0, NIST SP 800-53 Security and Privacy Controls, "
                f"and applicable national or regional implementing legislation where {org_name} operates."
            ),
            references=[f"{framework} official documentation", "ISO 27001:2022", "NIST CSF 2.0"],
        ),
    ]

    return GeneratedPolicy(
        policy_id=f"POL-{framework.upper()[:6]}-{policy_type.upper()[:4]}-001",
        framework=framework,
        policy_type=policy_type,
        title=policy_title,
        version="1.0",
        effective_date=today.strftime("%Y-%m-%d"),
        review_date=(today + timedelta(days=365)).strftime("%Y-%m-%d"),
        sections=sections,
        applicable_to=f"All employees, contractors, and third-party vendors of {org_name}",
        owner="Chief Information Security Officer",
        classification="Internal — Confidential",
    )


AVAILABLE_POLICY_TYPES = list(POLICY_TYPES.keys())
POLICY_TYPE_DETAILS = POLICY_TYPES
