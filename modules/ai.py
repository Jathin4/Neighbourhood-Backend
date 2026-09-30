"""ai — Phase 2. Interfaces scaffolded now so the contract is stable;
implementation intentionally deferred. Per the product guardrails: AI must never
autonomously execute sensitive actions (refunds, suspensions, dispute decisions),
must enforce authorization before retrieval, must carry traceable source
references, and must say so plainly when confidence is low."""

from fastapi import APIRouter, Depends, Query

from deps import AuthUser, require_auth
from envelope import ok
from models.ai_model import AssistantQueryBody

router = APIRouter()


@router.post("/ai/community-assistant/query")
async def community_assistant_query(body: AssistantQueryBody, user: AuthUser = Depends(require_auth)):
    # TODO(Phase 2): retrieve only notices/rules/events/service info the caller is
    # authorized to see (community-scoped, same rules as notice/marketplace),
    # answer strictly from those sources, attach source references, and offer human
    # escalation whenever confidence is low. Never wire this to refund/suspend/dispute actions.
    return ok({
        "answer": None,
        "confidence": "unavailable",
        "sources": [],
        "escalation_available": True,
        "message": "The community assistant is not yet available. Please use Notices, Issues or Services directly, or contact your community admin.",
    })


@router.get("/ai/provider-recommendations")
async def provider_recommendations(
    category: str = Query(...), community_id: int | None = Query(default=None), user: AuthUser = Depends(require_auth)
):
    # TODO(Phase 2): rank using verification, completed jobs, ratings, recency,
    # availability, service area and resident feedback — swappable independently
    # of fn_rank_providers (the marketplace core), and never ranked solely on
    # paid placement. Until implemented, defer to the marketplace ranking directly.
    # Note: fn_rank_providers requires an Approved provider_community_requests row
    # per community, so a caller must pass community_id or results will be empty.
    from database.db import call_fn, record_to_dict

    rows = [record_to_dict(r) for r in await call_fn("fn_rank_providers", [community_id, category, 0, 20, 0])]
    return ok({
        "recommendations": [{k: v for k, v in r.items() if k != "total_count"} for r in rows],
        "factors": ["verification_state", "rating_avg", "jobs_completed"],
        "note": "AI-personalized recommendations are Phase 2 — this falls back to the standard marketplace ranking.",
    })
