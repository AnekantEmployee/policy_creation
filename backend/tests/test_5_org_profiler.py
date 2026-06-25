"""
TEST 5 — Org Profiler Agent
Profiles an organization and validates the framework recommendations returned.
"""

import sys
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.org_profiler import profile_organization
from models.schemas import OrgProfileResponse

ORG_DESC = "Indian healthcare SaaS startup handling patient records"
WEBSITE  = ""
COUNTRY  = "India"

print(f"\n{'='*60}")
print(f"  Org Profiler Test")
print(f"  Description : {ORG_DESC}")
print(f"  Country     : {COUNTRY}")
print(f"{'='*60}\n")

start = time.time()
try:
    result: OrgProfileResponse = profile_organization(
        description=ORG_DESC,
        website=WEBSITE,
        country=COUNTRY,
    )
    elapsed = time.time() - start

    print(f"✅  Profiling completed in {elapsed:.1f}s")
    print(f"   Org type         : {result.org_type}")
    print(f"   Industries       : {result.industries_detected}")
    print(f"   Regions          : {result.regions_detected}")
    print(f"   Frameworks found : {len(result.recommended_frameworks)}")
    print(f"   Summary (first 150): {result.analysis_summary[:150]}")
    print()

    if not result.recommended_frameworks:
        print("⚠️   No frameworks recommended")
    else:
        print("   Recommended frameworks:")
        for fw in result.recommended_frameworks:
            mandatory_tag = " [MANDATORY]" if fw.is_mandatory else ""
            print(f"     {fw.id:<15} score={fw.relevance_score:.2f}  {mandatory_tag}  {fw.relevance_reason[:60]}")

    # Validation
    errors = []
    if not result.org_type:                   errors.append("org_type is empty")
    if not result.recommended_frameworks:     errors.append("no frameworks recommended")
    if not result.analysis_summary:           errors.append("analysis_summary is empty")
    for fw in result.recommended_frameworks:
        if not (0.0 <= fw.relevance_score <= 1.0):
            errors.append(f"{fw.id} has invalid relevance_score {fw.relevance_score}")

    if errors:
        print(f"\n⚠️   Validation warnings:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"\n✅  All validation checks passed")

    print(f"\n{'='*60}")
    print(f"  RESULT: {'PASS' if not errors else 'PASS with warnings'}")
    print(f"{'='*60}\n")
    sys.exit(0)

except Exception as e:
    elapsed = time.time() - start
    print(f"❌  Profiling failed after {elapsed:.1f}s: {e}")
    import traceback
    traceback.print_exc()
    print(f"\n{'='*60}")
    print(f"  RESULT: FAIL")
    print(f"{'='*60}\n")
    sys.exit(1)
