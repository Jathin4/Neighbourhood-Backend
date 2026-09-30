from fastapi import APIRouter, Depends, Query

from app.db import call_fn, call_fn_jsonb, get_pool, record_to_dict
from app.deps import AuthUser, optional_auth, require_auth
from app.envelope import ok
from app.pagination import Pagination, pagination_params, paginated_envelope

router = APIRouter()


@router.get("/service-categories")
async def list_categories():
    async with get_pool().acquire() as conn:
        rows = await conn.fetch("SELECT id, name, key, icon, sla_hours FROM service_categories WHERE is_active ORDER BY name")
    return ok([record_to_dict(r) for r in rows])


@router.get("/providers/search")
async def search_providers(
    category: str = Query(...),
    community_id: int | None = Query(default=None),
    rating: float = Query(default=0),
    user: AuthUser | None = Depends(optional_auth),
    pagination: Pagination = Depends(pagination_params),
):
    if not category:
        return ok(paginated_envelope([], 0, pagination))

    rows = [record_to_dict(r) for r in await call_fn("fn_rank_providers", [community_id, category, rating, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))


@router.get("/providers/{provider_id}")
async def get_provider(provider_id: int, user: AuthUser | None = Depends(optional_auth)):
    return ok(await call_fn_jsonb("fn_get_public_provider_profile", [provider_id]))


@router.post("/providers/{provider_id}/favourite")
async def add_favourite(provider_id: int, user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_toggle_favourite", [user.user_id, provider_id, "add"]))


@router.delete("/providers/{provider_id}/favourite")
async def remove_favourite(provider_id: int, user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_toggle_favourite", [user.user_id, provider_id, "remove"]))
