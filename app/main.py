import logging
import os
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.container import Container
from app.interface.mcp.server import build_mcp_server
from app.infrastructure.auth.user import map_user
from app.infrastructure.metrics.logging_middleware import LoggingMiddleware
from app.interface.api.agents.endpoints import router as agents_router
from app.interface.api.attachments.endpoints import router as attachments_router
from app.interface.api.auth.endpoints import router as auth_router
from app.interface.api.integrations.endpoints import router as integrations_router
from app.interface.api.language_models.endpoints import router as language_models_router
from app.interface.api.messages.endpoints import router as messages_router
from app.interface.api.status.endpoints import router as status_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    container = Container()

    mcp_server = build_mcp_server(container)
    mcp_app = mcp_server.http_app(path="/", stateless_http=True)

    application = FastAPI(
        title=os.getenv("SERVICE_NAME", "Agent-Lab"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        dependencies=[],
        lifespan=mcp_app.lifespan,
    )
    application.container = container

    setup_tracing(container, application)
    setup_auth(container, application)
    setup_routers(container, application)
    application.mount("/mcp", mcp_app)
    setup_resource_metadata(container, application)
    setup_exception_handlers(application)
    setup_middleware(application)
    setup_mcp_slash_rewrite(application)

    return application


def setup_auth(container, application):
    config = container.config()
    if config["auth"]["enabled"]:
        keycloak_config = KeycloakConfiguration(
            url=config["auth"]["url"],
            realm=config["auth"]["realm"],
            client_id=config["auth"]["client_id"],
            client_secret=config["auth"]["client_secret"],
        )

        setup_keycloak_middleware(
            application,
            keycloak_configuration=keycloak_config,
            exclude_patterns=[
                "/auth/login(/|$)",
                "/auth/renew(/|$)",
                "/auth/exchange(/|$)",
                "/openapi.json(/|$)",
                "/status/",
                ".*well-known/",
                "/mcp(/.*)?$",
            ],
            user_mapper=map_user,
        )

    else:
        logger.warning("Authentication disabled")


def setup_resource_metadata(container: Container, application: FastAPI):
    config = container.config()
    if not config["auth"]["enabled"]:
        return

    base_url = config["api_base_url"]
    resource_url = f"{base_url}/mcp"
    authorization_server = f"{base_url}/mcp"

    resource_metadata = {
        "resource": resource_url,
        "authorization_servers": [authorization_server],
        "scopes_supported": ["openid", "profile", "email"],
        "bearer_methods_supported": ["header"],
    }

    @application.get("/.well-known/oauth-protected-resource/mcp")
    async def oauth_protected_resource_metadata():
        return JSONResponse(resource_metadata)

    @application.get("/.well-known/oauth-protected-resource/mcp/")
    async def oauth_protected_resource_metadata_slash():
        return JSONResponse(resource_metadata)

    auth_server_metadata = {
        "issuer": authorization_server,
        "authorization_endpoint": f"{authorization_server}/authorize",
        "token_endpoint": f"{authorization_server}/token",
        "registration_endpoint": f"{authorization_server}/register",
        "scopes_supported": ["openid", "profile", "email"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
        ],
        "code_challenge_methods_supported": ["S256"],
    }

    @application.get("/.well-known/oauth-authorization-server/mcp")
    async def oauth_authorization_server_metadata():
        return JSONResponse(auth_server_metadata)

    @application.get("/.well-known/oauth-authorization-server/mcp/")
    async def oauth_authorization_server_metadata_slash():
        return JSONResponse(auth_server_metadata)


def setup_routers(container: Container, application: FastAPI):
    config = container.config()
    if config["auth"]["enabled"]:
        application.include_router(auth_router, prefix="/auth", tags=["auth"])

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


def setup_tracing(container: Container, application: FastAPI):
    tracer = container.tracer()
    tracer.setup(application)


def setup_middleware(application: FastAPI):
    application.add_middleware(
        LoggingMiddleware,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_mcp_slash_rewrite(application: FastAPI):
    @application.middleware("http")
    async def mcp_slash_rewrite(request: Request, call_next):
        if request.url.path == "/mcp":
            scope = request.scope
            scope["path"] = "/mcp/"
            scope["raw_path"] = b"/mcp/"
        return await call_next(request)


app = create_app()
