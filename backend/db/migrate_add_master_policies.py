"""
Database Migration: Add master_policies table
Supports the new consolidated master policy feature.
"""

import logging
from sqlalchemy import text

from db.database import engine

logger = logging.getLogger(__name__)


def migrate_add_master_policies():
    """Create the master_policies table if it doesn't exist."""
    
    with engine.connect() as connection:
        # Check if master_policies table already exists
        result = connection.execute(
            text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='master_policies'
            """)
        )
        
        if result.fetchone():
            logger.info("✓ master_policies table already exists")
            connection.commit()
            return
        
        # Create master_policies table
        logger.info("Creating master_policies table...")
        connection.execute(text("""
            CREATE TABLE master_policies (
                id              INTEGER PRIMARY KEY,
                session_id      INTEGER NOT NULL,
                master_policy_id VARCHAR(128) NOT NULL UNIQUE,
                title           VARCHAR(512) NOT NULL,
                version         VARCHAR(16) DEFAULT '1.0',
                executive_summary TEXT,
                aligned_frameworks JSON DEFAULT '[]',
                consolidation_notes TEXT,
                domains         JSON DEFAULT '[]',
                compliance_matrix JSON DEFAULT '[]',
                implementation_roadmap JSON DEFAULT '[]',
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        """))
        
        # Create index on session_id for faster lookups
        logger.info("Creating index on master_policies.session_id...")
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_master_policies_session_id
            ON master_policies(session_id)
        """))
        
        # Create index on master_policy_id
        logger.info("Creating index on master_policies.master_policy_id...")
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_master_policies_id
            ON master_policies(master_policy_id)
        """))
        
        connection.commit()
        logger.info("✓ master_policies table created successfully")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        migrate_add_master_policies()
        logger.info("✅ Migration completed successfully")
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}", exc_info=True)
        raise
