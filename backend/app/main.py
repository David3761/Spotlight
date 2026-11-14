"""The FastAPI app: CORS, routers and the contract's error format."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import jobs
from app.api import chat, fixes, places, scans
from app.config import get_settings
from app.db import create_tables
from app.errors import ApiError, handle_api_error


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Creates the database tables and fails scans a previous run left unfinished, before the app starts serving."""
    create_tables()
    jobs.fail_interrupted_scans()
    yield


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
app.include_router(scans.router)
app.include_router(fixes.router)
app.include_router(chat.router)
