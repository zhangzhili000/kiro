"""
Kiro AI Platform - Migration Runner

This module provides database migration management.
"""
import os
import logging
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ..core.settings import get_settings
from ..core.license_manager import get_license_manager

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Database Migration Runner"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize migration runner
        
        Args:
            db_url: Database URL (optional)
        """
        settings = get_settings()
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(self.db_url)
        self.migrations_dir = os.path.join(os.path.dirname(__file__))
    
    def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migrations
        
        Returns:
            List of migration names
        """
        with self.engine.connect() as conn:
            # Create migrations table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            # Get applied migrations
            result = conn.execute(text("SELECT name FROM schema_migrations ORDER BY id"))
            return [row[0] for row in result]
    
    def mark_migration_applied(self, migration_name: str) -> None:
        """
        Mark a migration as applied
        
        Args:
            migration_name: Name of migration
        """
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO schema_migrations (name) VALUES (:name)"),
                {"name": migration_name}
            )
            conn.commit()
            logger.info(f"Marked migration as applied: {migration_name}")
    
    def run_migration(self, migration_file: str) -> bool:
        """
        Run a single migration
        
        Args:
            migration_file: Path to migration file
            
        Returns:
            True if successful, False otherwise
        """
        migration_name = os.path.basename(migration_file)
        
        try:
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            with self.engine.begin() as conn:
                conn.execute(text(sql))
            
            self.mark_migration_applied(migration_name)
            logger.info(f"Successfully applied migration: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_name}: {e}")
            return False
    
    def run_all_base_migrations(self) -> None:
        """Run all base migrations (always required)"""
        base_migrations = [
            "base_schema.sql",
        ]
        
        applied = self.get_applied_migrations()
        
        for migration in base_migrations:
            if migration in applied:
                logger.info(f"Skipping already applied migration: {migration}")
                continue
            
            migration_path = os.path.join(self.migrations_dir, migration)
            if os.path.exists(migration_path):
                self.run_migration(migration_path)
    
    def run_commercial_migrations(self) -> None:
        """Run commercial migrations based on license"""
        license_manager = get_license_manager()
        
        if not license_manager.is_license_valid():
            logger.info("No valid license, skipping commercial migrations")
            return
        
        # Define migrations and their required features
        migration_features = {
            "001_add_multi_tenant_columns.sql": ["multi_tenant"],
            "002_add_cross_org_sharing.sql": ["cross_org_sharing"],
            "003_add_audit_logging.sql": ["audit_logging"],
            "004_add_sso.sql": ["sso"],
        }
        
        applied = self.get_applied_migrations()
        enabled_features = license_manager.get_enabled_features()
        
        for migration, features in migration_features.items():
            # Check if migration is already applied
            if migration in applied:
                logger.info(f"Skipping already applied migration: {migration}")
                continue
            
            # Check if required features are enabled
            if not any(f in enabled_features for f in features) and "all" not in enabled_features:
                logger.info(f"Skipping migration {migration}: required features not enabled")
                continue
            
            migration_path = os.path.join(self.migrations_dir, migration)
            if os.path.exists(migration_path):
                self.run_migration(migration_path)
    
    def run_all(self) -> None:
        """Run all migrations"""
        logger.info("Starting database migrations...")
        
        # Run base migrations first
        self.run_all_base_migrations()
        
        # Run commercial migrations
        self.run_commercial_migrations()
        
        logger.info("Database migrations completed")


def run_migrations():
    """Run all migrations (main entry point)"""
    logging.basicConfig(level=logging.INFO)
    
    runner = MigrationRunner()
    runner.run_all()


if __name__ == "__main__":
    run_migrations()
