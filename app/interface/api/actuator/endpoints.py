import time
import threading
import psutil
from fastapi import APIRouter

startup_time = time.time()

router = APIRouter()


@router.get(
    "/health",
)
def health():
    """
    Returns the health status of the application.
    """
    return {"msg": "success"}


@router.get(
    "/metrics",
)
def metrics():
    """
    Returns application metrics.
    """
    return {
        "application": {
            "uptime_seconds": time.time() - startup_time,
            "startup_time": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(startup_time)
            ),
        },
        "system": {
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory": {
                "total_mb": psutil.virtual_memory().total / 1024 / 1024,
                "used_mb": psutil.virtual_memory().used / 1024 / 1024,
                "free_mb": psutil.virtual_memory().free / 1024 / 1024,
            },
            "disk": {
                "total_gb": psutil.disk_usage("/").total / 1024 / 1024 / 1024,
                "used_gb": psutil.disk_usage("/").used / 1024 / 1024 / 1024,
                "free_gb": psutil.disk_usage("/").free / 1024 / 1024 / 1024,
            },
        },
        "threads": {"active_count": threading.active_count()},
    }
