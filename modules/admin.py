from fastapi import APIRouter, Depends, Query

from database.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_auth, require_role
from envelope import ok
from pagination import Pagination, pagination_params, paginated_envelope
from models.admin_model import (
    AdminCreateProviderBody,
    BulkImportBody,
    CommitteeRoleBody,
    CreateCommunityBody,
    CreateTowerBody,
    CreateUnitBody,
    CuratedProviderBody,
    DecideCommunityRequestBody,
    MembershipDecisionBody,
    ModerationBody,
    UpdateCommunityBody,
    VerificationBody,
)

router = APIRouter()

admin_roles = ("community_admin", "platform_admin")


@router.get("/admin/communities")
async def list_communities(user: AuthUser = Depends(require_role(*admin_roles))):
    rows = await call_fn("fn_list_communities", [user.user_id])
    return ok([record_to_dict(r) for r in rows])


@router.get("/admin/communities/{community_id}/towers")
async def list_towers(community_id: int, user: AuthUser = Depends(require_auth)):
    # fn_list_towers re-validates via fn__has_capability('can_manage_structure')
    rows = await call_fn("fn_list_towers", [user.user_id, community_id])
    return ok([record_to_dict(r) for r in rows])


@router.get("/admin/towers/{tower_id}/units")
async def list_units(tower_id: int, user: AuthUser = Depends(require_auth)):
    # fn_list_units re-validates via fn__has_capability('can_manage_structure')
    rows = await call_fn("fn_list_units", [user.user_id, tower_id])
    return ok([record_to_dict(r) for r in rows])


@router.get("/admin/communities/{community_id}/residents")
async def admin_search_residents(
    community_id: int, query: str | None = Query(default=None), limit: int = Query(default=200, le=500),
    user: AuthUser = Depends(require_role(*admin_roles)),
):
    rows = await call_fn("fn_admin_search_residents", [user.user_id, community_id, query, limit])
    return ok([record_to_dict(r) for r in rows])


@router.post("/admin/communities")
async def create_community(body: CreateCommunityBody, user: AuthUser = Depends(require_role("platform_admin"))):
    row = record_to_dict(await call_fn_one("fn_create_community", [user.user_id, body.name, body.city, body.default_currency]))
    return ok(row, 201)


@router.patch("/admin/communities/{community_id}")
async def update_community(community_id: int, body: UpdateCommunityBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one("fn_update_community", [user.user_id, community_id, body.name, body.city]))
    return ok(row)


@router.post("/admin/towers")
async def create_tower(body: CreateTowerBody, user: AuthUser = Depends(require_auth)):
    # fn_create_tower re-validates via fn__has_capability('can_manage_structure')
    row = record_to_dict(await call_fn_one("fn_create_tower", [user.user_id, body.community_id, body.name]))
    return ok(row, 201)


@router.post("/admin/units")
async def create_unit(body: CreateUnitBody, user: AuthUser = Depends(require_auth)):
    # fn_create_unit re-validates via fn__has_capability('can_manage_structure')
    row = record_to_dict(await call_fn_one("fn_create_unit", [user.user_id, body.tower_id, body.name]))
    return ok(row, 201)


@router.post("/admin/communities/{community_id}/residents/bulk-import")
async def bulk_import_residents(community_id: int, body: BulkImportBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one("fn_bulk_import_residents", [user.user_id, community_id, body.rows]))
    return ok(row, 201)


@router.get("/admin/membership-requests")
async def list_membership_requests(
    community_id: int = Query(...), status: str | None = Query(default=None),
    user: AuthUser = Depends(require_role(*admin_roles)), pagination: Pagination = Depends(pagination_params),
):
    rows = await call_fn("fn_list_membership_requests", [user.user_id, community_id, status, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    return ok(paginated_envelope([r["request"] for r in rows], total, pagination))


@router.patch("/admin/membership-requests/{request_id}")
async def decide_membership_request(request_id: int, body: MembershipDecisionBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one("fn_update_membership_request", [user.user_id, request_id, body.status, body.reason]))
    return ok(row)


@router.get("/admin/issues")
async def list_community_issues(
    community_id: int = Query(...), status: str | None = Query(default=None),
    user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params),
):
    # fn_list_issues_for_community re-validates via fn__has_capability('can_assign_issue')
    rows = await call_fn("fn_list_issues_for_community", [user.user_id, community_id, status, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    return ok(paginated_envelope([r["issue"] for r in rows], total, pagination))


@router.post("/admin/committee-roles")
async def assign_committee_role(body: CommitteeRoleBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one("fn_assign_committee_role", [user.user_id, body.community_id, body.target_user_id, body.capabilities]))
    return ok(row, 201)


@router.get("/admin/committee-roles")
async def list_committee_members(community_id: int = Query(...), user: AuthUser = Depends(require_role(*admin_roles))):
    rows = await call_fn("fn_list_committee_members", [user.user_id, community_id])
    return ok([record_to_dict(r) for r in rows])


@router.post("/admin/providers")
async def admin_create_provider(body: AdminCreateProviderBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one(
        "fn_admin_create_provider", [user.user_id, body.phone, body.business_name, body.categories, body.community_id, body.auto_verify]
    ))
    return ok(row, 201)


@router.get("/admin/providers/community-requests")
async def list_community_provider_requests(
    community_id: int = Query(...), status: str | None = Query(default="Pending"),
    user: AuthUser = Depends(require_role(*admin_roles)),
):
    rows = await call_fn("fn_list_community_provider_requests", [user.user_id, community_id, status])
    return ok([record_to_dict(r) for r in rows])


@router.patch("/admin/providers/community-requests/{request_id}")
async def decide_community_provider_request(
    request_id: int, body: DecideCommunityRequestBody, user: AuthUser = Depends(require_role(*admin_roles)),
):
    row = record_to_dict(await call_fn_one("fn_decide_community_provider_request", [user.user_id, request_id, body.new_status, body.note]))
    return ok(row)


@router.patch("/admin/providers/{provider_id}/verification")
async def update_provider_verification(provider_id: int, body: VerificationBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one(
        "fn_update_provider_verification", [user.user_id, provider_id, body.new_state, body.reason, body.verification_expiry_at]
    ))
    return ok(row)


@router.get("/admin/providers/verification-queue")
async def provider_verification_queue(
    states: str = Query(default="Submitted,UnderReview"),
    user: AuthUser = Depends(require_role(*admin_roles)), pagination: Pagination = Depends(pagination_params),
):
    state_list = [s.strip() for s in states.split(",") if s.strip()]
    rows = await call_fn("fn_list_providers_for_verification", [user.user_id, state_list, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    return ok(paginated_envelope([r["provider"] for r in rows], total, pagination))


@router.post("/admin/providers/curated")
async def curate_provider(body: CuratedProviderBody, user: AuthUser = Depends(require_role(*admin_roles))):
    row = record_to_dict(await call_fn_one("fn_curate_provider", [user.user_id, body.community_id, body.provider_id, body.label]))
    return ok(row, 201)


@router.get("/admin/providers/curated")
async def list_curated_providers(community_id: int = Query(...), user: AuthUser = Depends(require_role(*admin_roles))):
    rows = await call_fn("fn_list_curated_providers", [user.user_id, community_id])
    return ok([r["entry"] for r in rows])


@router.delete("/admin/providers/curated/{curated_id}")
async def remove_curated_provider(curated_id: int, user: AuthUser = Depends(require_role(*admin_roles))):
    await call_fn("fn_remove_curated_provider", [user.user_id, curated_id])
    return ok({"removed": True})


@router.get("/admin/moderation/flagged-reviews")
async def flagged_reviews(user: AuthUser = Depends(require_role(*admin_roles)), pagination: Pagination = Depends(pagination_params)):
    rows = await call_fn("fn_list_flagged_reviews", [user.user_id, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    return ok(paginated_envelope([r["review"] for r in rows], total, pagination))


@router.get("/admin/reports")
async def generate_report(
    community_id: int = Query(...), report_type: str = Query(...), user: AuthUser = Depends(require_role(*admin_roles))
):
    return ok(await call_fn_jsonb("fn_generate_admin_report", [user.user_id, community_id, report_type, {}]))


@router.post("/admin/moderation/{content_type}/{content_id}")
async def moderate_content(content_type: str, content_id: int, body: ModerationBody, user: AuthUser = Depends(require_role(*admin_roles))):
    return ok(await call_fn_jsonb("fn_moderate_content", [user.user_id, content_type, content_id, body.action, body.reason]))
