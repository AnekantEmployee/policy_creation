"""
Organization Profiling Agent
Analyzes org description + website → recommends applicable compliance frameworks
Uses Tavily for web research when website is provided.
"""

import json
import logging
import re
import time
import random
from datetime import datetime
from typing import List, Optional, Dict, Any

from crewai import Agent, Task, Crew, Process

from backend.config.llm_config import get_llm_with_fallback, get_tavily_key
from backend.config.frameworks import FRAMEWORKS, get_all_frameworks
from backend.models.schemas import FrameworkMatch, OrgProfileResponse

logger = logging.getLogger(__name__)


def _build_org_profiling_agent() -> Agent:
    """Build the org profiling agent with Tavily search tool."""
    try:
        from crewai_tools import TavilySearchTool, TavilyExtractorTool
        tavily_key = get_tavily_key()
        tools = [
            TavilySearchTool(api_key=tavily_key),
            TavilyExtractorTool(api_key=tavily_key),
        ]
        logger.info("Tavily search + extractor tools attached to org profiling agent")
    except Exception as e:
        logger.warning(f"Tavily not available: {e}. Running without web search.")
        tools = []

    return Agent(
        role="Compliance Intelligence Analyst",
        goal=(
            "Analyze an organization's description and website to determine which "
            "compliance frameworks apply, with detailed reasoning for each recommendation."
        ),
        backstory="""You are a senior compliance intelligence analyst with 20 years of 
        experience advising organizations across industries on regulatory requirements. 
        You have deep knowledge of GDPR, HIPAA, ISO 27001, NIST CSF, PCI DSS, SOC 2, 
        CCPA, DPDP, SOX, FedRAMP and all major global compliance frameworks.
        
        Given a brief organization description, you can instantly identify:
        - The industry and sector
        - Geographic regions of operation
        - Data types handled (personal, health, financial, etc.)
        - Applicable regulations and their relative importance
        - Whether each framework is mandatory or best practice
        
        You provide precise, actionable recommendations with clear reasoning.
        When a website is available, you research it to get more context.""",
        tools=tools,
        verbose=False,
        allow_delegation=False,
        llm=get_llm_with_fallback(temperature=0.2),
    )


def _build_profiling_task(
    agent: Agent,
    description: str,
    website: Optional[str],
    country: Optional[str],
    frameworks_list: str,
) -> Task:
    """Build the org profiling task."""

    website_instruction = ""
    if website:
        website_instruction = f"""
STEP 1: Research this organization's website: {website}
First, use TavilyExtractorTool with url: "{website}" to extract the actual page content.
Then, use TavilySearchTool with query: "site:{website} about services products company" for additional context.
Extract: company name, industry, products/services, regions served, data types handled, customer base.
This real website content must inform your framework scoring.
"""

    return Task(
        description=f"""Analyze this organization and recommend applicable compliance frameworks.

Organization Description: "{description}"
Country/Region: {country or "Not specified - infer from description"}
Website: {website or "Not provided"}

{website_instruction}

Available Compliance Frameworks:
{frameworks_list}

YOUR TASK:
1. Identify the organization's industry, sector, and business type
2. Determine geographic regions of operation
3. Identify what types of data they handle (personal, health, financial, payment, etc.)
4. Score each framework from 0.0 to 1.0 for relevance
5. Mark frameworks as mandatory (legally required) vs recommended (best practice)
6. Provide a specific reason why each relevant framework applies

SCORING GUIDE:
- 0.9-1.0: Legally required, directly applicable
- 0.7-0.8: Strongly recommended, high applicability
- 0.5-0.6: Moderately applicable, good to have
- 0.3-0.4: Low applicability, nice to have
- Below 0.3: Not applicable (exclude from output)

IMPORTANT: Return ONLY a valid JSON object, no markdown, no explanation:
{{
  "org_type": "Brief org type (e.g., Indian Healthcare SaaS Company)",
  "industries_detected": ["healthcare", "saas", "technology"],
  "regions_detected": ["India", "Global"],
  "analysis_summary": "2-3 sentence summary of compliance landscape for this org",
  "recommended_frameworks": [
    {{
      "id": "HIPAA",
      "relevance_score": 0.95,
      "relevance_reason": "Handles patient health data; HIPAA Privacy and Security Rules mandatory",
      "is_mandatory": true
    }},
    {{
      "id": "ISO27001",
      "relevance_score": 0.80,
      "relevance_reason": "SaaS platform requires ISMS; customers will demand ISO 27001 certification",
      "is_mandatory": false
    }}
  ]
}}

Only include frameworks with relevance_score >= 0.3.
Sort by relevance_score descending.
""",
        expected_output="Valid JSON with org profiling and framework recommendations",
        agent=agent,
    )


def profile_organization(
    description: str,
    website: Optional[str] = None,
    country: Optional[str] = None,
    max_retries: int = 3,
) -> OrgProfileResponse:
    """
    Profile an organization from its description and recommend compliance frameworks.

    Args:
        description: 3-4 word org description (e.g., "Indian healthcare SaaS startup")
        website: Optional org website URL
        country: Optional primary country
        max_retries: Max retry attempts

    Returns:
        OrgProfileResponse with recommended frameworks
    """

    # Build frameworks list for the prompt
    frameworks_list = "\n".join([
        f"- {fid}: {meta['name']} ({meta['region']})"
        for fid, meta in FRAMEWORKS.items()
    ])

    last_error = None
    for attempt in range(max_retries):
        try:
            agent = _build_org_profiling_agent()
            task = _build_profiling_task(agent, description, website, country, frameworks_list)

            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
            )

            result = crew.kickoff()
            result_str = str(result)

            # Extract JSON
            result_str = re.sub(r"```json\s*", "", result_str)
            result_str = re.sub(r"```\s*$", "", result_str)
            result_str = re.sub(r"Thought:.*?(\{)", r"\1", result_str, flags=re.DOTALL)

            json_match = re.search(r"\{[\s\S]*\}", result_str)
            if not json_match:
                raise ValueError("No JSON found in response")

            data = json.loads(json_match.group(0))

            # Build response with full framework metadata
            framework_matches = []
            for rec in data.get("recommended_frameworks", []):
                fw_id = rec.get("id")
                if fw_id not in FRAMEWORKS:
                    continue
                fw_meta = FRAMEWORKS[fw_id]
                framework_matches.append(FrameworkMatch(
                    id=fw_id,
                    name=fw_meta["name"],
                    icon=fw_meta["icon"],
                    color=fw_meta["color"],
                    region=fw_meta["region"],
                    description=fw_meta["description"],
                    relevance_score=rec.get("relevance_score", 0.5),
                    relevance_reason=rec.get("relevance_reason", ""),
                    is_mandatory=rec.get("is_mandatory", False),
                    max_fine=fw_meta["max_fine"],
                    notification_window=fw_meta["notification_window"],
                ))

            # Sort by relevance score
            framework_matches.sort(key=lambda x: x.relevance_score, reverse=True)

            return OrgProfileResponse(
                org_description=description,
                org_type=data.get("org_type", description),
                industries_detected=data.get("industries_detected", []),
                regions_detected=data.get("regions_detected", []),
                recommended_frameworks=framework_matches,
                analysis_summary=data.get("analysis_summary", ""),
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Org profiling attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue

    # Fallback: rule-based profiling
    logger.error(f"All attempts failed, using rule-based fallback: {last_error}")
    return _rule_based_fallback(description, country)


def _rule_based_fallback(description: str, country: Optional[str]) -> OrgProfileResponse:
    """Simple rule-based framework recommendation when AI fails."""
    desc_lower = description.lower()
    matches = []

    for fw_id, fw_meta in FRAMEWORKS.items():
        score = 0.0
        reason = ""
        for trigger in fw_meta.get("triggers", []):
            if trigger in desc_lower:
                score += 0.25
                reason += f"Matches '{trigger}'. "

        if country:
            country_lower = country.lower()
            if "india" in country_lower and fw_id == "DPDP":
                score += 0.4
                reason += "Indian org - DPDP Act 2023 mandatory. "
            if any(c in country_lower for c in ["uk", "germany", "france", "eu"]) and fw_id == "GDPR":
                score += 0.4
                reason += "EU/UK org - GDPR mandatory. "
            if "us" in country_lower or "america" in country_lower:
                if fw_id in ["HIPAA", "SOX", "CCPA", "NIST_CSF", "PCI_DSS"]:
                    score += 0.2
                    reason += "US-based org. "

        if score >= 0.3:
            matches.append(FrameworkMatch(
                id=fw_id,
                name=fw_meta["name"],
                icon=fw_meta["icon"],
                color=fw_meta["color"],
                region=fw_meta["region"],
                description=fw_meta["description"],
                relevance_score=min(score, 1.0),
                relevance_reason=reason.strip() or "Based on org description keywords",
                is_mandatory=score >= 0.65,
                max_fine=fw_meta["max_fine"],
                notification_window=fw_meta["notification_window"],
            ))

    matches.sort(key=lambda x: x.relevance_score, reverse=True)

    return OrgProfileResponse(
        org_description=description,
        org_type=description,
        industries_detected=[],
        regions_detected=[country] if country else [],
        recommended_frameworks=matches[:6],
        analysis_summary=(
            f"Rule-based analysis for '{description}'. "
            "Please verify these recommendations with a compliance expert."
        ),
        timestamp=datetime.now().isoformat(),
    )
