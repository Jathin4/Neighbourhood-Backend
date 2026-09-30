from fastapi import APIRouter, Depends

from database.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from pagination import Pagination, pagination_params, paginated_envelope
from modules.notification import dispatch
from models.issue_model import AssignBody, CommentBody, CreateIssueBody, ReopenBody, StatusBody

router = APIRouter()


@router.post("/issues")
async def create_issue(body: CreateIssueBody, user: AuthUser = Depends(require_auth)):
    issue = record_to_dict(await call_fn_one("fn_create_issue", [
        user.user_id, body.community_id, body.category, body.description, body.media, body.location, body.urgency,
    ]))
    return ok(issue, 201)


@router.get("/issues/mine")
async def list_my_issues(user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = [record_to_dict(r) for r in await call_fn("fn_list_issues_for_resident", [user.user_id, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))


@router.get("/issues/{ticket_no}")
async def get_issue(ticket_no: str, user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_get_issue_detail", [user.user_id, ticket_no]))


@router.post("/issues/{issue_id}/comments")
async def add_comment(issue_id: int, body: CommentBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_add_issue_comment", [user.user_id, issue_id, body.comment]))
    return ok(row, 201)


@router.post("/issues/{issue_id}/reopen")
async def reopen_issue(issue_id: int, body: ReopenBody, user: AuthUser = Depends(require_auth)):
    issue = record_to_dict(await call_fn_one("fn_reopen_issue", [user.user_id, issue_id, body.reason]))
    await dispatch(issue["resident_user_id"], "issue_status_changed", {"ticket_no": issue["ticket_no"], "status": issue["status"]})
    return ok(issue)


@router.patch("/issues/{issue_id}/assign")
async def assign_issue(issue_id: int, body: AssignBody, user: AuthUser = Depends(require_auth)):
    issue = record_to_dict(await call_fn_one("fn_assign_issue", [user.user_id, issue_id, body.owner_id, body.note]))
    await dispatch(issue["resident_user_id"], "issue_status_changed", {"ticket_no": issue["ticket_no"], "status": issue["status"]})
    return ok(issue)


@router.patch("/issues/{issue_id}/status")
async def transition_status(issue_id: int, body: StatusBody, user: AuthUser = Depends(require_auth)):
    issue = record_to_dict(await call_fn_one("fn_transition_issue_status", [user.user_id, issue_id, body.status, body.note]))
    await dispatch(issue["resident_user_id"], "issue_status_changed", {"ticket_no": issue["ticket_no"], "status": issue["status"]})
    return ok(issue)
