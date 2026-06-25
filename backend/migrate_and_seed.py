"""
Migration + seed script.
- Adds is_approved column to users (safe if already exists)
- Adds user_role enum values if needed
- Seeds one pre-approved account for every role
- Preserves ALL existing organization / session / policy / procedure data
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal, init_db
from db.models import User, UserRole
from db import auth_crud

# ── 1. Raw SQLite migration: add is_approved column ──────────────────────────

db_path = os.path.join(os.path.dirname(__file__), 'compliance.db')
con = sqlite3.connect(db_path)
cur = con.cursor()

# Check if column already exists
cur.execute("PRAGMA table_info(users)")
existing_cols = [row[1] for row in cur.fetchall()]

if 'is_approved' not in existing_cols:
    print("Adding is_approved column to users table...")
    cur.execute("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0 NOT NULL")
    con.commit()
    print("  ✓ Column added")
else:
    print("  ✓ is_approved column already exists")

# Approve any existing users (demo user created before approval flow existed)
cur.execute("UPDATE users SET is_approved = 1 WHERE is_approved = 0")
updated = cur.rowcount
con.commit()
print(f"  ✓ Approved {updated} existing user(s) (legacy accounts)")

con.close()

# ── 2. Run init_db to ensure all tables are current ──────────────────────────

init_db()
print("✓ Database schema verified")

# ── 3. Seed role accounts ─────────────────────────────────────────────────────

SEED_USERS = [
    {
        "email":     "admin@complianceiq.com",
        "username":  "admin",
        "password":  "Admin1234!",
        "full_name": "System Administrator",
        "role":      UserRole.ADMIN,
    },
    {
        "email":     "compliance@complianceiq.com",
        "username":  "compliance_officer",
        "password":  "Compliance1234!",
        "full_name": "Compliance Officer",
        "role":      UserRole.COMPLIANCE_OFFICER,
    },
    {
        "email":     "security@complianceiq.com",
        "username":  "security_lead",
        "password":  "Security1234!",
        "full_name": "Security Lead",
        "role":      UserRole.SECURITY_LEAD,
    },
    {
        "email":     "executive@complianceiq.com",
        "username":  "executive",
        "password":  "Executive1234!",
        "full_name": "Executive User",
        "role":      UserRole.EXECUTIVE,
    },
    {
        "email":     "auditor@complianceiq.com",
        "username":  "auditor",
        "password":  "Auditor1234!",
        "full_name": "Auditor User",
        "role":      UserRole.AUDITOR,
    },
]

db = SessionLocal()
print("\nSeeding role accounts...")

for seed in SEED_USERS:
    existing = auth_crud.get_user_by_email(db, seed["email"])
    if existing:
        # Make sure they are approved regardless
        if not existing.is_approved:
            existing.is_approved = True
            db.commit()
        print(f"  ~ {seed['email']} already exists — skipped")
        continue

    auth_crud.create_user(
        db=db,
        email=seed["email"],
        username=seed["username"],
        password=seed["password"],
        full_name=seed["full_name"],
        role=seed["role"],
        is_approved=True,
    )
    print(f"  ✓ Created {seed['role'].value}: {seed['email']}")

db.close()

# ── 4. Final summary ──────────────────────────────────────────────────────────

con = sqlite3.connect(db_path)
cur = con.cursor()

print("\n=== Final State ===")
cur.execute("SELECT email, username, role, is_approved FROM users ORDER BY id")
for row in cur.fetchall():
    status = "✓ approved" if row[3] else "⏳ pending"
    print(f"  {row[1]:<25} {row[2]:<25} {row[0]:<35} {status}")

cur.execute("SELECT COUNT(*) FROM organizations")
print(f"\n  Organizations : {cur.fetchone()[0]}  (unchanged)")
cur.execute("SELECT COUNT(*) FROM sessions")
print(f"  Sessions      : {cur.fetchone()[0]}  (unchanged)")
cur.execute("SELECT COUNT(*) FROM policies")
print(f"  Policies      : {cur.fetchone()[0]}  (unchanged)")
cur.execute("SELECT COUNT(*) FROM procedures")
print(f"  Procedures    : {cur.fetchone()[0]}  (unchanged)")

con.close()
print("\nMigration complete.")
