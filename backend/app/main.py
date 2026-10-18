from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import Settings, get_settings
from app.database import Database
from app.middleware.error_handler import ErrorEnvelopeMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    database = Database(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database = database
        await database.ping()
        try:
            yield
        finally:
            await database.dispose()

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.state.database = database
    app.add_middleware(ErrorEnvelopeMiddleware)
    app.include_router(health_router)
    return app
