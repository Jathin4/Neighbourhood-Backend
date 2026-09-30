from fastapi import Query


class Pagination:
    def __init__(self, limit: int = 20, offset: int = 0):
        self.limit = limit
        self.offset = offset


def pagination_params(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)) -> Pagination:
    return Pagination(limit=limit, offset=offset)


def paginated_envelope(items: list, total: int, pagination: Pagination) -> dict:
    next_offset = pagination.offset + len(items)
    return {
        "items": items,
        "total": total,
        "limit": pagination.limit,
        "offset": pagination.offset,
        "next_cursor": str(next_offset) if next_offset < total else None,
    }
