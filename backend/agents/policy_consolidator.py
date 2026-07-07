"""
Policy Consolidation Agent
Consolidates multiple framework policies into a single unified master policy.
Handles conflict resolution, deduplication, and cross-framework alignment.
"""

import json
import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from crewai import Agent, Task, Crew, Process

from config.llm_config import get_fresh_llm, get_llm_with_fallback
from config.frameworks import FRAMEWORKS
from models.schemas import GeneratedPolicy, PolicySection

logger = logging.getLogger(__name__)


def _build_consolidator_agent() -> Agent:
    """Build the policy consolidation agent."""
    return Agent(
        role="Compliance Integration Architect",
        goal=(
            "Synthesize multiple framework-specific policies into a single, "
            "unified master compliance policy that addresses all selected frameworks "
            "without redundancy or conflict."
        ),
        backstory="""You are a senior compliance architect with 20+ years of experience 
        consolidating compliance requirements across multiple regulations.
        
        You excel at:
        - Identifying duplicate/overlapping requirements across frameworks
        - Resolving conflicts between frameworks (choosing the stricter requirement)
        - Creating domain-based organizational structures (Access Control, Data Protection, etc.)
        - Cross-referencing requirements to their source frameworks
        - Ensuring no requirement is missed or lost in consolidation
        - Creating practical, implementable unified policies
        
        Your consolidated policies are:
        - Legally sound and reference all relevant frameworks
        - Organized by domain (not framework) for clarity
        - Free of redundancy and contradiction
        - Audit-ready with clear framework traceability
        - Immediately actionable by the organization""",
        tools=[],
        verbose=False,
        allow_delegation=False,
        llm=get_fresh_llm(temperature=0.1, rotate=True),
    )


def _build_consolidation_task(
    agent: Agent,
    org_name: str,
    org_description: str,
    selected_frameworks: List[str],
    policies_data: List[Dict[str, Any]],
    org_context: Optional[Dict[str, Any]] = None,
) -> Task:
    """Build the policy consolidation task."""
    
    current_year = datetime.now().year
    frameworks_list = ", ".join(selected_frameworks)
    framework_details = "\n".join([
        f"- {fw}: {FRAMEWORKS.get(fw, {}).get('name', fw)}"
        for fw in selected_frameworks
    ])
    
    # Create formatted policies input
    policies_text = _format_policies_for_consolidation(policies_data)
    
    context_str = ""
    if org_context:
        context_str = f"\nOrganization Context: {json.dumps(org_context, indent=2)}"
    
    # Format frameworks list for JSON output
    frameworks_json = json.dumps(selected_frameworks)
    
    return Task(
        agent=agent,
        description=f"""You are consolidating compliance policies from multiple frameworks 
into ONE unified master policy for {org_name}.

ORGANIZATION CONTEXT:
- Name: {org_name}
- Description: {org_description}{context_str}

SELECTED FRAMEWORKS:
{framework_details}

INDIVIDUAL FRAMEWORK POLICIES:
{policies_text}

YOUR TASK - Create a UNIFIED MASTER COMPLIANCE POLICY:

1. CONFLICT RESOLUTION:
   - Where frameworks conflict, apply the STRICTER requirement
   - Document which frameworks mandate each requirement
   - Create a single integrated requirement that satisfies all

2. DEDUPLICATION:
   - Identify overlapping requirements across frameworks
   - Merge them into single, cross-referenced requirements
   - Avoid repeating the same concept multiple times

3. DOMAIN ORGANIZATION:
   - Organize the master policy by COMPLIANCE DOMAIN (not by framework)
   - Domains should include:
     * Access Control & Identity Management
     * Data Protection & Privacy
     * Security Incident Response
     * Third-Party Risk Management
     * Data Retention & Disposal
     * Encryption & Key Management
     * Business Continuity & Disaster Recovery
     * Compliance Monitoring & Audit
   - Within each domain, list integrated requirements with framework citations

4. CROSS-REFERENCE MATRIX:
   - Create a matrix showing which frameworks require which controls
   - Highlight if requirement is mandatory vs recommended for any framework
   - Note maximum penalties for non-compliance per framework

5. QUALITY CHECKS:
   - Ensure no requirements are lost in consolidation
   - Verify all frameworks are represented
   - Check for logical consistency and no internal conflicts
   - Ensure the master policy is immediately implementable

OUTPUT FORMAT:
You must return ONLY valid JSON (no markdown, no code blocks) in this exact structure:
{{
    "master_policy_id": "MASTER-{current_year}-001",
    "title": "Unified Compliance Master Policy for {org_name}",
    "executive_summary": "High-level overview of consolidated compliance approach...",
    "aligned_frameworks": {frameworks_json},
    "consolidation_notes": "Description of how conflicts were resolved and requirements merged...",
    "domains": [
        {{
            "domain_name": "Access Control & Identity Management",
            "domain_description": "...",
            "integrated_requirements": [
                {{
                    "requirement_id": "REQ-001",
                    "title": "Unified Access Control Requirement",
                    "description": "Detailed description consolidating all framework requirements...",
                    "frameworks": {frameworks_json},
                    "framework_references": ["ISO 27001:A.9.2", "SOC2 CC6.1"],
                    "is_mandatory": true,
                    "max_penalty": "€20 million per framework",
                    "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                    "responsibility": "IT Security & IAM Team"
                }}
            ]
        }}
    ],
    "compliance_matrix": [
        {{
            "control_name": "Multi-Factor Authentication",
            "iso_27001": "Mandatory",
            "gdpr": "Required",
            "soc2": "Required",
            "hipaa": "Mandatory"
        }}
    ],
    "implementation_roadmap": [
        {{
            "phase": 1,
            "duration": "Months 1-3",
            "focus": "Quick wins and foundational controls",
            "controls": ["Control names"]
        }}
    ]
}}

CRITICAL: Return ONLY the JSON object, nothing else. No explanations, no markdown.""",
        expected_output="Valid JSON master policy consolidation",
    )


def _format_policies_for_consolidation(policies_data: List[Dict[str, Any]]) -> str:
    """Format individual policies into readable consolidation input."""
    formatted = []
    for policy in policies_data:
        framework = policy.get("framework", "Unknown")
        policy_type = policy.get("policy_type", "Unknown")
        title = policy.get("title", "Untitled")
        
        sections_text = ""
        for section in policy.get("sections", []):
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            # Truncate long content for readability
            if len(section_content) > 500:
                section_content = section_content[:500] + "..."
            sections_text += f"  - {section_title}: {section_content}\n"
        
        policy_str = f"""
FRAMEWORK: {framework}
POLICY TYPE: {policy_type}
TITLE: {title}
SECTIONS:
{sections_text}
---
"""
        formatted.append(policy_str)
    
    return "\n".join(formatted)


def _parse_consolidated_policy(raw: str) -> Optional[Dict[str, Any]]:
    """Parse LLM response into consolidated policy dict."""
    logger.debug("Parsing consolidated policy response...")
    
    try:
        # Try direct JSON parse
        consolidated = json.loads(raw)
        logger.info("✓ Successfully parsed consolidated policy JSON")
        return consolidated
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON, attempting repair...")
        
        # Try to extract JSON from text
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            try:
                consolidated = json.loads(json_match.group())
                logger.info("✓ Extracted and parsed consolidated policy JSON")
                return consolidated
            except json.JSONDecodeError:
                pass
        
        # Try json_repair if available
        try:
            from json_repair import repair_json
            repaired = repair_json(raw)
            consolidated = json.loads(repaired)
            logger.info("✓ Repaired and parsed consolidated policy JSON")
            return consolidated
        except Exception:
            pass
    
    logger.error("❌ Failed to parse consolidated policy response")
    return None


def consolidate_policies(
    org_name: str,
    org_description: str,
    selected_frameworks: List[str],
    policies: List[Dict[str, Any]],
    org_context: Optional[Dict[str, Any]] = None,
    personalization_data: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Consolidate multiple framework policies into a single master policy.
    
    Args:
        org_name: Organization name
        org_description: Organization description
        selected_frameworks: List of framework IDs (e.g., ["gdpr", "iso-27001"])
        policies: List of individual policy dicts from policy_generator
        org_context: Optional org profiling context
        personalization_data: Optional org personalization (CISO, DPO, tools, etc.)
    
    Returns:
        Dict with consolidated master policy, or None if failed
    """
    
    logger.info(f"🔄 Consolidating {len(policies)} policies from {len(selected_frameworks)} frameworks")
    logger.info(f"   Frameworks: {', '.join(selected_frameworks)}")
    
    try:
        # Build consolidator agent and task
        agent = _build_consolidator_agent()
        task = _build_consolidation_task(
            agent=agent,
            org_name=org_name,
            org_description=org_description,
            selected_frameworks=selected_frameworks,
            policies_data=policies,
            org_context=org_context,
        )
        
        # Create and execute crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        
        logger.info("🚀 Executing policy consolidation crew...")
        result = crew.kickoff()
        
        # Parse result
        consolidated_data = _parse_consolidated_policy(str(result))
        
        if not consolidated_data:
            logger.error("❌ Failed to parse consolidation result")
            return _create_fallback_consolidated_policy(
                org_name, selected_frameworks, policies
            )
        
        # Regenerate master_policy_id to avoid UNIQUE constraint violations
        # (LLM generates MASTER-2026-001, which conflicts on second run)
        import uuid
        unique_suffix = str(uuid.uuid4())[:8].upper()
        consolidated_data["master_policy_id"] = f"MASTER-{datetime.now().year}-{unique_suffix}"
        
        # Validate consolidation output
        if not _validate_consolidated_policy(consolidated_data):
            logger.warning("⚠ Consolidated policy validation failed, using fallback")
            return _create_fallback_consolidated_policy(
                org_name, selected_frameworks, policies
            )
        
        logger.info(f"✓ Successfully consolidated policies")
        logger.info(f"  - Master Policy ID: {consolidated_data.get('master_policy_id')}")
        logger.info(f"  - Domains: {len(consolidated_data.get('domains', []))}")
        
        return consolidated_data
        
    except Exception as e:
        logger.error(f"❌ Policy consolidation failed: {str(e)}", exc_info=True)
        return _create_fallback_consolidated_policy(
            org_name, selected_frameworks, policies
        )


def _validate_consolidated_policy(data: Dict[str, Any]) -> bool:
    """Validate consolidated policy structure."""
    required_fields = [
        "master_policy_id", "title", "aligned_frameworks", "domains"
    ]
    for field in required_fields:
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return False
    
    if not isinstance(data.get("domains"), list) or len(data["domains"]) == 0:
        logger.warning("Domains must be non-empty list")
        return False
    
    return True


def _create_fallback_consolidated_policy(
    org_name: str,
    selected_frameworks: List[str],
    policies: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a fallback consolidated policy by simple merging if AI consolidation fails.
    This ensures we always return something usable.
    """
    logger.info("📋 Creating fallback consolidated policy by merging...")
    
    today = datetime.now()
    review_date = (today + timedelta(days=365)).strftime("%d %B %Y")
    
    # Group policies by domain (use policy_type as proxy)
    domains_map = {}
    policy_type_to_domain = {
        "data_protection": "Data Protection & Privacy",
        "incident_response": "Security Incident Response",
        "access_control": "Access Control & Identity Management",
        "data_retention": "Data Retention & Disposal",
        "third_party_risk": "Third-Party Risk Management",
        "acceptable_use": "Acceptable Use Policy",
        "business_continuity": "Business Continuity & Disaster Recovery",
        "encryption": "Encryption & Key Management",
    }
    
    for policy in policies:
        policy_type = policy.get("policy_type", "other")
        domain = policy_type_to_domain.get(policy_type, "General Policies")
        
        if domain not in domains_map:
            domains_map[domain] = {
                "domain_name": domain,
                "domain_description": f"Consolidated requirements for {domain.lower()}",
                "integrated_requirements": []
            }
        
        # Convert policy to integrated requirement
        req = {
            "requirement_id": policy.get("policy_id", "REQ-UNKNOWN"),
            "title": policy.get("title", "Untitled Requirement"),
            "description": _merge_sections_to_text(policy.get("sections", [])),
            "frameworks": selected_frameworks,
            "framework_references": [
                ref for section in policy.get("sections", [])
                for ref in section.get("references", [])
            ],
            "is_mandatory": True,
            "implementation_steps": [
                "1. Review the requirement",
                "2. Implement necessary controls",
                "3. Document implementation",
                "4. Test and validate"
            ],
            "responsibility": policy.get("owner", "Compliance Officer")
        }
        domains_map[domain]["integrated_requirements"].append(req)
    
    # Generate unique master_policy_id using timestamp to avoid UNIQUE constraint violations
    import uuid
    unique_suffix = str(uuid.uuid4())[:8].upper()
    
    return {
        "master_policy_id": f"MASTER-{today.year}-{unique_suffix}",
        "title": f"Unified Compliance Master Policy — {org_name}",
        "executive_summary": (
            f"This master policy consolidates requirements from {len(selected_frameworks)} "
            f"compliance frameworks ({', '.join(selected_frameworks)}) into a unified, "
            f"organization-wide compliance strategy. Requirements are organized by domain "
            f"and cross-referenced to their source frameworks."
        ),
        "aligned_frameworks": selected_frameworks,
        "consolidation_notes": (
            "Fallback consolidation: Policies grouped by domain with framework references preserved. "
            "All individual policy requirements are represented."
        ),
        "domains": list(domains_map.values()),
        "compliance_matrix": _build_compliance_matrix(selected_frameworks, policies),
        "implementation_roadmap": _build_implementation_roadmap(),
    }


def _merge_sections_to_text(sections: List[Dict[str, Any]]) -> str:
    """Merge policy sections into single descriptive text."""
    texts = []
    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")
        if title and content:
            texts.append(f"{title}: {content}")
        elif content:
            texts.append(content)
    return "\n".join(texts)


def _build_compliance_matrix(frameworks: List[str], policies: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build a compliance matrix showing which frameworks require which controls."""
    matrix = []
    for policy in policies[:5]:  # Limit to first 5 for readability
        matrix.append({
            "control_name": policy.get("title", "Unknown"),
            **{fw: "Required" for fw in frameworks}
        })
    return matrix


def _build_implementation_roadmap() -> List[Dict[str, Any]]:
    """Build a phased implementation roadmap."""
    return [
        {
            "phase": 1,
            "duration": "Months 1-3",
            "focus": "Foundation and quick wins",
            "controls": ["Access Control", "Data Classification", "Incident Response"]
        },
        {
            "phase": 2,
            "duration": "Months 4-6",
            "focus": "Core operational controls",
            "controls": ["Data Protection", "Third-Party Risk", "Encryption"]
        },
        {
            "phase": 3,
            "duration": "Months 7-12",
            "focus": "Advanced and continuous monitoring",
            "controls": ["Compliance Monitoring", "Business Continuity", "Annual Review"]
        }
    ]
