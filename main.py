"""
Compliance Platform — FastAPI Backend
"""

import logging
import os

os.environ["CREWAI_TRACING_ENABLED"] = "false"

logging.getLogger("crewai").setLevel(logging.CRITICAL)
logging.getLogger("langchain").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
os.environ["LITELLM_LOG"] = "ERROR"

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session as DBSession

from backend.config.llm_config import get_rotation_info
from backend.config.frameworks import FRAMEWORKS, get_all_frameworks
from backend.agents.org_profiler import profile_organization
from backend.agents.policy_generator import generate_policies, AVAILABLE_POLICY_TYPES, POLICY_TYPE_DETAILS
from backend.agents.procedure_generator import generate_procedures, AVAILABLE_PROCEDURE_TYPES, PROCEDURE_TYPE_DETAILS
from backend.models.schemas import (
    OrgProfileRequest, OrgProfileResponse,
    PolicyGenerationRequest, PolicyGenerationResponse,
    ProcedureGenerationRequest, ProcedureGenerationResponse,
    SystemStatus,
)
from backend.db.database import init_db, get_db
from backend.db import crud

# ─── App Setup ────────────────────────────────────────────────────────────────

executor = ThreadPoolExecutor(max_workers=4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logging.info("DB tables created / verified.")
    yield
    executor.shutdown(wait=False)


app = FastAPI(
    title="Compliance Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"message": "Compliance Intelligence Platform API", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/status", response_model=SystemStatus, tags=["Health"])
async def status():
    rotation = get_rotation_info()
    return SystemStatus(
        status="operational",
        groq_keys=rotation["groq_keys"],
        groq_models=rotation["groq_models"],
        groq_total_slots=rotation["groq_total_slots"],
        tavily_available=rotation["tavily_available"],
        supported_frameworks=list(FRAMEWORKS.keys()),
    )


# ─── Frameworks ───────────────────────────────────────────────────────────────

@app.get("/frameworks", tags=["Frameworks"])
async def list_frameworks():
    return {"frameworks": get_all_frameworks()}


@app.get("/frameworks/{framework_id}", tags=["Frameworks"])
async def get_framework(framework_id: str):
    if framework_id not in FRAMEWORKS:
        raise HTTPException(status_code=404, detail=f"Framework '{framework_id}' not found")
    return {"id": framework_id, **FRAMEWORKS[framework_id]}


@app.get("/policy-types", tags=["Policy"])
async def list_policy_types():
    return {"policy_types": POLICY_TYPE_DETAILS}


@app.get("/procedure-types", tags=["Procedure"])
async def list_procedure_types():
    return {"procedure_types": PROCEDURE_TYPE_DETAILS}


# ─── Org Profiling ────────────────────────────────────────────────────────────

@app.post("/profile", response_model=OrgProfileResponse, tags=["Organization"])
async def profile_org(request: OrgProfileRequest, db: DBSession = Depends(get_db)):
    try:
        result = await run_in_executor(
            profile_organization,
            request.description,
            request.website,
            request.country,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profiling failed: {str(e)}")

    # ── Persist ──
    try:
        org = crud.get_or_create_org(
            db,
            description=request.description,
            name=request.description,
            website=request.website,
            country=request.country,
            org_type=result.org_type,
        )
        session = crud.create_session(
            db,
            org_id=org.id,
            industries_detected=result.industries_detected,
            regions_detected=result.regions_detected,
            analysis_summary=result.analysis_summary,
            recommended_frameworks=[fw.dict() for fw in result.recommended_frameworks],
        )
        db.commit()
        result.session_id = session.id
    except Exception as e:
        db.rollback()
        logging.warning(f"DB save failed (non-fatal): {e}")

    return result


# ─── Policy Generation ────────────────────────────────────────────────────────

@app.post("/policies/generate", response_model=PolicyGenerationResponse, tags=["Policy"])
async def generate_policy(request: PolicyGenerationRequest, db: DBSession = Depends(get_db)):
    if request.framework not in FRAMEWORKS:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {request.framework}")

    try:
        result = await run_in_executor(
            generate_policies,
            request.org_description,
            request.org_name or "Your Organization",
            request.framework,
            request.policy_types,
            request.org_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy generation failed: {str(e)}")

    # ── Persist ──
    try:
        org = crud.get_or_create_org(db, description=request.org_description, name=request.org_name)
        # Reuse latest session for this org or create a stub
        from backend.db.models import Session as SessionModel
        session = (
            db.query(SessionModel)
            .filter(SessionModel.org_id == org.id)
            .order_by(SessionModel.id.desc())
            .first()
        )
        if not session:
            session = crud.create_session(db, org_id=org.id,
                industries_detected=[], regions_detected=[],
                analysis_summary="", recommended_frameworks=[])

        crud.save_policies(db, session.id, result.dict())
        db.commit()
    except Exception as e:
        db.rollback()
        logging.warning(f"DB save failed (non-fatal): {e}")

    return result


# ─── Procedure Generation ─────────────────────────────────────────────────────

@app.post("/procedures/generate", response_model=ProcedureGenerationResponse, tags=["Procedure"])
async def generate_procedure(request: ProcedureGenerationRequest, db: DBSession = Depends(get_db)):
    if request.framework not in FRAMEWORKS:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {request.framework}")

    try:
        result = await run_in_executor(
            generate_procedures,
            request.org_description,
            request.org_name or "Your Organization",
            request.framework,
            request.procedure_types,
            request.org_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Procedure generation failed: {str(e)}")

    # ── Persist ──
    try:
        org = crud.get_or_create_org(db, description=request.org_description, name=request.org_name)
        from backend.db.models import Session as SessionModel
        session = (
            db.query(SessionModel)
            .filter(SessionModel.org_id == org.id)
            .order_by(SessionModel.id.desc())
            .first()
        )
        if not session:
            session = crud.create_session(db, org_id=org.id,
                industries_detected=[], regions_detected=[],
                analysis_summary="", recommended_frameworks=[])

        crud.save_procedures(db, session.id, result.dict())
        db.commit()
    except Exception as e:
        db.rollback()
        logging.warning(f"DB save failed (non-fatal): {e}")

    return result


# ─── History endpoints (for Streamlit history tab) ────────────────────────────

@app.get("/history", tags=["History"])
async def get_history(limit: int = 50, db: DBSession = Depends(get_db)):
    """Return all past sessions with org info + policy/procedure counts."""
    return {"sessions": crud.get_full_history(db, limit=limit)}


@app.get("/history/{session_id}", tags=["History"])
async def get_session_detail(session_id: int, db: DBSession = Depends(get_db)):
    """Return full detail for one session including all policies and procedures."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    policies   = crud.get_policies_for_session(db, session_id)
    procedures = crud.get_procedures_for_session(db, session_id)

    return {
        "session_id":   session.id,
        "org_name":     session.organization.name or session.organization.description,
        "org_description": session.organization.description,
        "org_country":  session.organization.country,
        "org_website":  session.organization.website,
        "industries":   session.industries_detected,
        "regions":      session.regions_detected,
        "summary":      session.analysis_summary,
        "selected_frameworks":     session.selected_frameworks,
        "recommended_frameworks":  session.recommended_frameworks,
        "created_at":   session.created_at.isoformat() if session.created_at else "",
        "policies": [
            {
                "policy_id": p.policy_id, "framework": p.framework,
                "policy_type": p.policy_type, "title": p.title,
                "version": p.version, "effective_date": p.effective_date,
                "review_date": p.review_date, "applicable_to": p.applicable_to,
                "owner": p.owner, "classification": p.classification,
                "sections": p.sections,
            }
            for p in policies
        ],
        "procedures": [
            {
                "procedure_id": p.procedure_id, "framework": p.framework,
                "procedure_type": p.procedure_type, "title": p.title,
                "purpose": p.purpose, "scope": p.scope,
                "frequency": p.frequency, "owner": p.owner,
                "escalation_path": p.escalation_path, "steps": p.steps,
            }
            for p in procedures
        ],
    }


@app.patch("/history/{session_id}/frameworks", tags=["History"])
async def update_session_frameworks(session_id: int, body: dict, db: DBSession = Depends(get_db)):
    """Update the selected frameworks for a session."""
    selected = body.get("selected_frameworks", [])
    crud.update_session_frameworks(db, session_id, selected)
    db.commit()
    return {"session_id": session_id, "selected_frameworks": selected}


@app.delete("/history/{session_id}", tags=["History"])
async def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    from backend.db.models import Session as SessionModel
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"deleted": session_id}


# ─── Combined ─────────────────────────────────────────────────────────────────

@app.post("/generate-compliance-suite", tags=["Combined"])
async def generate_compliance_suite(
    org_description: str,
    framework: str,
    org_name: str = "Your Organization",
    include_policies: bool = True,
    include_procedures: bool = True,
    db: DBSession = Depends(get_db),
):
    if framework not in FRAMEWORKS:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {framework}")

    result = {"org_name": org_name, "framework": framework, "org_description": org_description}

    if include_policies:
        policies = await run_in_executor(
            generate_policies, org_description, org_name, framework,
            ["data_protection", "incident_response", "access_control"],
        )
        result["policies"] = policies.dict()

    if include_procedures:
        procedures = await run_in_executor(
            generate_procedures, org_description, org_name, framework,
            ["incident_response", "data_breach", "access_review"],
        )
        result["procedures"] = procedures.dict()

    return result


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Compliance Intelligence Platform running at http://localhost:8000\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="warning")
