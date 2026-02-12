import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.infrastructure.metrics.tracer import excluded_paths

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if any(path.startswith(ep) for ep in excluded_paths):
            return await call_next(request)

        # Log incoming request details
        logger.info(f"Incoming request {request.method}: {request.url}")
        logger.debug(f"Request headers: {request.headers}")
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception as error
            logger.error("An error occurred during request processing", exc_info=True)
            raise e

        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Outgoing response {response.status_code} for {request.method}: {request.url} (time: {process_time:.2f} ms)"
        )
        logger.debug(f"Response headers: {response.headers}")
        return response
