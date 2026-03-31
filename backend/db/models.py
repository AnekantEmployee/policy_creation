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
    Text, DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from backend.db.database import Base


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
    created_at           = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="sessions")
    policies     = relationship("Policy",    back_populates="session", cascade="all, delete-orphan")
    procedures   = relationship("Procedure", back_populates="session", cascade="all, delete-orphan")


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
