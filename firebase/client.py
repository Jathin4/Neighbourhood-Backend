"""The only place in the backend that talks to Firebase directly. Everything
else (the push adapter) calls send_push() — to rotate credentials or swap
providers later, replace service_account.json (or this file) and nothing
else in the codebase needs to change."""
import asyncio
import pathlib

import firebase_admin
from firebase_admin import credentials, messaging

_SERVICE_ACCOUNT_PATH = pathlib.Path(__file__).parent / "service_account.json"
_app: firebase_admin.App | None = None
_app_init_attempted = False


def _get_app() -> firebase_admin.App | None:
    global _app, _app_init_attempted
    if not _app_init_attempted:
        _app_init_attempted = True
        if _SERVICE_ACCOUNT_PATH.exists():
            _app = firebase_admin.initialize_app(credentials.Certificate(str(_SERVICE_ACCOUNT_PATH)))
        else:
            print(f"[firebase] {_SERVICE_ACCOUNT_PATH} not found — push notifications will no-op")
    return _app


async def send_push(fcm_token: str, title: str, body: str) -> bool:
    app = _get_app()
    if app is None:
        return False
    message = messaging.Message(notification=messaging.Notification(title=title, body=body), token=fcm_token)
    try:
        await asyncio.to_thread(messaging.send, message, app=app)
        return True
    except Exception as exc:
        print("[firebase] send failed:", exc)
        return False
