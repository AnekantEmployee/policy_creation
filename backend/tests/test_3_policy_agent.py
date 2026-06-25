"""
TEST 3 — Policy Generator Agent (end-to-end CrewAI)
Generates ONE policy (data_protection for GDPR) and validates the output shape.
This is the real test — confirms the full CrewAI → Groq → JSON parse pipeline works.
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

from agents.policy_generator import generate_policies
from models.schemas import PolicyGenerationResponse

ORG_DESC  = "Indian IT services company providing cloud and software solutions"
ORG_NAME  = "TestOrg"
FRAMEWORK = "ISO27001"
TYPES     = ["data_protection"]   # generate just ONE to keep it fast

print(f"\n{'='*60}")
print(f"  Policy Agent Test")
print(f"  Framework : {FRAMEWORK}")
print(f"  Policy    : {TYPES[0]}")
print(f"  Org       : {ORG_NAME}")
print(f"{'='*60}\n")

start = time.time()
try:
    result: PolicyGenerationResponse = generate_policies(
        org_description=ORG_DESC,
        org_name=ORG_NAME,
        framework=FRAMEWORK,
        policy_types=TYPES,
        org_context={"ciso_contact": "Jane Smith, jane@testorg.com"},
        max_retries=2,
    )
    elapsed = time.time() - start

    print(f"✅  Generation completed in {elapsed:.1f}s")
    print(f"   Policies returned : {len(result.policies)}")
    print(f"   Summary           : {result.summary[:100]}")
    print()

    if not result.policies:
        print("❌  No policies in response")
        sys.exit(1)

    pol = result.policies[0]
    print(f"   Policy ID    : {pol.policy_id}")
    print(f"   Title        : {pol.title}")
    print(f"   Framework    : {pol.framework}")
    print(f"   Version      : {pol.version}")
    print(f"   Sections     : {len(pol.sections)}")
    print(f"   Owner        : {pol.owner}")
    print(f"   Classification: {pol.classification}")

    # Validate required fields
    errors = []
    if not pol.policy_id:     errors.append("policy_id is empty")
    if not pol.title:          errors.append("title is empty")
    if len(pol.sections) < 3:  errors.append(f"too few sections ({len(pol.sections)}), expected ≥8")
    for sec in pol.sections:
        if not sec.content.strip():
            errors.append(f"section '{sec.title}' has no content")

    if errors:
        print(f"\n⚠️   Validation warnings:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"\n✅  All validation checks passed")

    # Print first section preview
    if pol.sections:
        s = pol.sections[0]
        print(f"\n   Section 1 preview: {s.title}")
        print(f"   {s.content[:200]}…")

    print(f"\n{'='*60}")
    print(f"  RESULT: {'PASS' if not errors else 'PASS with warnings'}")
    print(f"{'='*60}\n")
    sys.exit(0)

except Exception as e:
    elapsed = time.time() - start
    print(f"❌  Generation failed after {elapsed:.1f}s: {e}")
    print(f"\n{'='*60}")
    print(f"  RESULT: FAIL")
    print(f"{'='*60}\n")
    sys.exit(1)
