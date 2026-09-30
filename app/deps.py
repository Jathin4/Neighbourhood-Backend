from dataclasses import dataclass

from fastapi import Depends, Header

from app.errors import ApiError
from app.security import decode_access_token


@dataclass
class AuthUser:
    user_id: int
    role: str


def require_auth(authorization: str | None = Header(default=None)) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError.unauthorized()
    token = authorization[len("Bearer "):]
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise ApiError.unauthorized("Invalid or expired access token")
    return AuthUser(user_id=payload["userId"], role=payload["role"])


def optional_auth(authorization: str | None = Header(default=None)) -> AuthUser | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = decode_access_token(authorization[len("Bearer "):])
        return AuthUser(user_id=payload["userId"], role=payload["role"])
    except ValueError:
        return None


def require_role(*roles: str):
    """Coarse API-layer role gate. NOT the authoritative check — every DB function
    re-validates capability + community scope itself (fn__has_capability,
    fn__actor_owns_provider, ...), because client/API-layer role checks alone
    are never sufficient."""

    def dependency(user: AuthUser = Depends(require_auth)) -> AuthUser:
        if user.role not in roles:
            raise ApiError.forbidden()
        return user

    return dependency
