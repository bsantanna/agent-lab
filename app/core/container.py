import os

from dependency_injector import containers, providers

from app.application.services.agent import AgentService
from app.core.logging import logger
from app.domain.repositories.agent import AgentRepository
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.database.config import Database


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["app.interface.api.agents.endpoints"]
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

    agent_repository = providers.Factory(
        AgentRepository, session_factory=db.provided.session
    )

    agent_service = providers.Factory(
        AgentService,
        agent_repository=agent_repository,
    )
