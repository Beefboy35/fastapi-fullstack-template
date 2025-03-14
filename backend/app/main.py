import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute

from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.deps import SessionDep
from app.api.main import api_router
from app.core.config import settings
from loguru import logger

from app.core.db import init_db
from app.initial_data import init_test_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing data")
    init_test_data()
    yield
    logger.info("App has just been stopped")

def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return "default"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

