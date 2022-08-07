import httpx
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from asgi_lifespan import LifespanManager

from fastapi_pyramidion import pyramidion


pytestmark = pytest.mark.anyio


async def test_base_app():
    """
    test fastapi app without pyramidion
    """

    def create_app() -> FastAPI:
        app = FastAPI()

        @app.get("/")
        def root():
            return JSONResponse({"detail": {"msg": "hello world!"}})

        return app

    app = create_app()
    assert hasattr(app.state, "pyramidion") is False

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 200, f"payload: {r.text}"
    assert r.json() == {"detail": {"msg": "hello world!"}}


async def test_pyramidion_app():
    """
    test fastapi app with pyramidion
    """

    @pyramidion
    def create_app() -> FastAPI:
        app = FastAPI(root_path="/test")

        @app.get("/")
        def root():
            return JSONResponse({"detail": {"msg": "hello world!"}})

        return app

    app = create_app()
    assert hasattr(app.state, "pyramidion") is True

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 301, f"payload: {r.text}"

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/test/")
    assert r.status_code == 200, f"payload: {r.text}"
    assert r.json() == {"detail": {"msg": "hello world!"}}


async def test_lifespan():
    """
    confirm startup/shutdown events are being properly forwarded to the child app
    """

    @pyramidion
    def create_app() -> FastAPI:
        app = FastAPI(root_path="/test")
        app.state.startup_called = False
        app.state.shutdown_called = False

        @app.get("/")
        def root():
            return JSONResponse({"detail": {"msg": "hello world!"}})

        @app.on_event("startup")
        async def startup():
            app.state.startup_called = True

        @app.on_event("shutdown")
        async def shutdown():
            app.state.shutdown_called = True

        return app

    app = create_app()
    base_app = app.state.pyramidion

    assert base_app.state.startup_called is False
    assert base_app.state.shutdown_called is False

    async with LifespanManager(app):
        assert base_app.state.startup_called is True
        assert base_app.state.shutdown_called is False

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/test/")
        assert r.status_code == 200, f"payload: {r.text}"
        assert r.json() == {"detail": {"msg": "hello world!"}}

    assert base_app.state.startup_called is True
    assert base_app.state.shutdown_called is True
