"""
TEST — Cascade Delete Verification (direct DB, no HTTP)
Creates a session with policies and procedures directly in the DB,
deletes it the same way the API does, then confirms all child rows are gone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.models import Organization, Session, Policy, Procedure
from db import crud

print(f"\n{'='*60}")
print(f"  Cascade Delete Test (direct DB)")
print(f"{'='*60}\n")

db = SessionLocal()

try:
    # ── 1. Insert test org + session + policy + procedure ─────────────────────
    print("1. Inserting test org → session → policy + procedure …")

    org = Organization(
        description="__cascade_test__",
        name="Cascade Test Org",
        country="India",
    )
    db.add(org)
    db.flush()

    session = Session(
        org_id=org.id,
        industries_detected=["IT"],
        regions_detected=["India"],
        analysis_summary="Test session",
        recommended_frameworks=[],
        selected_frameworks=[],
    )
    db.add(session)
    db.flush()

    policy = Policy(
        session_id=session.id,
        policy_id="POL-TEST-001",
        framework="ISO27001",
        policy_type="data_protection",
        title="Test Policy",
        version="1.0",
        effective_date="2026-01-01",
        review_date="2027-01-01",
        owner="CISO",
        classification="Internal",
        sections=[],
    )
    db.add(policy)

    procedure = Procedure(
        session_id=session.id,
        procedure_id="PROC-TEST-001",
        framework="ISO27001",
        procedure_type="incident_response",
        title="Test Procedure",
        purpose="Test",
        scope="All",
        frequency="Annually",
        owner="CISO",
        escalation_path="CISO → CEO",
        steps=[],
    )
    db.add(procedure)
    db.commit()

    sid = session.id
    oid = org.id
    print(f"   ✅  Inserted: org_id={oid}, session_id={sid}")

    # ── 2. Confirm rows exist ─────────────────────────────────────────────────
    pol_before  = db.query(Policy).filter(Policy.session_id == sid).count()
    proc_before = db.query(Procedure).filter(Procedure.session_id == sid).count()
    print(f"2. Before delete → policies: {pol_before}, procedures: {proc_before}")
    assert pol_before == 1 and proc_before == 1, "Setup failed"

    # ── 3. Delete exactly as the API does ─────────────────────────────────────
    print("3. Deleting session (API-style: load children, then delete) …")
    target = crud.get_session(db, sid)
    _ = target.policies      # force-load into identity map
    _ = target.procedures
    db.delete(target)
    db.commit()
    print(f"   ✅  db.delete() + commit() called")

    # ── 4. Verify no orphans ──────────────────────────────────────────────────
    print("4. Checking for orphaned rows …")
    session_after  = db.query(Session).filter(Session.id == sid).first()
    pol_after      = db.query(Policy).filter(Policy.session_id == sid).count()
    proc_after     = db.query(Procedure).filter(Procedure.session_id == sid).count()

    print(f"   Session row still exists : {session_after is not None}")
    print(f"   Orphaned policies        : {pol_after}")
    print(f"   Orphaned procedures      : {proc_after}")

    errors = []
    if session_after is not None: errors.append("Session row was NOT deleted")
    if pol_after > 0:             errors.append(f"{pol_after} orphaned policy rows remain")
    if proc_after > 0:            errors.append(f"{proc_after} orphaned procedure rows remain")

    # ── 5. Clean up test org ──────────────────────────────────────────────────
    leftover_org = db.query(Organization).filter(Organization.id == oid).first()
    if leftover_org:
        db.delete(leftover_org)
        db.commit()

finally:
    db.close()

print(f"\n{'='*60}")
if errors:
    for e in errors:
        print(f"  ❌  {e}")
    print(f"  RESULT: FAIL")
    sys.exit(1)
else:
    print(f"  ✅  All child rows deleted cleanly")
    print(f"  RESULT: PASS")
print(f"{'='*60}\n")
sys.exit(0)
