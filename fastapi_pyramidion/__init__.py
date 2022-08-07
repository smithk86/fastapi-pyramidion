from typing import Callable

from fastapi import FastAPI
from fastapi.responses import RedirectResponse


def pyramidion(func) -> Callable[..., FastAPI]:
    def wrapper() -> FastAPI:
        app = func()
        if app.root_path:
            # init the fastapi application object
            # disable openapi documentation
            # manually propagate on_start/on_shutdown to child api
            root = FastAPI(
                openapi_url=None,
                on_startup=app.router.on_startup,
                on_shutdown=app.router.on_shutdown,
            )

            # store a reference to the child app in state.pyramidion
            root.state.pyramidion = app

            # mount child app to path
            root.mount(app.root_path, app)

            # add redirect
            @root.get("/")
            def redirect():
                return RedirectResponse(url=app.root_path, status_code=301)

            return root
        else:
            return app

    return wrapper
