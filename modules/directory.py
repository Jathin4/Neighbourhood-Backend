from fastapi import APIRouter, Depends, Query

from database.db import call_fn, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from pagination import Pagination, pagination_params, paginated_envelope

router = APIRouter()


@router.get("/directory")
async def search_directory(
    query: str | None = Query(default=None),
    tower: int | None = Query(default=None),
    user: AuthUser = Depends(require_auth),
    pagination: Pagination = Depends(pagination_params),
):
    rows = [record_to_dict(r) for r in await call_fn("fn_search_directory", [user.user_id, query, tower, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))
