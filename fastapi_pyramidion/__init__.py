from typing import Callable

from fastapi import FastAPI
from fastapi.responses import RedirectResponse


__version__ = "0.1-dev"


def pyramidion(func) -> Callable[..., FastAPI]:
    def wrapper(*args, **kwargs) -> FastAPI:
        # call func to create base app
        base_app = func(*args, **kwargs)

        # only wrap app if app.root_path is defined
        if base_app.root_path:
            # create fastapi application to wrap the given app
            # disable openapi documentation
            # manually propagate startup/shutdown events from base app
            root_app = FastAPI(
                openapi_url=None,
                on_startup=base_app.router.on_startup,
                on_shutdown=base_app.router.on_shutdown,
            )

            # store a reference to the child app in state.pyramidion
            root_app.state.pyramidion = base_app

            # mount child app to path
            root_app.mount(base_app.root_path, base_app)

            # add redirect
            @root_app.get("/")
            def redirect():
                return RedirectResponse(url=base_app.root_path, status_code=301)

            return root_app
        else:
            return base_app

    return wrapper
