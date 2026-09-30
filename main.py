import uuid
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.db import close_pool, init_pool
from errors import ApiError, api_error_handler, postgres_error_handler, unhandled_error_handler, validation_error_handler

from modules import (
    admin,
    ai,
    auth,
    booking,
    chat,
    directory,
    issue,
    marketplace,
    notice,
    notification,
    payment,
    platform_admin,
    poll_event,
    provider,
    resident,
    review,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Trusted Neighbourhood Network API", version="0.1.0", lifespan=lifespan)

_cors_origins = [o.strip() for o in settings.cors_origin.split(",")]
app.add_middleware(
    CORSMiddleware,
    # Auth is Bearer-token based (no cookies), so a wildcard origin in dev is safe
    # without allow_credentials; production should set CORS_ORIGIN to real origins.
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    incoming = request.headers.get("X-Correlation-Id")
    correlation_id = incoming if incoming and len(incoming) < 128 else str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(asyncpg.PostgresError, postgres_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX, tags=["auth"])
app.include_router(resident.router, prefix=API_PREFIX, tags=["resident"])
app.include_router(directory.router, prefix=API_PREFIX, tags=["directory"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["chat"])
app.include_router(notice.router, prefix=API_PREFIX, tags=["notices"])
app.include_router(issue.router, prefix=API_PREFIX, tags=["issues"])
app.include_router(poll_event.router, prefix=API_PREFIX, tags=["polls_events"])
app.include_router(booking.router, prefix=API_PREFIX, tags=["bookings"])
app.include_router(review.router, prefix=API_PREFIX, tags=["reviews"])
app.include_router(payment.router, prefix=API_PREFIX, tags=["payments"])
# provider's literal /providers/me route must be registered before
# marketplace's wildcard /providers/{provider_id}, or FastAPI matches
# "me" against the wildcard segment first and routes it to the wrong handler.
app.include_router(provider.router, prefix=API_PREFIX, tags=["provider_portal"])
app.include_router(marketplace.router, prefix=API_PREFIX, tags=["marketplace"])
app.include_router(admin.router, prefix=API_PREFIX, tags=["admin"])
app.include_router(platform_admin.router, prefix=API_PREFIX, tags=["platform_admin"])
app.include_router(notification.router, prefix=API_PREFIX, tags=["notifications"])
app.include_router(ai.router, prefix=API_PREFIX, tags=["ai_phase2"])


@app.get("/health")
async def health():
    return {"success": True, "data": {"status": "ok"}, "error": None}
