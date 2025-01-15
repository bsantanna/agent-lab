import logging
import re

from fastapi import FastAPI, HTTPException, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.container import Container
from app.interface.api.agents.endpoints import router as agents_router
from app.interface.api.integrations.endpoints import router as integrations_router
from app.interface.api.language_models.endpoints import router as language_models_router
from app.interface.api.status.endpoints import router as status_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    application = FastAPI(
        title="Agent-Lab",
        version="0.1.0",
        dependencies=[],
    )

    setup_exception_handlers(application)
    setup_dependency_injection(application)
    setup_middlewares(application)
    setup_routers(application)

    return application


def setup_routers(application: FastAPI):
    application.include_router(agents_router, prefix="/agents", tags=["agents"])
    application.include_router(
        integrations_router, prefix="/integrations", tags=["integrations"]
    )
    application.include_router(language_models_router, prefix="/llms", tags=["llms"])
    application.include_router(status_router, prefix="/status", tags=["status"])


def setup_exception_handlers(application: FastAPI):
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


def setup_dependency_injection(application: FastAPI):
    container = Container()
    setup_database(container)
    application.container = container


def setup_middlewares(application: FastAPI):
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app = create_app()
