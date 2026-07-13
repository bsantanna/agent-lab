import logging
import os
import re
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles

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

    mcp_registrars = container.mcp_registrars()
    mcp_server = build_mcp_server(container, mcp_registrars)
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
    setup_mcp_authorize_resource_rewrite(container, application)
    setup_static(container, application)

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
                "/static/",
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
    authorization_server = f"{base_url}/mcp"

    def build_resource_metadata(request: Request) -> dict:
        user_agent = request.headers.get("user-agent") or ""
        resource = base_url if not user_agent else f"{base_url}/mcp"
        return {
            "resource": resource,
            "authorization_servers": [authorization_server],
            "scopes_supported": ["openid", "profile", "email"],
            "bearer_methods_supported": ["header"],
        }

    @application.get("/.well-known/oauth-protected-resource/mcp")
    async def oauth_protected_resource_metadata(request: Request):
        return JSONResponse(build_resource_metadata(request))

    @application.get("/.well-known/oauth-protected-resource/mcp/")
    async def oauth_protected_resource_metadata_slash(request: Request):
        return JSONResponse(build_resource_metadata(request))

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


def setup_mcp_authorize_resource_rewrite(container: Container, application: FastAPI):
    config = container.config()
    if not config["auth"]["enabled"]:
        return

    bare = config["api_base_url"].rstrip("/")
    target = f"{bare}/mcp"

    def is_bare(value: str) -> bool:
        return value.rstrip("/") == bare

    @application.middleware("http")
    async def mcp_authorize_resource_rewrite(request: Request, call_next):
        if request.url.path == "/mcp/authorize":
            items = list(request.query_params.multi_items())
            if any(k == "resource" and is_bare(v) for k, v in items):
                rewritten = [
                    (k, target if (k == "resource" and is_bare(v)) else v)
                    for k, v in items
                ]
                request.scope["query_string"] = urlencode(rewritten).encode("ascii")
        return await call_next(request)


def setup_static(container: Container, application: FastAPI):
    _setup_branding(application)
    _setup_spa_fallback(container, application)


def _setup_spa_fallback(container: Container, application: FastAPI):
    """Serves a static site (e.g. a SPA build) from a configured directory.

    Gated behind the optional ``static.enabled`` config key and a no-op by
    default. The 404→index fallback fires on any HTML-accepting 404 site-wide,
    which is only correct for ``mount_path: "/"`` (the default). A configured
    but missing directory fails fast at boot.
    """
    static_config = container.config().get("static") or {}
    if not static_config.get("enabled", False):
        return

    directory = static_config["directory"]
    index_file = os.path.join(
        directory, static_config.get("index_file", "index.html")
    )

    @application.middleware("http")
    async def spa_fallback(request: Request, call_next):
        response = await call_next(request)
        accept = request.headers.get("accept", "")
        if response.status_code == 404 and "text/html" in accept:
            return FileResponse(index_file)
        return response

    application.mount(
        path=static_config.get("mount_path", "/"),
        app=StaticFiles(directory=directory, html=True),
        name="static",
    )


def _setup_branding(application: FastAPI):
    # Cache-Control is set on the FileResponse directly: FastAPI only merges
    # dependency-set headers (e.g. cache_control()) into non-Response returns.
    @application.get("/static/logo.svg")
    async def logo() -> FileResponse:
        return FileResponse(
            "app/static/logo.svg",
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400, s-maxage=86400"},
        )


app = create_app()
