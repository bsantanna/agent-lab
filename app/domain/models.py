from sqlalchemy import Boolean, Column, Integer, String

from app.infrastructure.database.config import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return (
            f"<Agent(id={self.id}, "
            f'email="{self.email}", '
            f'hashed_password="{self.hashed_password}", '
            f"is_active={self.is_active})>"
        )


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return (
            f"<User(id={self.id}, "
            f'email="{self.email}", '
            f'hashed_password="{self.hashed_password}", '
            f"is_active={self.is_active})>"
        )
