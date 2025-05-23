"""Database module."""

import logging
from contextlib import AbstractContextManager, contextmanager

from sqlalchemy import create_engine, orm
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

    def create_database(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Callable[..., AbstractContextManager[Session]]:
        session: Session = self.session_factory()
        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
