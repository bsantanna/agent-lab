import logging
from contextlib import AbstractContextManager, contextmanager
from sqlalchemy import create_engine, orm
from sqlalchemy.sql import text
from sqlalchemy.orm import Session, declarative_base
from typing_extensions import Callable

logger = logging.getLogger(__name__)

Base = declarative_base()


class Database:
    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url)
        self.session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            ),
        )
        # Store the default schema (public) for reference
        self.default_schema = "public"

    def create_database(self, schema_name: str = "public") -> None:
        """Create schema and tables for a tenant if they don't exist."""
        with self.engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            conn.commit()
        # Create tables in the specified schema
        with self.engine.connect() as conn:
            # Temporarily set search_path to the tenant schema
            conn.execute(text(f"SET search_path TO {schema_name}"))
            Base.metadata.create_all(self.engine)
            # Reset search_path to default
            conn.execute(text(f"SET search_path TO {self.default_schema}"))
            conn.commit()

    def set_schema(self, schema_name: str) -> None:
        """Set the schema for the current connection."""
        with self.engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {schema_name}"))
            conn.commit()
        self.create_database(schema_name)

    @contextmanager
    def session(
        self, schema_name: str = "public"
    ) -> Callable[..., AbstractContextManager[Session]]:
        """Create a session with the specified schema."""
        # Set schema for the session
        self.set_schema(schema_name)
        session: Session = self.session_factory()
        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
            # Reset schema to default after session is closed
            self.set_schema(self.default_schema)
