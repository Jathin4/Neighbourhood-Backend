from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from app.deps import AuthUser, require_auth
from app.envelope import ok
from app.pagination import Pagination, pagination_params, paginated_envelope

router = APIRouter()


class PollOption(BaseModel):
    id: str
    label: str


class CreatePollBody(BaseModel):
    community_id: int
    question: str
    options: list[PollOption]
    type: str = "single"
    audience_type: str = "all"
    audience_ref: dict = {}
    is_anonymous: bool = False
    end_at: datetime


@router.post("/polls")
async def create_poll(body: CreatePollBody, user: AuthUser = Depends(require_auth)):
    # fn_create_poll re-validates via fn__has_capability('can_create_poll')
    row = record_to_dict(await call_fn_one("fn_create_poll", [
        user.user_id, body.community_id, body.question, [o.model_dump() for o in body.options], body.type,
        body.audience_type, body.audience_ref, body.is_anonymous, body.end_at,
    ]))
    return ok(row, 201)


@router.get("/polls")
async def list_polls(user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = [record_to_dict(r) for r in await call_fn("fn_list_polls_for_resident", [user.user_id, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))


@router.get("/polls/{poll_id}/results")
async def poll_results(poll_id: int):
    return ok(await call_fn_jsonb("fn_get_poll_results", [poll_id]))


class VoteBody(BaseModel):
    option_ids: list[str]


@router.post("/polls/{poll_id}/vote")
async def vote(poll_id: int, body: VoteBody, user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_cast_poll_vote", [user.user_id, poll_id, body.option_ids]))


class CreateEventBody(BaseModel):
    community_id: int
    title: str
    date_time: datetime
    location: str | None = None
    capacity: int | None = None
    description: str | None = None


@router.post("/events")
async def create_event(body: CreateEventBody, user: AuthUser = Depends(require_auth)):
    # fn_create_event re-validates via fn__has_capability('can_create_event')
    row = record_to_dict(await call_fn_one("fn_create_event", [
        user.user_id, body.community_id, body.title, body.date_time, body.location, body.capacity, body.description,
    ]))
    return ok(row, 201)


@router.get("/events")
async def list_events(user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = [record_to_dict(r) for r in await call_fn("fn_list_events_for_resident", [user.user_id, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))


class RsvpBody(BaseModel):
    status: str  # Going | NotGoing


@router.post("/events/{event_id}/rsvp")
async def rsvp(event_id: int, body: RsvpBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_rsvp_event", [user.user_id, event_id, body.status]))
    return ok(row)
