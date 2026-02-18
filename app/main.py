import os
import time
import logging
from contextlib import asynccontextmanager

import httpx
from app import models, user, activity, auth
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import schemas

logger = logging.getLogger(__name__)

PROXY_URL = os.environ.get("HTTP_PROXY_URL", "")

def build_proxy_client() -> httpx.Client:
    client_kwargs = {
        "timeout": httpx.Timeout(10.0),
    }
    if PROXY_URL:
        client_kwargs["proxy"] = PROXY_URL
    return httpx.Client(**client_kwargs)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Application starting up...")
    application.state.http_client = build_proxy_client()
    logger.info("HTTP client initialized")
    yield
    logger.info("Application shutting down...")
    application.state.http_client.close()
    logger.info("HTTP client closed")


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, tags=["Users"], prefix="/api/users")
app.include_router(activity.router, tags=["Activity Logs"], prefix="/api/activity")
app.include_router(auth.router, tags=["Auth"], prefix="/api/auth")


@app.get("/api/healthchecker")
def root():
    return {"message": "The API is LIVE!!"}


@app.get(
    "/api/external-health",
    response_model=schemas.ExternalHealthResponse,
    tags=["Health"],
)
def check_external_health(url: str = "https://httpbin.org/get"):
    client: httpx.Client = app.state.http_client
    try:
        start = time.monotonic()
        response = client.get(url)
        elapsed_ms = (time.monotonic() - start) * 1000

        was_redirected = len(response.history) > 0

        return schemas.ExternalHealthResponse(
            url=url,
            status_code=response.status_code,
            redirected=was_redirected,
            response_time_ms=round(elapsed_ms, 2),
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach external URL: {str(e)}",
        ) from e


@app.get(
    "/api/external-health/redirect-test",
    response_model=schemas.ExternalHealthResponse,
    tags=["Health"],
)
def check_redirect_behavior():
    client: httpx.Client = app.state.http_client
    try:
        start = time.monotonic()
        response = client.get("https://httpbin.org/redirect/1")
        elapsed_ms = (time.monotonic() - start) * 1000

        return schemas.ExternalHealthResponse(
            url="https://httpbin.org/redirect/1",
            status_code=response.status_code,
            redirected=len(response.history) > 0,
            response_time_ms=round(elapsed_ms, 2),
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach external URL: {str(e)}",
        ) from e
