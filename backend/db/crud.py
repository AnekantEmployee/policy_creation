"""
CRUD helpers — all DB reads/writes go through here.
"""

from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

from db.models import Organization, Session, Policy, Procedure


# ─── Organization ─────────────────────────────────────────────────────────────

def get_or_create_org(
    db: DBSession,
    description: str,
    name: Optional[str] = None,
    website: Optional[str] = None,
    country: Optional[str] = None,
    org_type: Optional[str] = None,
) -> Organization:
    org = db.query(Organization).filter(
        Organization.description == description
    ).first()
    if not org:
        org = Organization(
            description=description,
            name=name,
            website=website,
            country=country,
            org_type=org_type,
        )
        db.add(org)
        db.flush()
    else:
        # Update mutable fields if provided
        if name:     org.name     = name
        if website:  org.website  = website
        if country:  org.country  = country
        if org_type: org.org_type = org_type
    return org


# ─── Session ──────────────────────────────────────────────────────────────────

def create_session(
    db: DBSession,
    org_id: int,
    industries_detected: List[str],
    regions_detected: List[str],
    analysis_summary: str,
    recommended_frameworks: list,
    selected_frameworks: Optional[List[str]] = None,
) -> Session:
    session = Session(
        org_id=org_id,
        industries_detected=industries_detected,
        regions_detected=regions_detected,
        analysis_summary=analysis_summary,
        recommended_frameworks=recommended_frameworks,
        selected_frameworks=selected_frameworks or [],
    )
    db.add(session)
    db.flush()
    return session


def update_session_frameworks(db: DBSession, session_id: int, selected: List[str]):
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        session.selected_frameworks = selected
        db.flush()


def get_session(db: DBSession, session_id: int) -> Optional[Session]:
    return db.query(Session).filter(Session.id == session_id).first()


def list_sessions(db: DBSession, limit: int = 50) -> List[Session]:
    return (
        db.query(Session)
        .order_by(desc(Session.created_at))
        .limit(limit)
        .all()
    )


# ─── Policy ───────────────────────────────────────────────────────────────────

def save_policies(db: DBSession, session_id: int, policies_response: dict):
    """Save all policies from a PolicyGenerationResponse dict."""
    saved = []
    for p in policies_response.get("policies", []):
        pol = Policy(
            session_id=session_id,
            policy_id=p.get("policy_id", ""),
            framework=p.get("framework", ""),
            policy_type=p.get("policy_type", ""),
            title=p.get("title", ""),
            version=p.get("version", "1.0"),
            effective_date=p.get("effective_date"),
            review_date=p.get("review_date"),
            applicable_to=p.get("applicable_to"),
            owner=p.get("owner"),
            classification=p.get("classification", "Internal"),
            sections=[
                {"title": s.get("title", ""), "content": s.get("content", ""), "references": s.get("references", [])}
                for s in p.get("sections", [])
            ],
        )
        db.add(pol)
        saved.append(pol)
    db.flush()
    return saved


def get_policies_for_session(db: DBSession, session_id: int) -> List[Policy]:
    return db.query(Policy).filter(Policy.session_id == session_id).all()


# ─── Procedure ────────────────────────────────────────────────────────────────

def save_procedures(db: DBSession, session_id: int, procedures_response: dict):
    """Save all procedures from a ProcedureGenerationResponse dict."""
    saved = []
    for p in procedures_response.get("procedures", []):
        proc = Procedure(
            session_id=session_id,
            procedure_id=p.get("procedure_id", ""),
            framework=p.get("framework", ""),
            procedure_type=p.get("procedure_type", ""),
            title=p.get("title", ""),
            purpose=p.get("purpose"),
            scope=p.get("scope"),
            frequency=p.get("frequency"),
            owner=p.get("owner"),
            escalation_path=p.get("escalation_path"),
            steps=p.get("steps", []),
        )
        db.add(proc)
        saved.append(proc)
    db.flush()
    return saved


def get_procedures_for_session(db: DBSession, session_id: int) -> List[Procedure]:
    return db.query(Procedure).filter(Procedure.session_id == session_id).all()


# ─── History (for frontend) ───────────────────────────────────────────────────

def get_full_history(db: DBSession, limit: int = 50) -> List[dict]:
    """Return sessions with org info + counts for the history view.
    
    Only returns sessions that have at least one generated policy or procedure.
    Sessions created during a wizard run that was interrupted before generation
    are excluded — they would otherwise appear as empty scans.
    """
    from db.models import Policy, Procedure
    from sqlalchemy import func

    # Subqueries: count policies and procedures per session
    policy_counts = (
        db.query(Policy.session_id, func.count(Policy.id).label("policy_count"))
        .group_by(Policy.session_id)
        .subquery()
    )
    procedure_counts = (
        db.query(Procedure.session_id, func.count(Procedure.id).label("procedure_count"))
        .group_by(Procedure.session_id)
        .subquery()
    )

    sessions = (
        db.query(Session)
        .outerjoin(policy_counts,    Session.id == policy_counts.c.session_id)
        .outerjoin(procedure_counts, Session.id == procedure_counts.c.session_id)
        .filter(
            # Keep only sessions that have at least one doc
            (func.coalesce(policy_counts.c.policy_count, 0) +
             func.coalesce(procedure_counts.c.procedure_count, 0)) > 0
        )
        .order_by(desc(Session.created_at))
        .limit(limit)
        .all()
    )

    result = []
    for s in sessions:
        result.append({
            "session_id":   s.id,
            "org_id":       s.org_id,
            "org_name":     s.organization.name or s.organization.description,
            "org_description": s.organization.description,
            "org_country":  s.organization.country,
            "org_website":  s.organization.website,
            "industries":   s.industries_detected or [],
            "regions":      s.regions_detected or [],
            "summary":      s.analysis_summary,
            "selected_frameworks": s.selected_frameworks or [],
            "recommended_frameworks": s.recommended_frameworks or [],
            "policy_count":    len(s.policies),
            "procedure_count": len(s.procedures),
            "created_at":   s.created_at.isoformat() if s.created_at else "",
        })
    return result
