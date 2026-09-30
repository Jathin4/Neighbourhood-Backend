import asyncpg
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

DB_ERROR_MAP: dict[str, tuple[int, str]] = {
    "FORBIDDEN": (403, "You do not have permission to perform this action"),
    "RESIDENT_NOT_ACTIVE": (403, "Your account is not yet active in this community"),
    "DIRECTORY_DISABLED": (403, "The resident directory is disabled for this community"),
    "OTP_RATE_LIMITED": (429, "Too many OTP requests — please wait before trying again"),
    "OTP_NOT_FOUND": (400, "No pending OTP for this number — request a new one"),
    "OTP_EXPIRED": (400, "This OTP has expired — request a new one"),
    "OTP_ATTEMPTS_EXCEEDED": (429, "Too many incorrect attempts — request a new OTP"),
    "OTP_INVALID": (400, "Incorrect OTP"),
    "INVALID_PHONE": (400, "Invalid phone number"),
    "INVALID_REFRESH_TOKEN": (401, "Session expired — please log in again"),
    "ISSUE_NOT_FOUND": (404, "Issue not found"),
    "BOOKING_NOT_FOUND": (404, "Booking not found"),
    "PROVIDER_NOT_FOUND": (404, "Provider not found"),
    "PROVIDER_NOT_VERIFIED": (409, "This provider is not yet verified"),
    "REVIEW_NOT_FOUND": (404, "Review not found"),
    "REVIEW_ALREADY_EXISTS": (409, "A review already exists for this booking"),
    "BOOKING_NOT_COMPLETED": (409, "You can only review a completed booking"),
    "INVALID_TRANSITION": (409, "That status change is not allowed from the current state"),
    "REOPEN_WINDOW_EXPIRED": (409, "The window to reopen this issue has passed"),
    "REOPEN_LIMIT_REACHED": (409, "This issue has already been reopened the maximum number of times"),
    "ISSUE_NOT_ELIGIBLE_FOR_REOPEN": (409, "Only resolved or closed issues can be reopened"),
    "CATEGORY_NOT_FOUND": (404, "Service category not found"),
    "MEMBERSHIP_REQUEST_NOT_FOUND": (404, "Membership request not found"),
    "TOWER_NOT_FOUND": (404, "Tower not found"),
    "PAYMENT_NOT_FOUND": (404, "Payment not found"),
    "TEMPLATE_NOT_FOUND": (404, "Notification template not found"),
    "CRITICAL_ALERTS_CANNOT_BE_DISABLED": (400, "Critical alerts cannot be disabled"),
    "EVENT_NOT_FOUND": (404, "Event not found"),
    "POLL_NOT_FOUND": (404, "Poll not found"),
    "POLL_CLOSED": (409, "This poll is not currently open for voting"),
    "SINGLE_CHOICE_ONLY": (400, "This poll only allows a single choice"),
    "UNKNOWN_REPORT_TYPE": (400, "Unknown report type"),
    "UNKNOWN_CONTENT_TYPE": (400, "Unknown content type"),
    "USE_REOPEN_ENDPOINT": (400, "Use the reopen endpoint to reopen an issue"),
    "INVALID_ACTION": (400, "Invalid action"),
    "CONVERSATION_NOT_FOUND": (404, "Conversation not found"),
    "PHONE_ALREADY_IN_USE": (409, "This phone number is already registered to another account"),
}

# Friendly messages for native Postgres unique-constraint violations (SQLSTATE 23505) —
# these aren't raised explicitly by a PL/pgSQL function, so DB_ERROR_MAP can't catch them.
UNIQUE_CONSTRAINT_MESSAGES: dict[str, str] = {
    "uq_communities_name_city": "A community with that name already exists in this city",
    "uq_towers_community_name": "A tower with that name already exists in this community",
    "uq_units_tower_name": "A unit with that name already exists in this tower",
    "uq_providers_owner_user_id": "This user already owns a provider profile",
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}

    @staticmethod
    def forbidden(message: str = "You do not have permission to perform this action") -> "ApiError":
        return ApiError("FORBIDDEN", message, 403)

    @staticmethod
    def not_found(message: str = "Resource not found") -> "ApiError":
        return ApiError("NOT_FOUND", message, 404)

    @staticmethod
    def bad_request(message: str, details: dict | None = None) -> "ApiError":
        return ApiError("BAD_REQUEST", message, 400, details)

    @staticmethod
    def unauthorized(message: str = "Authentication required") -> "ApiError":
        return ApiError("UNAUTHORIZED", message, 401)

    @staticmethod
    def from_db_error(err: asyncpg.PostgresError) -> "ApiError":
        if isinstance(err, asyncpg.UniqueViolationError):
            constraint = getattr(err, "constraint_name", None)
            message = UNIQUE_CONSTRAINT_MESSAGES.get(constraint, "This already exists")
            return ApiError("ALREADY_EXISTS", message, 409)
        raw_message = getattr(err, "message", str(err)) or str(err)
        code = raw_message.split("\n")[0].strip()
        known = DB_ERROR_MAP.get(code)
        if known:
            status, message = known
            return ApiError(code, message, status)
        return ApiError("INTERNAL_ERROR", "Something went wrong", 500, {"db_message": raw_message})


def envelope_error(code: str, message: str, details: dict, correlation_id: str) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message, "details": details, "correlation_id": correlation_id},
    }


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "")
    return JSONResponse(status_code=exc.status, content=envelope_error(exc.code, exc.message, exc.details, correlation_id))


async def postgres_error_handler(request: Request, exc: asyncpg.PostgresError) -> JSONResponse:
    api_err = ApiError.from_db_error(exc)
    correlation_id = getattr(request.state, "correlation_id", "")
    if api_err.status >= 500:
        print(f"[{correlation_id}] DB error:", exc)
    return JSONResponse(status_code=api_err.status, content=envelope_error(api_err.code, api_err.message, api_err.details, correlation_id))


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI's default 422 response ({"detail": [...]}) doesn't follow the standard
    # {success, data, error} envelope every other response uses — wrap it so clients
    # can rely on ApiException parsing for every error, not just ones raised via ApiError.
    correlation_id = getattr(request.state, "correlation_id", "")
    first = exc.errors()[0] if exc.errors() else None
    if first:
        field = ".".join(str(p) for p in first["loc"] if p not in ("body", "query", "path"))
        message = f"{field}: {first['msg']}" if field else first["msg"]
    else:
        message = "Invalid request"
    return JSONResponse(
        status_code=422,
        content=envelope_error("VALIDATION_ERROR", message, {"errors": jsonable_encoder(exc.errors())}, correlation_id),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "")
    print(f"[{correlation_id}] Unhandled error:", exc)
    return JSONResponse(status_code=500, content=envelope_error("INTERNAL_ERROR", "Something went wrong", {}, correlation_id))
