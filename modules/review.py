from fastapi import APIRouter, Depends

from database.db import call_fn_one, record_to_dict
from deps import AuthUser, require_auth, require_role
from envelope import ok
from models.review_model import FlagBody, ResponseBody, SubmitReviewBody

router = APIRouter()


@router.post("/bookings/{booking_id}/review")
async def submit_review(booking_id: int, body: SubmitReviewBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_submit_review", [user.user_id, booking_id, body.rating, body.text, body.photo_url]))
    return ok(row, 201)


@router.post("/reviews/{review_id}/response")
async def add_response(review_id: int, body: ResponseBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_add_provider_response", [user.user_id, review_id, body.response]))
    return ok(row)


@router.post("/reviews/{review_id}/flag")
async def flag_review(review_id: int, body: FlagBody, user: AuthUser = Depends(require_role("community_admin", "platform_admin"))):
    row = record_to_dict(await call_fn_one("fn_flag_review", [user.user_id, review_id, body.reason]))
    return ok(row)
