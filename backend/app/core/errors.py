import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def request_id_var() -> str:
    return str(uuid.uuid4())


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    err_msgs = []
    for err in exc.errors():
        loc = err.get("loc", [])
        field = loc[-1] if loc else "field"
        msg = err.get("msg", "Invalid value")

        # User-friendly translation of pydantic errors
        if "value is not a valid email address" in msg or "email" in str(field).lower():
            err_msgs.append("Please enter a valid email address including domain (e.g. name@gmail.com)")
        elif "string does not match regex" in msg or "phone" in str(field).lower():
            err_msgs.append("Phone number must be a 10-digit number (e.g. 9876543210)")
        elif "at least" in msg and "character" in msg:
            err_msgs.append(f"{field.replace('_', ' ').capitalize()} must be at least 6 characters")
        else:
            err_msgs.append(f"{field.replace('_', ' ').capitalize()}: {msg}")

    friendly_message = ". ".join(err_msgs) if err_msgs else "Validation failed. Please check your inputs."
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "message": friendly_message,
            "code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "request_id": rid,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": str(exc.detail),
                "code": "HTTP_ERROR",
                "request_id": rid,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "Internal server error",
            "code": "INTERNAL_ERROR",
            "request_id": rid,
        },
    )
