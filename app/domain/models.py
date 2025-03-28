from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.sql import Base

message_role = Enum("assistant", "human", name="message_role")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    created_at = Column(TIMESTAMP)
    is_active = Column(Boolean)
    agent_name = Column(String)
    agent_type = Column(String)
    agent_summary = Column(Text)
    language_model_id = Column(String, ForeignKey("language_models.id"))

    language_model = relationship("LanguageModel", back_populates="agents")
    settings = relationship("AgentSetting", back_populates="agent")
    messages = relationship("Message", back_populates="agent")


class AgentSetting(Base):
    __tablename__ = "agent_settings"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    setting_key = Column(String)
    setting_value = Column(Text)

    agent = relationship("Agent", back_populates="settings")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String, primary_key=True)
    created_at = Column(TIMESTAMP)
    is_active = Column(Boolean)
    file_name = Column(String)
    raw_content = Column(LargeBinary)
    parsed_content = Column(Text)
    embeddings_collection = Column(String)

    messages = relationship("Message", back_populates="attachment")


class LanguageModel(Base):
    __tablename__ = "language_models"

    id = Column(String, primary_key=True)
    created_at = Column(TIMESTAMP)
    is_active = Column(Boolean)
    language_model_tag = Column(String)
    integration_id = Column(String, ForeignKey("integrations.id"))

    agents = relationship("Agent", back_populates="language_model")
    integration = relationship("Integration", back_populates="language_models")
    settings = relationship("LanguageModelSetting", back_populates="language_model")


class LanguageModelSetting(Base):
    __tablename__ = "language_model_settings"

    id = Column(String, primary_key=True)
    language_model_id = Column(String, ForeignKey("language_models.id"))
    setting_key = Column(String)
    setting_value = Column(String)

    language_model = relationship("LanguageModel", back_populates="settings")


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(String, primary_key=True)
    created_at = Column(TIMESTAMP)
    is_active = Column(Boolean)
    integration_type = Column(String)

    language_models = relationship("LanguageModel", back_populates="integration")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    created_at = Column(TIMESTAMP)
    is_active = Column(Boolean)
    agent_id = Column(String, ForeignKey("agents.id"))
    message_role = Column(message_role)
    message_content = Column(Text)
    attachment_id = Column(String, ForeignKey("attachments.id"))
    replies_to = Column(String)

    agent = relationship("Agent", back_populates="messages")
    attachment = relationship("Attachment", back_populates="messages")
