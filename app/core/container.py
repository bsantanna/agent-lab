import os

from dependency_injector import containers, providers
from markitdown import MarkItDown

from app.core.logging import logger
from app.domain.repositories.agents import AgentRepository, AgentSettingRepository
from app.domain.repositories.attachments import AttachmentRepository
from app.domain.repositories.integrations import IntegrationRepository
from app.domain.repositories.language_models import (
    LanguageModelRepository,
    LanguageModelSettingRepository,
)
from app.domain.repositories.messages import MessageRepository
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.database.config import Database
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.registry import AgentRegistry
from app.services.agent_types.test_echo.test_echo_agent import TestEchoAgent
from app.services.agent_types.three_phase_react.three_phase_react_agent import (
    ThreePhaseReactAgent,
)
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService
from app.services.messages import MessageService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.interface.api.agents.endpoints",
            "app.interface.api.integrations.endpoints",
            "app.interface.api.language_models.endpoints",
            "app.interface.api.messages.endpoints",
        ]
    )

    if os.getenv("DOCKER"):
        config_file = "config-docker.yml"
    elif os.getenv("TESTING"):
        config_file = "config-test.yml"
    else:
        config_file = "config.yml"

    logger.info(f"Using configuration file: {config_file}")

    config = providers.Configuration(yaml_files=[config_file])

    db = providers.Singleton(Database, db_url=config.db.url)

    redis_client = providers.Singleton(RedisClient, redis_url=config.cache.url)

    markdown = providers.Singleton(MarkItDown)

    attachment_repository = providers.Factory(
        AttachmentRepository, session_factory=db.provided.session
    )

    attachment_service = providers.Factory(
        AttachmentService,
        attachment_repository=attachment_repository,
        markdown=markdown,
    )

    integration_repository = providers.Factory(
        IntegrationRepository,
        session_factory=db.provided.session,
        vault_url=config.vault.url,
        vault_token=config.vault.token,
    )

    integration_service = providers.Factory(
        IntegrationService,
        integration_repository=integration_repository,
    )

    language_model_setting_repository = providers.Factory(
        LanguageModelSettingRepository, session_factory=db.provided.session
    )

    language_model_setting_service = providers.Factory(
        LanguageModelSettingService,
        language_model_setting_repository=language_model_setting_repository,
    )

    language_model_repository = providers.Factory(
        LanguageModelRepository, session_factory=db.provided.session
    )

    language_model_service = providers.Factory(
        LanguageModelService,
        language_model_repository=language_model_repository,
        language_model_setting_service=language_model_setting_service,
        integration_service=integration_service,
    )

    agent_setting_repository = providers.Factory(
        AgentSettingRepository, session_factory=db.provided.session
    )

    agent_setting_service = providers.Factory(
        AgentSettingService,
        agent_setting_repository=agent_setting_repository,
    )

    agent_repository = providers.Factory(
        AgentRepository, session_factory=db.provided.session
    )

    three_phase_react_agent = providers.Factory(
        ThreePhaseReactAgent,
        agent_setting_service=agent_setting_service,
    )

    test_echo_agent = providers.Factory(
        TestEchoAgent,
        agent_setting_service=agent_setting_service,
    )

    agent_registry = providers.Factory(
        AgentRegistry,
        test_echo_agent=test_echo_agent,
        three_phase_react_agent=three_phase_react_agent,
    )

    agent_service = providers.Factory(
        AgentService,
        agent_repository=agent_repository,
        agent_setting_service=agent_setting_service,
        agent_registry=agent_registry,
        language_model_service=language_model_service,
    )

    message_repository = providers.Factory(
        MessageRepository, session_factory=db.provided.session
    )

    message_service = providers.Factory(
        MessageService,
        message_repository=message_repository,
        agent_service=agent_service,
    )
