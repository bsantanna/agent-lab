from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.interface.api.cache_control import cache_control


def test_cache_control_default():
    app = FastAPI()

    @app.get("/test", dependencies=[cache_control()])
    def endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=86400, s-maxage=86400"


def test_cache_control_custom_max_age():
    app = FastAPI()

    @app.get("/test", dependencies=[cache_control(max_age=3600)])
    def endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=3600, s-maxage=3600"


def test_cache_control_zero():
    app = FastAPI()

    @app.get("/test", dependencies=[cache_control(max_age=0)])
    def endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=0, s-maxage=0"
