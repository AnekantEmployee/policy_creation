"""
ORM Models — SQLAlchemy table definitions.

Tables
------
organizations   — one row per unique org description
sessions        — one row per profiling run (links org → frameworks)
policies        — generated policy documents (linked to session)
procedures      — generated procedure documents (linked to session)
"""

import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    Text, DateTime, ForeignKey, JSON, Enum,
)
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class UserRole(str, enum.Enum):
    """User roles for the compliance platform"""
    ADMIN = "admin"                      # Full system access
    COMPLIANCE_OFFICER = "compliance_officer"  # Can create/manage policies and procedures
    SECURITY_LEAD = "security_lead"      # Can view and approve policies
    EXECUTIVE = "executive"               # Read-only access to reports and dashboards
    AUDITOR = "auditor"                  # Read-only access to history and generated docs


class User(Base):
    """User accounts for authentication"""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(256), unique=True, nullable=False, index=True)
    username        = Column(String(128), unique=True, nullable=False, index=True)
    password_hash   = Column(String(256), nullable=False)
    full_name       = Column(String(256), nullable=True)
    role            = Column(Enum(UserRole), default=UserRole.COMPLIANCE_OFFICER, nullable=False)
    is_active       = Column(Boolean, default=True)
    is_verified     = Column(Boolean, default=False)
    is_approved     = Column(Boolean, default=False)   # must be approved by admin before login
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login      = Column(DateTime, nullable=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """Track user login sessions"""
    __tablename__ = "user_sessions"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token    = Column(String(512), nullable=False, unique=True, index=True)
    refresh_token   = Column(String(512), nullable=True, unique=True, index=True)
    expires_at      = Column(DateTime, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    ip_address      = Column(String(45), nullable=True)
    user_agent      = Column(String(512), nullable=True)
    is_active       = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")


class Organization(Base):
    __tablename__ = "organizations"

    id          = Column(Integer, primary_key=True, index=True)
    description = Column(String(256), nullable=False)
    name        = Column(String(256), nullable=True)
    website     = Column(String(512), nullable=True)
    country     = Column(String(128), nullable=True)
    org_type    = Column(String(256), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="organization", cascade="all, delete-orphan")


class Session(Base):
    """One profiling run = one session. Stores the full AI profile result."""
    __tablename__ = "sessions"

    id                   = Column(Integer, primary_key=True, index=True)
    org_id               = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    industries_detected  = Column(JSON, default=list)
    regions_detected     = Column(JSON, default=list)
    analysis_summary     = Column(Text, nullable=True)
    selected_frameworks  = Column(JSON, default=list)   # list of framework IDs user picked
    recommended_frameworks = Column(JSON, default=list) # full AI recommendation payload
    personalization_data = Column(JSON, default=dict)   # extracted org context (CISO, DPO, tools, etc.)
    created_at           = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="sessions")
    policies     = relationship("Policy",    back_populates="session", cascade="all, delete-orphan")
    procedures   = relationship("Procedure", back_populates="session", cascade="all, delete-orphan")
    master_policies = relationship("MasterPolicy", back_populates="session", cascade="all, delete-orphan")


class Policy(Base):
    __tablename__ = "policies"

    id             = Column(Integer, primary_key=True, index=True)
    session_id     = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    policy_id      = Column(String(128), nullable=False)   # e.g. POL-GDPR-DATA-001
    framework      = Column(String(64),  nullable=False)
    policy_type    = Column(String(128), nullable=False)
    title          = Column(String(512), nullable=False)
    version        = Column(String(16),  default="1.0")
    effective_date = Column(String(32),  nullable=True)
    review_date    = Column(String(32),  nullable=True)
    applicable_to  = Column(Text,        nullable=True)
    owner          = Column(String(256), nullable=True)
    classification = Column(String(64),  default="Internal")
    sections       = Column(JSON,        default=list)   # list of {title, content, references}
    created_at     = Column(DateTime,    default=datetime.utcnow)

    session = relationship("Session", back_populates="policies")


class Procedure(Base):
    __tablename__ = "procedures"

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    procedure_id    = Column(String(128), nullable=False)
    framework       = Column(String(64),  nullable=False)
    procedure_type  = Column(String(128), nullable=False)
    title           = Column(String(512), nullable=False)
    purpose         = Column(Text,        nullable=True)
    scope           = Column(Text,        nullable=True)
    frequency       = Column(String(128), nullable=True)
    owner           = Column(String(256), nullable=True)
    escalation_path = Column(Text,        nullable=True)
    steps           = Column(JSON,        default=list)  # list of step dicts
    created_at      = Column(DateTime,    default=datetime.utcnow)

    session = relationship("Session", back_populates="procedures")


class MasterPolicy(Base):
    """Unified, consolidated master policy aligned to all selected frameworks"""
    __tablename__ = "master_policies"

    id                      = Column(Integer, primary_key=True, index=True)
    session_id              = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    master_policy_id        = Column(String(128), nullable=False, unique=True, index=True)
    title                   = Column(String(512), nullable=False)
    version                 = Column(String(16), default="1.0")
    executive_summary       = Column(Text, nullable=True)
    aligned_frameworks      = Column(JSON, default=list)  # list of framework IDs
    consolidation_notes     = Column(Text, nullable=True)
    domains                 = Column(JSON, default=list)  # list of domain objects with requirements
    compliance_matrix       = Column(JSON, default=list)  # framework vs control matrix
    implementation_roadmap  = Column(JSON, default=list)  # phased rollout plan
    created_at              = Column(DateTime, default=datetime.utcnow)
    updated_at              = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session", back_populates="master_policies")
