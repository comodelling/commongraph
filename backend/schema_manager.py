from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select
from packaging import version

from backend.models.schema import GraphSchema, SchemaMigration
from backend.config import SchemaChangeDetector, CONFIG_HASH, CONFIG_VERSION, _CONFIG


class SchemaManager:
    """Manage schema versions and migrations"""
    
    def __init__(self, session: Session):
        self.session = session
        self.detector = SchemaChangeDetector()
    
    def get_active_schema(self) -> Optional[GraphSchema]:
        """Get the currently active schema"""
        stmt = select(GraphSchema).where(GraphSchema.is_active == True)
        return self.session.exec(stmt).first()
    
    def check_for_schema_changes(self) -> Tuple[bool, List[Dict], List[str]]:
        """Check if the YAML config has changed compared to the active schema"""
        active_schema = self.get_active_schema()
        
        if not active_schema:
            # No schema in DB yet, this is the first time
            return True, [{"type": "initial_schema"}], []
        
        if active_schema.config_hash == CONFIG_HASH:
            return False, [], []  # No changes
        
        # Reconstruct old config
        old_config = {
            "node_types": active_schema.node_types,
            "edge_types": active_schema.edge_types,
            "polls": active_schema.polls,
            "auth": active_schema.auth
        }
        
        changes = self.detector.detect_changes(old_config, _CONFIG)
        warnings = self.detector.validate_against_existing_data(changes, self.session)
        
        return True, changes, warnings
    
    def apply_schema_update(self, username: str, force: bool = False) -> GraphSchema:
        """Apply the current YAML config as a new schema version"""
        has_changes, changes, warnings = self.check_for_schema_changes()
        
        if not has_changes:
            raise ValueError("No schema changes detected")
        
        if warnings and not force:
            raise ValueError(f"Schema changes have warnings: {warnings}. Use force=True to proceed.")
        
        # Get current active schema
        active = self.get_active_schema()
        
        # Deactivate current schema
        if active:
            active.is_active = False
            self.session.add(active)
        
        # Create new schema version
        new_version = self._increment_version(active.version if active else "0.0.0")
        new_schema = GraphSchema(
            version=new_version,
            config_hash=CONFIG_HASH,
            node_types=_CONFIG["node_types"],
            edge_types=_CONFIG["edge_types"],
            polls=_CONFIG["polls"],
            auth=_CONFIG.get("auth", {}),
            is_active=True
        )
        
        self.session.add(new_schema)
        
        # Record migration
        if active:
            migration = SchemaMigration(
                from_version=active.version,
                to_version=new_version,
                migration_type="config_update",
                changes={"changes": changes, "warnings": warnings},
                applied_by=username
            )
            self.session.add(migration)
        
        self.session.commit()
        return new_schema
    
    def get_schema_history(self) -> List[GraphSchema]:
        """Get all schema versions ordered by creation date"""
        stmt = select(GraphSchema).order_by(GraphSchema.created_at.desc())
        return list(self.session.exec(stmt).all())
    
    def get_migrations(self) -> List[SchemaMigration]:
        """Get all migrations ordered by application date"""
        stmt = select(SchemaMigration).order_by(SchemaMigration.applied_at.desc())
        return list(self.session.exec(stmt).all())
    
    def _increment_version(self, current: str) -> str:
        """Increment version number"""
        try:
            v = version.parse(current)
            return f"{v.major}.{v.minor}.{v.micro + 1}"
        except:
            return "1.0.0"
    
    def ensure_schema_in_db(self, username: str = "system") -> GraphSchema:
        """Ensure the current YAML config is stored in the database"""
        active = self.get_active_schema()
        if not active:
            # First time - store the current config
            schema = GraphSchema(
                version=CONFIG_VERSION,
                config_hash=CONFIG_HASH,
                node_types=_CONFIG["node_types"],
                edge_types=_CONFIG["edge_types"],
                polls=_CONFIG["polls"],
                auth=_CONFIG.get("auth", {}),
                is_active=True
            )
            self.session.add(schema)
            self.session.commit()
            return schema
        return active
