from fastapi import APIRouter, Depends, Query

from database.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_role
from envelope import ok
from pagination import Pagination, pagination_params, paginated_envelope
from models.platform_admin_model import CreateCategoryBody, FeatureFlagBody, UpdateCategoryBody

router = APIRouter()

platform_only = require_role("platform_admin")


@router.post("/platform/categories")
async def create_category(body: CreateCategoryBody, user: AuthUser = Depends(platform_only)):
    row = record_to_dict(await call_fn_one("fn_create_service_category", [user.user_id, body.name, body.key, body.icon, body.commission_rate, body.sla_hours]))
    return ok(row, 201)


@router.patch("/platform/categories/{category_id}")
async def update_category(category_id: int, body: UpdateCategoryBody, user: AuthUser = Depends(platform_only)):
    row = record_to_dict(await call_fn_one("fn_update_category_config", [user.user_id, category_id, body.commission_rate, body.sla_hours, body.config]))
    return ok(row)


@router.post("/platform/feature-flags")
async def update_feature_flag(body: FeatureFlagBody, user: AuthUser = Depends(platform_only)):
    row = record_to_dict(await call_fn_one("fn_update_feature_flag", [user.user_id, body.community_id, body.key, body.enabled, body.config]))
    return ok(row, 201)


@router.get("/platform/audit-log")
async def audit_log(
    entity_type: str | None = Query(default=None), user: AuthUser = Depends(platform_only), pagination: Pagination = Depends(pagination_params)
):
    rows = await call_fn("fn_get_audit_log", [user.user_id, entity_type, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    return ok(paginated_envelope([r["entry"] for r in rows], total, pagination))


@router.get("/platform/kpis")
async def kpis(user: AuthUser = Depends(platform_only)):
    return ok(await call_fn_jsonb("fn_get_platform_kpis", [user.user_id]))
