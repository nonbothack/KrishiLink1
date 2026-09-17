from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.core.security import decode_token
from app.models import AuditLog, User
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.modules.auth.service import (
    authenticate_user,
    issue_tokens,
    logout_user,
    refresh_tokens,
    register_user,
    request_password_reset,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

def check_browser_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins_list:
        raise HTTPException(403, "Unrecognized browser origin")
    if not origin and request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site session request denied")


def browser_tokens(request: Request, response: Response, tokens: dict):
    if request.headers.get("x-krishilink-client") != "web":
        return tokens
    check_browser_origin(request)
    response.set_cookie("krishilink_refresh", tokens["refresh_token"], httponly=True,
                        secure=settings.env == "production", samesite="lax",
                        path="/api/v1/auth", max_age=settings.jwt_refresh_ttl_days * 86400)
    return {key: value for key, value in tokens.items() if key != "refresh_token"}



@router.post("/register", response_model=dict, status_code=201)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_reg")
def register(data: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, data, request)
    tokens = browser_tokens(request, response, issue_tokens(user))
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Registered successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/login", response_model=dict)
@rate_limit(max_requests=25, window_seconds=60, key_prefix="rl_login")
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password, request)
    tokens = browser_tokens(request, response, issue_tokens(user))
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Login successful",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/refresh", response_model=dict)
@rate_limit(max_requests=30, window_seconds=60, key_prefix="rl_ref")
def refresh(request: Request, response: Response, data: RefreshRequest | None = None, db: Session = Depends(get_db)):
    token = data.refresh_token if data else request.cookies.get("krishilink_refresh")
    if not data:
        check_browser_origin(request)
    if not token:
        raise HTTPException(401, "Missing refresh session")
    tokens = browser_tokens(request, response, refresh_tokens(db, token))
    return {"success": True, "data": tokens, "message": "Session refreshed"}


@router.post("/forgot-password", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_fp")
def forgot_password(data: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    res = request_password_reset(db, data.email, request)
    return {
        "success": True,
        "data": res,
        "message": res["message"],
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/reset-password", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_rp")
def reset_password_endpoint(data: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    res = reset_password(db, data.token, data.new_password, request)
    return {
        "success": True,
        "data": res,
        "message": res["message"],
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/me", response_model=dict)
def me(request: Request, user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "message": "Current user",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/logout", response_model=dict)
def logout(
    request: Request,
    response: Response,
    data: LogoutRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_browser_origin(request)
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    payload = decode_token(token)
    sid = payload.get("sid")
    if sid:
        db.add(AuditLog(actor_id=str(user.id), action="session.revoked", entity="session", entity_id=sid))
        db.commit()
    logout_user(db, token, data.refresh_token if data else request.cookies.get("krishilink_refresh"), user, request)
    response.delete_cookie("krishilink_refresh", path="/api/v1/auth", httponly=True, samesite="lax")
    return {"success": True, "data": None, "message": "Session ended"}
