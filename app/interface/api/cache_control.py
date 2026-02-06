from typing_extensions import Callable
from fastapi import Depends, Response


def cache_control(max_age: int = 86400) -> Callable:
    """
    Returns a FastAPI dependency that sets Cache-Control headers on the Response.
    Use in endpoints as: cache: None = cache_control(86400)
    """
    def _set_cache_header(response: Response):
        response.headers["Cache-Control"] = f"public, max-age={max_age}, s-maxage={max_age}"
    return Depends(_set_cache_header)
