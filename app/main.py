import logging
import os
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware
from fastapi_mcp import FastApiMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.container import Container
from app.infrastructure.metrics.logging_middleware import LoggingMiddleware
from app.interface.api.agents.endpoints import router as agents_router
from app.interface.api.attachments.endpoints import router as attachments_router
from app.interface.api.integrations.endpoints import router as integrations_router
from app.interface.api.language_models.endpoints import router as language_models_router
from app.interface.api.messages.endpoints import router as messages_router
from app.interface.api.status.endpoints import router as status_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    container = Container()

    application = FastAPI(
        title=os.getenv("SERVICE_NAME", "Agent-Lab"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        dependencies=[],
    )

    setup_dependency_injection(container, application)
    setup_auth(container, application)
    setup_exception_handlers(application)
    setup_middleware(application)
    setup_routers(application)
    setup_mcp(application)

    return application


def setup_auth(container, application):
    async def map_user(userinfo: dict) -> dict:
        user_id = userinfo.get("sub")
        # container.db().create_database(schema_name=user_id)
        return {
            "id": user_id,
            "username": userinfo.get("preferred_username"),
            "email": userinfo.get("email"),
        }
    config = container.config()
    if config["auth"]["enabled"] == "True":
        keycloak_config = KeycloakConfiguration(
            url=config["auth"]["url"],
            realm=config["auth"]["realm"],
            client_id=config["auth"]["client_id"],
            client_secret=config["auth"]["client_secret"],
        )

        setup_keycloak_middleware(
            application,
            keycloak_configuration=keycloak_config,
            user_mapper=map_user,
            exclude_patterns=["/docs", "/openapi.json", "/status/*"],
        )

    else:
        logger.warning("Authentication disabled")


def setup_mcp(application: FastAPI):
    mcp = FastApiMCP(
        application,
        include_operations=["get_agent_list", "get_message_list", "post_message"],
        describe_all_responses=True,
        describe_full_response_schema=True,
    )
    mcp.mount_http()
    mcp.mount_sse()


def setup_routers(application: FastAPI):
    application.include_router(agents_router, prefix="/agents", tags=["agents"])
    application.include_router(
        attachments_router, prefix="/attachments", tags=["attachments"]
    )
    application.include_router(
        integrations_router, prefix="/integrations", tags=["integrations"]
    )
    application.include_router(language_models_router, prefix="/llms", tags=["llms"])
    application.include_router(messages_router, prefix="/messages", tags=["messages"])
    application.include_router(status_router, prefix="/status", tags=["status"])


def setup_exception_handlers(application: FastAPI):
    @application.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        match = re.match(r"^(\d+):", exc.detail)
        if match:
            status_code = int(match.group(1))
            detail = exc.detail[len(match.group(0)) :].strip()
        else:
            status_code = exc.status_code
            detail = exc.detail

        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )


def setup_database(container: Container):
    db = container.db()
    db.create_database()


def setup_tracing(container: Container, application: FastAPI):
    tracer = container.tracer()
    tracer.setup(application)


def setup_dependency_injection(container: Container, application: FastAPI):
    application.container = container
    setup_database(container)
    setup_tracing(container, application)


def setup_middleware(application: FastAPI):
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        LoggingMiddleware,
    )


app = create_app()
