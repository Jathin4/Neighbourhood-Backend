from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok(data: Any, status: int = 200) -> JSONResponse:
    """The standard success envelope every endpoint returns."""
    return JSONResponse(status_code=status, content=jsonable_encoder({"success": True, "data": data, "error": None}))
