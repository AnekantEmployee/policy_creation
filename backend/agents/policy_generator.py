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

from backend.config.llm_config import get_llm_with_fallback, get_fresh_llm, get_tavily_key
from backend.config.frameworks import FRAMEWORKS
from backend.models.schemas import (
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
        from crewai_tools import TavilySearchResults
        tavily_key = get_tavily_key()
        tools = [TavilySearchResults(api_key=tavily_key, max_results=3)]
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
        llm=get_llm_with_fallback(temperature=0.2),
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

    context_str = ""
    if org_context:
        context_str = f"\nOrganization Context: {json.dumps(org_context, indent=2)}"

    return Task(
        description=f"""Generate a comprehensive {framework} {policy_meta['title']} for:

Organization: {org_name}
Description: {org_description}
Framework: {framework} — {fw_meta.get('name', '')}
Policy Type: {policy_type} — {policy_meta['description']}
Effective Date: {today.strftime('%Y-%m-%d')}
Review Date: {review_date}
{context_str}

Generate a COMPLETE, DETAILED policy document with these sections:
1. Purpose & Scope
2. Policy Statement  
3. Definitions
4. Policy Requirements (detailed, with sub-sections)
5. Roles & Responsibilities
6. Compliance & Enforcement
7. Exceptions
8. Review & Updates
9. References (list specific {framework} articles/sections)

The policy MUST:
- Reference specific {framework} articles/sections: {', '.join(fw_meta.get('key_articles', []))}
- Be tailored to a {org_description} organization
- Use clear, formal language appropriate for a legal document
- Include specific, actionable requirements (not vague statements)
- Be immediately usable (no [PLACEHOLDER] gaps)

Return ONLY valid JSON:
{{
  "policy_id": "POL-{framework}-{policy_type.upper()[:4]}-001",
  "policy_type": "{policy_type}",
  "title": "{policy_meta['title']}",
  "version": "1.0",
  "effective_date": "{today.strftime('%Y-%m-%d')}",
  "review_date": "{review_date}",
  "applicable_to": "All employees, contractors, and third parties with access to {org_name} systems",
  "owner": "Chief Information Security Officer / Data Protection Officer",
  "classification": "Internal",
  "sections": [
    {{
      "title": "1. Purpose & Scope",
      "content": "Detailed content here...",
      "references": ["{framework} Article X", "{framework} Section Y"]
    }},
    {{
      "title": "2. Policy Statement",
      "content": "Detailed content here...",
      "references": []
    }}
  ]
}}
""",
        expected_output=f"Valid JSON policy document for {framework} {policy_type}",
        agent=agent,
    )


def _sanitize_json(text: str) -> str:
    """Fix control characters and trailing commas that break json.loads."""
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
    # Strip trailing commas before ] or }
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _parse_policy(raw: str, framework: str, policy_type: str) -> Optional[GeneratedPolicy]:
    """Parse LLM output into GeneratedPolicy."""
    try:
        clean = re.sub(r"```json\s*", "", raw)
        clean = re.sub(r"```\s*$", "", clean)
        clean = re.sub(r"Thought:.*?(\{)", r"\1", clean, flags=re.DOTALL)

        json_match = re.search(r"\{[\s\S]*\}", clean)
        if not json_match:
            return None

        data = json.loads(_sanitize_json(json_match.group(0)))

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
        logger.error(f"Policy parse error: {e}")
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
                )
                result = crew.kickoff()
                policy = _parse_policy(str(result), framework, policy_type)

                if policy:
                    generated_policies.append(policy)
                    logger.info(f"✓ Generated {policy_type} policy")
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
    """Create a minimal placeholder policy when generation fails."""
    today = datetime.now()
    return GeneratedPolicy(
        policy_id=f"POL-{framework}-{policy_type.upper()[:4]}-001",
        framework=framework,
        policy_type=policy_type,
        title=policy_meta.get("title", f"{framework} {policy_type.replace('_', ' ').title()} Policy"),
        version="1.0",
        effective_date=today.strftime("%Y-%m-%d"),
        review_date=(today + timedelta(days=365)).strftime("%Y-%m-%d"),
        sections=[
            PolicySection(
                title="1. Purpose & Scope",
                content=(
                    f"This policy establishes {framework} compliance requirements for {org_name}. "
                    f"It applies to all employees, contractors, and systems that handle data "
                    f"subject to {framework} regulations. Manual review and customization required."
                ),
                references=[],
            )
        ],
        applicable_to=f"All employees and contractors of {org_name}",
        owner="Chief Information Security Officer",
        classification="Internal",
    )


AVAILABLE_POLICY_TYPES = list(POLICY_TYPES.keys())
POLICY_TYPE_DETAILS = POLICY_TYPES
