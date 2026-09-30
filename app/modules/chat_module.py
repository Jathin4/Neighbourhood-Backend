from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db import call_fn, call_fn_one, record_to_dict
from app.deps import AuthUser, require_auth
from app.envelope import ok
from app.pagination import Pagination, pagination_params, paginated_envelope
from app.modules.notification_module import dispatch

router = APIRouter()


class StartConversationBody(BaseModel):
    other_user_id: int


@router.post("/chat/conversations")
async def start_conversation(body: StartConversationBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_get_or_create_conversation", [user.user_id, body.other_user_id]))
    return ok(row, 201)


@router.get("/chat/conversations")
async def list_conversations(user: AuthUser = Depends(require_auth)):
    rows = await call_fn("fn_list_conversations", [user.user_id])
    return ok([record_to_dict(r) for r in rows])


@router.get("/chat/conversations/{conversation_id}/messages")
async def list_messages(conversation_id: int, user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = [record_to_dict(r) for r in await call_fn("fn_list_messages", [user.user_id, conversation_id, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))


class SendMessageBody(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


@router.post("/chat/conversations/{conversation_id}/messages")
async def send_message(conversation_id: int, body: SendMessageBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_send_message", [user.user_id, conversation_id, body.body]))
    await dispatch(row["recipient_id"], "chat_message", {"title": row["sender_name"], "preview": row["body"][:80]}, category="general")
    return ok(row, 201)


@router.post("/chat/conversations/{conversation_id}/read")
async def mark_read(conversation_id: int, user: AuthUser = Depends(require_auth)):
    await call_fn_one("fn_mark_conversation_read", [user.user_id, conversation_id])
    return ok({"read": True})
