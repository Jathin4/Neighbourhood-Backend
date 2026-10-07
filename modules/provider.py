from fastapi import APIRouter, Depends, Query

from database.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from pagination import Pagination, pagination_params
from models.provider_model import (
    AddStaffBody,
    AvailabilityBody,
    RequestServeCommunityBody,
    ServiceCatalogueBody,
    SubmitApplicationBody,
    SubmitDocumentBody,
    SupportTicketBody,
    TicketMessageBody,
    UpdateProfileBody,
    UpdateStaffBody,
)

router = APIRouter()


@router.get("/providers/me")
async def get_my_provider(user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_get_my_provider", [user.user_id]))
    if not row or not row.get("id"):
        return ok(None)
    return ok(row)


@router.post("/providers")
async def submit_application(body: SubmitApplicationBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_submit_provider_application", [
        user.user_id, body.business_name, body.categories, body.service_area, body.operating_hours, body.pricing_model,
    ]))
    return ok(row, 201)


@router.post("/providers/{provider_id}/documents")
async def submit_document(provider_id: int, body: SubmitDocumentBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_submit_provider_document", [user.user_id, provider_id, body.doc_type, body.file_url]))
    return ok(row, 201)


@router.get("/communities/browse")
async def browse_communities(search: str | None = Query(default=None), user: AuthUser = Depends(require_auth)):
    rows = await call_fn("fn_browse_communities", [search])
    return ok([record_to_dict(r) for r in rows])


@router.post("/providers/me/community-requests")
async def request_serve_community(body: RequestServeCommunityBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_request_serve_community", [user.user_id, body.community_id]))
    return ok(row, 201)


@router.get("/providers/me/community-requests")
async def my_community_requests(user: AuthUser = Depends(require_auth)):
    rows = await call_fn("fn_list_my_community_requests", [user.user_id])
    return ok([record_to_dict(r) for r in rows])


@router.get("/providers/me/dashboard")
async def my_dashboard(provider_id: int = Query(...), user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_get_provider_dashboard", [user.user_id, provider_id]))


@router.patch("/providers/me/profile")
async def update_profile(provider_id: int = Query(...), body: UpdateProfileBody = ..., user: AuthUser = Depends(require_auth)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    row = record_to_dict(await call_fn_one("fn_update_provider_profile", [user.user_id, provider_id, patch]))
    return ok(row)


@router.patch("/providers/me/service-catalogue")
async def update_service_catalogue(provider_id: int = Query(...), body: ServiceCatalogueBody = ..., user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_update_service_catalogue", [user.user_id, provider_id, body.pricing_model]))
    return ok(row)


@router.post("/providers/me/staff")
async def add_staff(provider_id: int = Query(...), body: AddStaffBody = ..., user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_add_provider_staff", [user.user_id, provider_id, body.staff_phone, body.role, body.name]))
    return ok(row, 201)


@router.get("/providers/me/staff")
async def list_staff(provider_id: int = Query(...), user: AuthUser = Depends(require_auth)):
    rows = await call_fn("fn_list_provider_staff", [user.user_id, provider_id])
    return ok([record_to_dict(r) for r in rows])


@router.patch("/providers/me/staff/{staff_id}")
async def update_staff(staff_id: int, provider_id: int = Query(...), body: UpdateStaffBody = ..., user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_update_provider_staff", [user.user_id, provider_id, staff_id, body.role, body.active]))
    return ok(row)


@router.get("/providers/me/availability")
async def get_availability(provider_id: int = Query(...), user: AuthUser = Depends(require_auth)):
    return ok(record_to_dict(await call_fn_one("fn_get_provider_availability", [user.user_id, provider_id])))


@router.patch("/providers/me/availability")
async def update_availability(provider_id: int = Query(...), body: AvailabilityBody = ..., user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_update_provider_availability", [user.user_id, provider_id, body.weekly_schedule, body.blackout_dates]))
    return ok(row)


@router.get("/providers/me/leads")
async def leads(provider_id: int = Query(...), user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = await call_fn("fn_list_bookings_for_provider", [user.user_id, provider_id, pagination.limit, pagination.offset])
    return ok([r["booking"] for r in rows if r["booking"]["status"] == "Requested"])


@router.post("/providers/me/support-tickets")
async def create_support_ticket(body: SupportTicketBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_create_support_ticket", [user.user_id, body.provider_id, body.subject, body.description]))
    return ok(row, 201)


@router.get("/providers/me/support-tickets")
async def list_support_tickets(provider_id: int = Query(...), user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = await call_fn("fn_list_support_tickets", [user.user_id, provider_id, pagination.limit, pagination.offset])
    return ok([r["ticket"] for r in rows])


@router.post("/providers/me/support-tickets/{ticket_id}/messages")
async def add_ticket_message(ticket_id: int, body: TicketMessageBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_add_support_ticket_message", [user.user_id, ticket_id, body.message]))
    return ok(row, 201)
