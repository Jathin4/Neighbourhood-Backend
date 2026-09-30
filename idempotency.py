from fastapi import Header

from errors import ApiError


def require_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
    if not idempotency_key or not (8 <= len(idempotency_key) <= 200):
        raise ApiError.bad_request("An Idempotency-Key header (8-200 chars) is required for this operation")
    return idempotency_key
