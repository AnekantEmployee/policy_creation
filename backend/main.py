"""
Compliance Platform — FastAPI Backend
Simplified version for Python 3.14 compatibility
"""

import logging
import os
import sys
import atexit

# ─── Configure logging BEFORE any imports ───────────────────────────────────

# Create console handler with detailed formatting
log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Silence noisy loggers
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info("="*80)
logger.info("🚀 Compliance Intelligence Platform - Starting Up")
logger.info("="*80)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

from config.frameworks import FRAMEWORKS, get_all_frameworks
from config.llm_config import get_llm_with_fallback
from config.dependencies import (
    get_current_user,
    get_request_context,
    require_admin,
    require_write_access,
    require_read_access,
)
from config.auth import create_access_token, create_refresh_token, hash_password, decode_token, verify_password
from models.schemas import SystemStatus
from models.auth_schemas import UserCreate, UserLogin, TokenResponse, PasswordChange, UserResponse
from db.database import init_db, get_db, SessionLocal
from db import crud, auth_crud
from db.models import Session, Organization, User, UserRole
from agents.org_profiler import profile_organization
from agents.policy_generator import generate_policies, POLICY_TYPES as POLICY_TYPE_DEFS
from agents.procedure_generator import generate_procedures, PROCEDURE_TYPES as PROCEDURE_TYPE_DEFS
from export.docx_builder import build_compliance_docx

# ─── App Setup ────────────────────────────────────────────────────────────────

executor = ThreadPoolExecutor(max_workers=4)

# Global flag for graceful shutdown
_is_shutting_down = False

def _graceful_shutdown():
    """Perform graceful shutdown of executor and cleanup."""
    global _is_shutting_down
    _is_shutting_down = True
    logger.info("🛑 Shutting down thread pool executor...")
    try:
        executor.shutdown(wait=False)  # non-blocking so uvicorn can exit cleanly
        logger.info("✓ Thread pool executor shut down")
    except Exception as e:
        logger.warning(f"⚠️  Error during executor shutdown: {e}")

# Register atexit only — let uvicorn own SIGINT/SIGTERM
atexit.register(_graceful_shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    logger.info("🔄 Initializing application...")
    
    # Startup phase
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("✓ Database tables created/verified")
        
        # Create demo user if it doesn't exist
        db = SessionLocal()
        try:
            demo_user = auth_crud.get_user_by_email(db, "demo@example.com")
            if not demo_user:
                logger.info("Creating demo user for testing...")
                auth_crud.create_user(
                    db=db,
                    email="demo@example.com",
                    username="demo",
                    password="Demo1234!",
                    full_name="Demo User",
                    role=UserRole.COMPLIANCE_OFFICER,
                    is_approved=True,   # demo account is pre-approved
                )
                logger.info("✓ Demo user created: demo@example.com / Demo1234!")
            else:
                logger.info("✓ Demo user already exists")

            # Seed admin user
            admin_user = auth_crud.get_user_by_email(db, "admin@complianceiq.com")
            if not admin_user:
                auth_crud.create_user(
                    db=db,
                    email="admin@complianceiq.com",
                    username="admin",
                    password="Admin1234!",
                    full_name="System Administrator",
                    role=UserRole.ADMIN,
                    is_approved=True,
                )
                logger.info("✓ Admin user created: admin@complianceiq.com / Admin1234!")
            else:
                logger.info("✓ Admin user already exists")
        finally:
            db.close()
        
        logger.info("📊 Available frameworks: %s", ", ".join(FRAMEWORKS.keys()))
        logger.info("✓ Server ready for requests")
    except Exception as e:
        logger.error(f"❌ Failed to initialize app: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown phase
    logger.info("🛑 Application shutdown initiated")
    
    # Cancel all remaining tasks
    pending = asyncio.all_tasks()
    for task in pending:
        if not task.done():
            logger.debug(f"Cancelling pending task: {task.get_name()}")
            task.cancel()
    
    # Wait for tasks to complete cancellation (with timeout)
    if pending:
        try:
            await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=5.0)
            logger.info("✓ All pending tasks cancelled")
        except asyncio.TimeoutError:
            logger.warning("⚠️  Timeout waiting for tasks to cancel")
        except Exception as e:
            logger.warning(f"⚠️  Error cancelling tasks: {e}")
    
    # Shutdown executor
    _graceful_shutdown()
    
    logger.info("="*80)
    logger.info("✓ Application shut down gracefully")
    logger.info("="*80)

app = FastAPI(
    title="Compliance Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Middleware for tracking active requests ──────────────────────────────────

@app.middleware("http")
async def track_requests_middleware(request, call_next):
    """Block new non-health requests while shutting down."""
    if _is_shutting_down and request.url.path not in ["/health", "/status"]:
        return Response(
            content='{"error": "Server is shutting down"}',
            status_code=503,
            media_type="application/json"
        )
    return await call_next(request)

# ─── Health Endpoints ─────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Compliance Intelligence Platform API",
        "status": "running",
        "version": "2.0.0"
    }

@app.get("/health", tags=["Health"])
async def health():
    global _is_shutting_down
    return {
        "status": "healthy" if not _is_shutting_down else "shutting_down",
        "shutting_down": _is_shutting_down
    }

@app.post("/shutdown", tags=["Health"])
async def shutdown(current_user: User = Depends(require_admin)):
    """
    Gracefully shutdown the server. Admin only.
    Initiates shutdown sequence and returns immediately.
    """
    global _is_shutting_down
    logger.info(f"📡 Shutdown endpoint triggered by admin: {current_user.username}")
    
    if _is_shutting_down:
        return {
            "status": "already_shutting_down",
            "message": "Server is already shutting down"
        }
    
    _is_shutting_down = True
    
    return {
        "status": "shutdown_initiated",
        "message": "Server shutdown has been initiated. Stop the process to fully shut down.",
    }

@app.get("/status", response_model=SystemStatus, tags=["Health"])
async def status():
    """Get comprehensive system status including shutdown state."""
    logger.debug("Status check requested")
    return SystemStatus(
        status="operational" if not _is_shutting_down else "shutting_down",
        groq_keys=1,
        groq_models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        groq_total_slots=2,
        tavily_available=True,
        supported_frameworks=list(FRAMEWORKS.keys()),
    )

# ─── Authentication Endpoints ─────────────────────────────────────────────────

@app.post("/auth/signup", response_model=dict, tags=["Authentication"], status_code=201)
async def signup(
    user_data: UserCreate,
    db: DBSession = Depends(get_db),
    context: dict = Depends(get_request_context),
):
    """Register a new account. Newly created accounts require admin approval before login."""
    try:
        user = auth_crud.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            is_approved=False,   # always start unapproved
        )
        logger.info(f"✓ New user registered (pending approval): {user.username} ({user.email})")
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "status": "pending_approval",
            "message": "Account created. Please wait for admin approval before logging in.",
        }
    except ValueError as e:
        logger.warning(f"Signup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create account")


@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    credentials: UserLogin,
    db: DBSession = Depends(get_db),
    context: dict = Depends(get_request_context),
):
    """Authenticate user and return JWT tokens. Account must be approved by an admin first."""
    try:
        user = auth_crud.authenticate_user(db, credentials.email, credentials.password)
    except PermissionError as e:
        if str(e) == "pending_approval":
            raise HTTPException(
                status_code=403,
                detail="Your account is pending admin approval. You will be notified once access is granted.",
            )
        raise HTTPException(status_code=403, detail=str(e))

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create tokens (sub must be a string per JWT spec; include role for middleware)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    expires_delta = timedelta(minutes=30)
    expires_at = datetime.utcnow() + expires_delta

    session = auth_crud.create_user_session(
        db=db,
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=context.get("ip_address"),
        user_agent=context.get("user_agent"),
    )
    logger.info(f"✓ User logged in: {user.username} (Session {session.id})")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
        user=UserResponse.model_validate(user),
    )


@app.post("/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh(
    refresh_request: dict,
    db: DBSession = Depends(get_db),
    context: dict = Depends(get_request_context),
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_request: Dict with 'refresh_token' key
        db: Database session
        context: Request context
        
    Returns:
        New TokenResponse with fresh access_token
    """
    refresh_token = refresh_request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    
    try:
        payload = decode_token(refresh_token)
        user_id_str = payload.get("sub")
        
        if not user_id_str or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )
        
        user_id = int(user_id_str)  # Convert string back to int
    except (ValueError, TypeError):
        logger.warning("Invalid user_id in refresh token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Get user and verify session
    user = auth_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    session = auth_crud.get_session_by_refresh_token(db, refresh_token)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found or expired")
    
    # Create new access token (sub must be a string; include role for middleware)
    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    
    # Update session with new tokens
    session.access_token = new_access_token
    db.commit()
    
    expires_delta = timedelta(minutes=30)
    logger.info(f"✓ Token refreshed for user: {user.username}")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token,  # Keep same refresh token
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
        user=UserResponse.model_validate(user),
    )


@app.post("/auth/logout", tags=["Authentication"])
async def logout(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Logout current user (revoke current session).
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    # Revoke all user sessions
    auth_crud.revoke_user_sessions(db, current_user.id)
    logger.info(f"✓ User logged out: {current_user.username}")
    
    return {
        "message": "Logged out successfully",
        "status": "success",
    }


@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        UserResponse with user details
    """
    logger.debug(f"Profile requested for user: {current_user.username}")
    return UserResponse.model_validate(current_user)


@app.post("/auth/change-password", tags=["Authentication"])
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Change password for current user."""
    if not verify_password(password_change.old_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if password_change.new_password != password_change.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    auth_crud.update_user_password(db, current_user.id, password_change.new_password)
    logger.info(f"✓ Password changed for user: {current_user.username}")
    return {"message": "Password changed successfully", "status": "success"}


# ─── Admin — User Approval Endpoints ─────────────────────────────────────────


@app.get("/admin/users/pending", tags=["Admin"])
async def list_pending_users(
    admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """List all users awaiting admin approval."""
    users = auth_crud.get_pending_users(db)
    return {"pending_users": [UserResponse.model_validate(u) for u in users]}


@app.get("/admin/users", tags=["Admin"])
async def list_all_users(
    admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """List all users in the system."""
    users = auth_crud.list_users(db)
    return {"users": [UserResponse.model_validate(u) for u in users]}


@app.post("/admin/users/{user_id}/approve", tags=["Admin"])
async def approve_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """Approve a pending user account so they can log in."""
    try:
        user = auth_crud.approve_user(db, user_id)
        logger.info(f"✓ Admin {admin.username} approved user {user.username}")
        return {"message": f"User {user.username} approved", "user": UserResponse.model_validate(user)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/admin/users/{user_id}/reject", tags=["Admin"])
async def reject_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """Reject and delete a pending user account."""
    try:
        auth_crud.reject_user(db, user_id)
        logger.info(f"✓ Admin {admin.username} rejected user {user_id}")
        return {"message": f"User {user_id} rejected and removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.patch("/admin/users/{user_id}/role", tags=["Admin"])
async def update_user_role(
    user_id: int,
    body: dict,
    admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """Update a user's role."""
    role_str = body.get("role")
    try:
        new_role = UserRole(role_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role_str}")
    user = auth_crud.update_user(db, user_id, role=new_role)
    logger.info(f"✓ Admin {admin.username} set role of {user.username} to {new_role}")
    return {"message": f"Role updated", "user": UserResponse.model_validate(user)}

# ─── Frameworks ───────────────────────────────────────────────────────────────

@app.get("/frameworks", tags=["Frameworks"])
async def list_frameworks():
    logger.info("📋 Frameworks list requested")
    frameworks = get_all_frameworks()
    # Add confidence scores to each framework
    for fw in frameworks:
        if "confidence" not in fw:
            fw["confidence"] = 85  # Default confidence
    return {"frameworks": frameworks}

@app.get("/frameworks/{framework_id}", tags=["Frameworks"])
async def get_framework(framework_id: str):
    if framework_id not in FRAMEWORKS:
        raise HTTPException(status_code=404, detail=f"Framework '{framework_id}' not found")
    return {"id": framework_id, **FRAMEWORKS[framework_id]}

# ─── Policy Types ─────────────────────────────────────────────────────────────

@app.get("/policy-types", tags=["Policy"])
async def list_policy_types():
    return {"policy_types": {k: v["title"] for k, v in POLICY_TYPE_DEFS.items()}}

@app.get("/procedure-types", tags=["Procedure"])
async def list_procedure_types():
    return {"procedure_types": {k: v["title"] for k, v in PROCEDURE_TYPE_DEFS.items()}}

# ─── Organization Profiling (Placeholder) ─────────────────────────────────────

@app.post("/profile", tags=["Organization"])
async def profile_org(
    body: dict,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """
    Profile an organization using AI analysis.
    Requires Compliance Officer or Admin role.
    """
    description = body.get("description", "")
    website = body.get("website", "")
    country = body.get("country", "")
    org_name_input = body.get("name", "")  # user-supplied org name from wizard
    
    if not description:
        logger.warning("❌ Profile request missing organization description")
        raise HTTPException(status_code=400, detail="Organization description required")
    
    logger.info(f"🔍 Profiling organization: {description[:50]}...")
    
    try:
        # Call the org_profiler agent
        result = await asyncio.get_running_loop().run_in_executor(
            executor,
            profile_organization,
            description,
            website,
            country
        )
        logger.info(f"✓ Organization profiled successfully")
        logger.info(f"  - Type: {result.org_type}")
        logger.info(f"  - Industries: {', '.join(result.industries_detected)}")
        logger.info(f"  - Recommended frameworks: {len(result.recommended_frameworks)}")
        
        # Save to database — prefer user-supplied name, fall back to AI description
        org = crud.get_or_create_org(
            db=db,
            description=description,
            name=org_name_input or result.org_description,
            website=website,
            country=country,
            
            org_type=result.org_type,
        )
        session = crud.create_session(
            db=db,
            org_id=org.id,
            industries_detected=result.industries_detected,
            regions_detected=result.regions_detected,
            analysis_summary=result.analysis_summary,
            recommended_frameworks=[f.model_dump() for f in result.recommended_frameworks],
        )
        db.commit()
        logger.info(f"✓ Session saved with ID {session.id}")
        
        # Return with session_id
        response_dict = result.model_dump()
        response_dict["session_id"] = session.id
        return response_dict
    except Exception as e:
        logger.error(f"❌ Profiling failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profiling failed: {str(e)}")

# ─── Policy Generation (Placeholder) ───────────────────────────────────────────

@app.post("/policies/generate", tags=["Policy"])
async def generate_policy(
    body: dict,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """
    Generate compliance policies using AI agents.
    Requires Compliance Officer or Admin role.
    """
    framework = body.get("framework", "iso-27001")
    org_name = body.get("org_name", "Your Organization")
    org_description = body.get("org_description", "")
    policy_types = body.get("policy_types", ["data_protection", "incident_response", "access_control"])
    org_context = body.get("org_context", {})
    session_id_from_request = body.get("session_id")  # link back to profiling session

    if framework not in FRAMEWORKS:
        logger.warning(f"❌ Unknown framework requested: {framework}")
        raise HTTPException(status_code=400, detail=f"Unknown framework: {framework}")
    
    logger.info(f"📝 Generating {len(policy_types)} policies for {org_name}")
    logger.info(f"   Framework: {framework}")
    logger.info(f"   Policy types: {', '.join(policy_types)}")
    
    try:
        # Call the policy generator agent in thread pool
        result = await asyncio.get_running_loop().run_in_executor(
            executor,
            generate_policies,
            org_description,
            org_name,
            framework,
            policy_types,
            org_context
        )
        logger.info(f"✓ Generated {len(result.policies)} policies")
        logger.info(f"   {result.summary}")
        
        # Find or create org + session for storing policies
        org = crud.get_or_create_org(db=db, description=org_description, name=org_name)
        if not org.id:
            db.flush()
        
        # Use session_id from request if provided (links to profiling run),
        # otherwise find latest session for org or create a new one
        if session_id_from_request:
            session = crud.get_session(db, session_id_from_request)
            if not session:
                logger.warning(f"⚠ session_id {session_id_from_request} not found, falling back to latest")
                session = None

        if not session_id_from_request or not session:
            session = db.query(Session).filter(Session.org_id == org.id).order_by(desc(Session.created_at)).first()
        if not session:
            session = crud.create_session(
                db=db,
                org_id=org.id,
                industries_detected=[],
                regions_detected=[],
                analysis_summary="",
                recommended_frameworks=[],
            )
        
        # Save policies
        crud.save_policies(db=db, session_id=session.id, policies_response=result.model_dump())
        db.commit()
        logger.info(f"✓ Saved {len(result.policies)} policies to session {session.id}")
        
        return result
    except Exception as e:
        logger.error(f"❌ Policy generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Policy generation failed: {str(e)}")

# ─── Procedure Generation (Placeholder) ────────────────────────────────────────

@app.post("/procedures/generate", tags=["Procedure"])
async def generate_procedure(
    body: dict,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """
    Generate compliance procedures using AI agents.
    Requires Compliance Officer or Admin role.
    """
    framework = body.get("framework", "iso-27001")
    org_name = body.get("org_name", "Your Organization")
    org_description = body.get("org_description", "")
    procedure_types = body.get("procedure_types", ["incident_response", "data_breach", "access_review"])
    org_context = body.get("org_context", {})
    session_id_from_request = body.get("session_id")  # link back to profiling session

    if framework not in FRAMEWORKS:
        logger.warning(f"❌ Unknown framework requested: {framework}")
        raise HTTPException(status_code=400, detail=f"Unknown framework: {framework}")
    
    logger.info(f"📋 Generating {len(procedure_types)} procedures for {org_name}")
    logger.info(f"   Framework: {framework}")
    logger.info(f"   Procedure types: {', '.join(procedure_types)}")
    
    try:
        # Call the procedure generator agent in thread pool
        result = await asyncio.get_running_loop().run_in_executor(
            executor,
            generate_procedures,
            org_description,
            org_name,
            framework,
            procedure_types,
            org_context
        )
        logger.info(f"✓ Generated {len(result.procedures)} procedures")
        logger.info(f"   {result.summary}")

        # Save procedures to database — link to profiling session if provided
        org = crud.get_or_create_org(db=db, description=org_description, name=org_name)
        if not org.id:
            db.flush()

        session = None
        if session_id_from_request:
            session = crud.get_session(db, session_id_from_request)
            if not session:
                logger.warning(f"⚠ session_id {session_id_from_request} not found for procedures, falling back")

        if not session:
            session = db.query(Session).filter(Session.org_id == org.id).order_by(desc(Session.created_at)).first()
        if not session:
            session = crud.create_session(
                db=db,
                org_id=org.id,
                industries_detected=[],
                regions_detected=[],
                analysis_summary="",
                recommended_frameworks=[],
            )

        crud.save_procedures(db=db, session_id=session.id, procedures_response=result.model_dump())
        db.commit()
        logger.info(f"✓ Saved {len(result.procedures)} procedures to session {session.id}")

        return result
    except Exception as e:
        logger.error(f"❌ Procedure generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Procedure generation failed: {str(e)}")

# ─── History Endpoints ────────────────────────────────────────────────────────

@app.get("/history/org/{org_name}", tags=["History"])
async def get_org_history(
    org_name: str,
    limit: int = 20,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_read_access),
):
    """Return all sessions for a specific org name (case-insensitive match)."""
    try:
        from sqlalchemy import func
        orgs = db.query(Organization).filter(
            func.lower(Organization.name) == org_name.lower()
        ).all()
        if not orgs:
            # fallback: match by description
            orgs = db.query(Organization).filter(
                func.lower(Organization.description).contains(org_name.lower())
            ).all()
        if not orgs:
            return {"sessions": []}

        org_ids = [o.id for o in orgs]
        from db.models import Policy, Procedure
        from sqlalchemy import func

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
            .filter(Session.org_id.in_(org_ids))
            .filter(
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
        return {"sessions": result}
    except Exception as e:
        logger.error(f"❌ Org history retrieval failed: {str(e)}", exc_info=True)
        return {"sessions": []}


@app.get("/history", tags=["History"])
async def get_history(
    limit: int = 50,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_read_access),
):
    """Return all past sessions with org & policy/procedure counts"""
    try:
        history = crud.get_full_history(db, limit=limit)
        logger.info(f"✓ Retrieved {len(history)} sessions from history")
        return {"sessions": history}
    except Exception as e:
        logger.error(f"❌ History retrieval failed: {str(e)}", exc_info=True)
        return {"sessions": []}

@app.get("/history/{session_id}", tags=["History"])
async def get_session_detail(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_read_access),
):
    """Return full detail for one session with all policies and procedures"""
    try:
        session = crud.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        policies = crud.get_policies_for_session(db, session_id)
        procedures = crud.get_procedures_for_session(db, session_id)
        
        return {
            "session_id": session.id,
            "org_id": session.org_id,
            "org_name": session.organization.name or session.organization.description,
            "org_description": session.organization.description,
            "org_type": session.organization.org_type,
            "industries": session.industries_detected or [],
            "regions": session.regions_detected or [],
            "summary": session.analysis_summary,
            "selected_frameworks": session.selected_frameworks or [],
            "created_at": session.created_at.isoformat() if session.created_at else "",
            "policies": [
                {
                    "id": p.id,
                    "policy_id": p.policy_id,
                    "framework": p.framework,
                    "policy_type": p.policy_type,
                    "title": p.title,
                    "version": p.version,
                    "effective_date": p.effective_date,
                    "review_date": p.review_date,
                    "owner": p.owner,
                    "sections": p.sections,
                }
                for p in policies
            ],
            "procedures": [
                {
                    "id": p.id,
                    "procedure_id": p.procedure_id,
                    "framework": p.framework,
                    "procedure_type": p.procedure_type,
                    "title": p.title,
                    "purpose": p.purpose,
                    "scope": p.scope,
                    "frequency": p.frequency,
                    "owner": p.owner,
                    "steps": p.steps,
                }
                for p in procedures
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session detail retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")

@app.patch("/history/{session_id}/frameworks", tags=["History"])
async def update_session_frameworks(
    session_id: int,
    body: dict,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """Update frameworks for a session"""
    try:
        selected = body.get("selected_frameworks", [])
        crud.update_session_frameworks(db, session_id, selected)
        db.commit()
        logger.info(f"✓ Updated session {session_id} frameworks: {selected}")
        return {"session_id": session_id, "selected_frameworks": selected}
    except Exception as e:
        logger.error(f"❌ Framework update failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update frameworks: {str(e)}")

@app.post("/history/{session_id}/regenerate", tags=["History"])
async def regenerate_session(
    session_id: int,
    body: dict,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """
    Regenerate policies and/or procedures for an existing session without
    re-entering org info. Accepts optional policy_types, procedure_types,
    and org_context overrides. Returns the new combined results.
    """
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    org = session.organization
    org_name        = org.name or org.description
    org_description = org.description
    org_context     = body.get("org_context", {})
    framework       = body.get("framework", "")
    policy_types    = body.get("policy_types", [])
    procedure_types = body.get("procedure_types", [])
    frameworks      = body.get("frameworks", session.selected_frameworks or [])

    if framework and framework not in frameworks:
        frameworks = [framework]

    if not frameworks:
        raise HTTPException(status_code=400, detail="No frameworks available for session")

    all_policies: list = []
    all_procedures: list = []

    for fw in frameworks:
        if fw not in FRAMEWORKS:
            continue
        if policy_types:
            try:
                pol = await asyncio.get_running_loop().run_in_executor(
                    executor, generate_policies,
                    org_description, org_name, fw, policy_types, org_context,
                )
                # Stamp IDs with a short timestamp to avoid collisions across runs
                ts = datetime.now().strftime("%m%d%H%M")
                for p in pol.policies:
                    p.policy_id = f"{p.policy_id}-{ts}"
                crud.save_policies(db=db, session_id=session_id, policies_response=pol.model_dump())
                all_policies.extend([p.model_dump() for p in pol.policies])
                logger.info(f"✓ Regenerated {len(pol.policies)} {fw} policies for session {session_id}")
            except Exception as e:
                logger.error(f"Regenerate policy failed for {fw}: {e}")

        if procedure_types:
            try:
                proc = await asyncio.get_running_loop().run_in_executor(
                    executor, generate_procedures,
                    org_description, org_name, fw, procedure_types, org_context,
                )
                ts = datetime.now().strftime("%m%d%H%M")
                for p in proc.procedures:
                    p.procedure_id = f"{p.procedure_id}-{ts}"
                crud.save_procedures(db=db, session_id=session_id, procedures_response=proc.model_dump())
                all_procedures.extend([p.model_dump() for p in proc.procedures])
                logger.info(f"✓ Regenerated {len(proc.procedures)} {fw} procedures for session {session_id}")
            except Exception as e:
                logger.error(f"Regenerate procedure failed for {fw}: {e}")

    db.commit()
    return {
        "session_id": session_id,
        "org_name": org_name,
        "frameworks": frameworks,
        "policies": all_policies,
        "procedures": all_procedures,
        "policy_count": len(all_policies),
        "procedure_count": len(all_procedures),
    }


@app.delete("/history/{session_id}", tags=["History"])
async def delete_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """Delete a session and all associated policies/procedures. Requires Compliance Officer or Admin."""
    try:
        session = crud.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Explicitly load child collections into the session identity map
        # so SQLAlchemy's cascade="all, delete-orphan" fires correctly.
        # This also ensures correct behaviour even if PRAGMA foreign_keys
        # hasn't propagated to the current connection.
        _ = session.policies
        _ = session.procedures

        db.delete(session)
        db.commit()
        logger.info(f"✓ Deleted session {session_id} (+ its policies and procedures)")
        return {"deleted": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

# ─── Export Endpoints ─────────────────────────────────────────────────────────

@app.post("/export/docx", tags=["Export"])
async def export_docx(
    body: dict,
    current_user: User = Depends(require_read_access),
):
    """
    Generate a professional DOCX compliance document package.
    Accepts the same payload shape that StepResults holds in the wizard store:
      { org_name, frameworks, policies[], procedures[] }
    Returns a .docx file download.
    """
    org_name   = body.get("org_name", "Organization")
    frameworks = body.get("frameworks", [])
    policies   = body.get("policies", [])
    procedures = body.get("procedures", [])

    if not policies and not procedures:
        raise HTTPException(status_code=400, detail="No policies or procedures provided")

    try:
        docx_bytes = await asyncio.get_running_loop().run_in_executor(
            executor,
            build_compliance_docx,
            org_name,
            frameworks,
            policies,
            procedures,
        )
        safe_name = org_name.replace(" ", "_").replace("/", "-")[:40]
        filename  = f"{safe_name}_compliance.docx"
        logger.info(f"✓ DOCX export: {filename} ({len(docx_bytes):,} bytes)")
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"❌ DOCX export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/export/session/{session_id}/docx", tags=["Export"])
async def export_session_docx(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_read_access),
):
    """
    Export a previously saved session (from history) as a DOCX file.
    """
    try:
        session = crud.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        policies   = crud.get_policies_for_session(db, session_id)
        procedures = crud.get_procedures_for_session(db, session_id)

        if not policies and not procedures:
            raise HTTPException(status_code=404, detail="No documents found for this session")

        org_name   = session.organization.name or session.organization.description
        frameworks = list({p.framework for p in policies} | {p.framework for p in procedures})

        pol_dicts  = [
            {
                "policy_id":    p.policy_id,
                "framework":    p.framework,
                "policy_type":  p.policy_type,
                "title":        p.title,
                "version":      p.version,
                "effective_date": p.effective_date or "",
                "review_date":  p.review_date or "",
                "applicable_to": p.applicable_to or "",
                "owner":        p.owner or "",
                "classification": p.classification or "Internal",
                "sections":     p.sections or [],
            }
            for p in policies
        ]
        proc_dicts = [
            {
                "procedure_id":  p.procedure_id,
                "framework":     p.framework,
                "procedure_type": p.procedure_type,
                "title":         p.title,
                "version":       "1.0",
                "purpose":       p.purpose or "",
                "scope":         p.scope or "",
                "frequency":     p.frequency or "",
                "owner":         p.owner or "",
                "escalation_path": p.escalation_path or "",
                "steps":         p.steps or [],
            }
            for p in procedures
        ]

        docx_bytes = await asyncio.get_running_loop().run_in_executor(
            executor,
            build_compliance_docx,
            org_name,
            frameworks,
            pol_dicts,
            proc_dicts,
        )
        safe_name = org_name.replace(" ", "_").replace("/", "-")[:40]
        filename  = f"{safe_name}_session_{session_id}.docx"
        logger.info(f"✓ Session DOCX export: {filename} ({len(docx_bytes):,} bytes)")
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session DOCX export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ─── Personalization Questions ────────────────────────────────────────────────

POLICY_TYPES_MAP = {
    "data_protection": "Data Protection & Privacy",
    "incident_response": "Incident Response",
    "access_control": "Access Control & IAM",
    "data_retention": "Data Retention & Disposal",
    "third_party_risk": "Third-Party Risk Management",
    "acceptable_use": "Acceptable Use",
    "business_continuity": "Business Continuity & DR",
    "encryption": "Encryption & Key Management",
}
PROCEDURE_TYPES_MAP = {
    "incident_response": "Security Incident Response",
    "data_breach": "Data Breach Notification",
    "access_review": "Periodic Access Review",
    "vendor_assessment": "Vendor Due Diligence",
    "data_subject_request": "Data Subject Rights Request",
    "risk_assessment": "Risk Assessment",
    "backup_recovery": "Backup & Recovery Testing",
    "security_awareness": "Security Awareness Training",
    "change_management": "Change Management",
    "vulnerability_management": "Vulnerability Management",
}

def _static_questions(frameworks: list) -> list:
    base = [
        {"key": "ciso_contact",         "label": "CISO / Security Officer — name and email",        "hint": "e.g. Jane Smith, ciso@acme.com",          "type": "text",  "category": "contacts"},
        {"key": "dpo_contact",          "label": "Data Protection Officer — name and email",          "hint": "e.g. John Doe, dpo@acme.com",             "type": "text",  "category": "contacts"},
        {"key": "incident_email",       "label": "Security incident reporting email / alias",         "hint": "e.g. security@acme.com",                  "type": "email", "category": "contacts"},
        {"key": "legal_contact",        "label": "Legal / Compliance counsel contact",               "hint": "e.g. General Counsel or external firm",   "type": "text",  "category": "contacts"},
        {"key": "siem_tool",            "label": "SIEM / log monitoring tool used",                  "hint": "e.g. Splunk, Microsoft Sentinel, Datadog", "type": "text",  "category": "tools"},
        {"key": "ticketing_tool",       "label": "Incident & task ticketing system",                 "hint": "e.g. JIRA, ServiceNow, Freshdesk",        "type": "text",  "category": "tools"},
        {"key": "iam_tool",             "label": "Identity & Access Management (IAM) tool",          "hint": "e.g. Okta, Azure AD, Google Workspace",   "type": "text",  "category": "tools"},
        {"key": "backup_tool",          "label": "Backup & recovery tool",                           "hint": "e.g. Veeam, AWS Backup, Acronis",         "type": "text",  "category": "tools"},
        {"key": "data_classification",  "label": "Data classification levels your org uses",         "hint": "e.g. Public, Internal, Confidential",     "type": "text",  "category": "processes"},
        {"key": "retention_period",     "label": "Standard data retention period",                   "hint": "e.g. 3 years customer data, 7 years financial", "type": "text", "category": "processes"},
        {"key": "incident_response_sla","label": "Incident response SLA / notification window",      "hint": "e.g. 72 hours (GDPR), 60 days (HIPAA)",   "type": "text",  "category": "processes"},
        {"key": "employee_count",       "label": "Approximate employee count",                       "hint": "e.g. 50, 200–500, 1000+",                 "type": "text",  "category": "technical"},
    ]
    if "GDPR" in frameworks:
        base.insert(2, {"key": "dpa_registration", "label": "ICO / DPA registration number (if applicable)", "hint": "e.g. ZA123456 (UK ICO)", "type": "text", "category": "legal"})
    if "HIPAA" in frameworks:
        base.insert(2, {"key": "covered_entity_type", "label": "HIPAA covered entity type", "hint": "", "type": "select",
                        "options": ["Healthcare Provider", "Health Plan", "Health Clearinghouse", "Business Associate"], "category": "legal"})
    if "PCI-DSS" in frameworks:
        base.insert(2, {"key": "merchant_level", "label": "PCI-DSS merchant / service provider level", "hint": "e.g. Level 1 (>6M transactions/yr)", "type": "select",
                        "options": ["Level 1", "Level 2", "Level 3", "Level 4", "Service Provider Level 1", "Service Provider Level 2"], "category": "legal"})
    return base


@app.post("/personalization/generate-questions", tags=["Personalization"])
async def generate_personalization_questions(
    body: dict,
    current_user: User = Depends(require_write_access),
):
    """
    Generate AI-tailored personalization questions based on org profile,
    selected frameworks, and chosen policy/procedure types.
    Falls back to a curated static list if the LLM call fails.
    """
    import json as _json
    import re as _re

    org_name        = body.get("org_name", "")
    org_description = body.get("org_description", "")
    org_country     = body.get("org_country", "")
    frameworks      = body.get("frameworks", [])
    policy_types    = body.get("policy_types", [])
    procedure_types = body.get("procedure_types", [])

    policy_names  = [POLICY_TYPES_MAP.get(p, p) for p in policy_types]
    proc_names    = [PROCEDURE_TYPES_MAP.get(p, p) for p in procedure_types]

    system_prompt = (
        "You are a compliance documentation specialist. Generate a SHORT, focused list of personalization questions "
        "to collect specific details needed to make compliance documents completely tailored — replacing generic placeholders.\n\n"
        "Return ONLY a valid JSON array. No explanation, no markdown.\n\n"
        "Each object must have: key (snake_case), label, hint, type (text/email/phone/textarea/select), "
        "category (contacts/tools/roles/processes/legal/technical), and optionally options (array, only for select).\n\n"
        "Rules: 8–14 questions total. Combine related topics. Ask about key contacts, internal tools (SIEM/ticketing/IAM/backup), "
        "registration numbers, timelines, data classification, retention. "
        "Tailor to the specific frameworks and doc types selected. Skip obvious things already collected."
    )
    user_prompt = (
        f"Organization: {org_name}\nDescription: {org_description}\nCountry: {org_country}\n"
        f"Frameworks: {', '.join(frameworks)}\nPolicies: {', '.join(policy_names)}\nProcedures: {', '.join(proc_names)}\n\n"
        "Return ONLY the JSON array."
    )

    try:
        llm = get_llm_with_fallback(temperature=0.3)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        raw = llm.call([{"role": "user", "content": full_prompt}])
        if hasattr(raw, "content"):
            raw = raw.content
        raw = str(raw).strip()
        raw = _re.sub(r"^```json\s*", "", raw)
        raw = _re.sub(r"^```\s*", "", raw)
        raw = _re.sub(r"\s*```$", "", raw)
        questions = _json.loads(raw)
        if isinstance(questions, list) and questions:
            logger.info(f"AI generated {len(questions)} personalization questions")
            return {"questions": questions, "source": "ai"}
    except Exception as e:
        logger.warning(f"AI question generation failed, using static fallback: {e}")

    return {"questions": _static_questions(frameworks), "source": "static"}


# ─── Combined Compliance Suite ────────────────────────────────────────────────

@app.post("/generate-compliance-suite", tags=["Combined"])
async def generate_compliance_suite(
    body: dict,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    """
    Generate policies + procedures for a given org and framework in one call.
    Accepts include_policies / include_procedures booleans to skip either.
    """
    org_description   = body.get("org_description", "")
    org_name          = body.get("org_name", "Your Organization")
    framework         = body.get("framework", "")
    include_policies  = body.get("include_policies",  True)
    include_procedures = body.get("include_procedures", True)
    policy_types      = body.get("policy_types",   ["data_protection", "incident_response", "access_control"])
    procedure_types   = body.get("procedure_types", ["incident_response", "data_breach", "access_review"])
    org_context       = body.get("org_context", {})

    if framework not in FRAMEWORKS:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {framework}")

    result: dict = {"org_name": org_name, "framework": framework}

    if include_policies:
        try:
            pol = await asyncio.get_running_loop().run_in_executor(
                executor, generate_policies,
                org_description, org_name, framework, policy_types, org_context,
            )
            result["policies"] = pol.model_dump()
            logger.info(f"✓ Suite: {len(pol.policies)} policies for {framework}")
        except Exception as e:
            logger.error(f"Suite policy generation failed: {e}")
            result["policies_error"] = str(e)

    if include_procedures:
        try:
            proc = await asyncio.get_running_loop().run_in_executor(
                executor, generate_procedures,
                org_description, org_name, framework, procedure_types, org_context,
            )
            result["procedures"] = proc.model_dump()
            logger.info(f"✓ Suite: {len(proc.procedures)} procedures for {framework}")
        except Exception as e:
            logger.error(f"Suite procedure generation failed: {e}")
            result["procedures_error"] = str(e)

    return result


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info("")
    logger.info("🚀 Starting FastAPI server...")
    logger.info("📍 API docs: http://localhost:8000/docs")
    logger.info("📊 Health check: http://localhost:8000/health")
    logger.info("")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
