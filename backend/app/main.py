"""The FastAPI app: CORS, routers and the contract's error format."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import jobs
from app.api import chat, fixes, onboarding, places, scans
from app.config import get_settings
from app.db import create_tables
from app.errors import ApiError, handle_api_error
from app.pipeline.fetch import close_browser


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Creates the tables and fails scans a previous run left unfinished; closes the render browser on shutdown."""
    create_tables()
    jobs.fail_interrupted_scans()
    yield
    await close_browser()


app = FastAPI(title="Marketingadvisor API", lifespan=lifespan)
"""The backend app."""

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, handle_api_error)
app.include_router(places.router)
app.include_router(onboarding.router)
app.include_router(scans.router)
app.include_router(fixes.router)
app.include_router(chat.router)
