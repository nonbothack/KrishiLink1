import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
            minimum = 10 if str(field) in {"password", "new_password"} else 6
            err_msgs.append(f"{field.replace('_', ' ').capitalize()} must be at least {minimum} characters")
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
            # Validation errors may contain submitted values and non-JSON-safe
            # exception objects. Return only schema locations and plain messages.
            "details": [
                {
                    "type": str(error.get("type", "value_error")),
                    "loc": [str(part) for part in error.get("loc", [])],
                    "msg": str(error.get("msg", "Invalid value")),
                }
                for error in exc.errors()
            ],
            "request_id": rid,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
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
