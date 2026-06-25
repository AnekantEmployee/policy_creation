"""
TEST 4 — Procedure Generator Agent (end-to-end CrewAI)
Generates ONE procedure (incident_response for NIST_CSF) and validates output.
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

from agents.procedure_generator import generate_procedures
from models.schemas import ProcedureGenerationResponse

ORG_DESC  = "US fintech startup processing credit card payments"
ORG_NAME  = "TestFintech"
FRAMEWORK = "NIST_CSF"
TYPES     = ["incident_response"]   # one procedure only

print(f"\n{'='*60}")
print(f"  Procedure Agent Test")
print(f"  Framework : {FRAMEWORK}")
print(f"  Procedure : {TYPES[0]}")
print(f"  Org       : {ORG_NAME}")
print(f"{'='*60}\n")

start = time.time()
try:
    result: ProcedureGenerationResponse = generate_procedures(
        org_description=ORG_DESC,
        org_name=ORG_NAME,
        framework=FRAMEWORK,
        procedure_types=TYPES,
        org_context={
            "siem_tool": "Splunk",
            "ticketing_tool": "JIRA",
            "iam_tool": "Okta",
            "incident_email": "security@testfintech.com",
        },
        max_retries=2,
    )
    elapsed = time.time() - start

    print(f"✅  Generation completed in {elapsed:.1f}s")
    print(f"   Procedures returned : {len(result.procedures)}")
    print(f"   Summary             : {result.summary[:100]}")
    print()

    if not result.procedures:
        print("❌  No procedures in response")
        sys.exit(1)

    proc = result.procedures[0]
    print(f"   Procedure ID : {proc.procedure_id}")
    print(f"   Title        : {proc.title}")
    print(f"   Framework    : {proc.framework}")
    print(f"   Frequency    : {proc.frequency}")
    print(f"   Owner        : {proc.owner}")
    print(f"   Steps        : {len(proc.steps)}")
    print(f"   Purpose      : {proc.purpose[:100] if proc.purpose else '(empty)'}…")
    print(f"   Escalation   : {proc.escalation_path[:80] if proc.escalation_path else '(empty)'}")

    # Validate
    errors = []
    if not proc.procedure_id:    errors.append("procedure_id is empty")
    if not proc.title:           errors.append("title is empty")
    if len(proc.steps) < 4:      errors.append(f"too few steps ({len(proc.steps)}), expected ≥8")
    if not proc.purpose:         errors.append("purpose is empty")
    for step in proc.steps:
        if not step.description.strip():
            errors.append(f"step {step.step_number} '{step.title}' has no description")

    if errors:
        print(f"\n⚠️   Validation warnings:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"\n✅  All validation checks passed")

    # Print first 3 steps
    print(f"\n   First {min(3, len(proc.steps))} steps:")
    for step in proc.steps[:3]:
        print(f"     Step {step.step_number}: {step.title}")
        print(f"       Role    : {step.responsible_role}")
        print(f"       Timeline: {step.timeline}")
        print(f"       Tools   : {', '.join(step.tools_required) or '—'}")

    print(f"\n{'='*60}")
    print(f"  RESULT: {'PASS' if not errors else 'PASS with warnings'}")
    print(f"{'='*60}\n")
    sys.exit(0)

except Exception as e:
    elapsed = time.time() - start
    print(f"❌  Generation failed after {elapsed:.1f}s: {e}")
    import traceback
    traceback.print_exc()
    print(f"\n{'='*60}")
    print(f"  RESULT: FAIL")
    print(f"{'='*60}\n")
    sys.exit(1)
