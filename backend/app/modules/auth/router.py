import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.core.security import decode_token
from app.models import AuditLog, User
from app.modules.auth.identity import current_policy_versions
from app.modules.auth.otp_service import request_otp, verify_otp
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    OtpRequest,
    OtpVerify,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.modules.auth.service import (
    authenticate_user,
    logout_user,
    refresh_tokens,
    register_user,
    request_password_reset,
    reset_password,
)
from app.modules.auth.session_service import create_session_tokens

router = APIRouter(prefix="/auth", tags=["auth"])

def check_browser_origin(
    request: Request,
    *,
    require_csrf: bool = False,
    allow_legacy_cookie_bootstrap: bool = False,
):
    origin = request.headers.get("origin")
    is_web = request.headers.get("x-krishilink-client") == "web"
    if is_web and not origin:
        raise HTTPException(403, "Browser origin is required")
    if origin and origin not in settings.cors_origins_list:
        raise HTTPException(403, "Unrecognized browser origin")
    if not origin and request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site session request denied")
    if is_web and require_csrf:
        cookie_token = request.cookies.get("krishilink_csrf", "")
        header_token = request.headers.get("x-krishilink-csrf", "")
        if cookie_token or header_token:
            if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
                raise HTTPException(403, "Browser session check failed")
        elif not allow_legacy_cookie_bootstrap:
            raise HTTPException(403, "Browser session check failed")


def browser_tokens(request: Request, response: Response, tokens: dict):
    if request.headers.get("x-krishilink-client") != "web":
        return tokens
    check_browser_origin(request)
    response.set_cookie("krishilink_refresh", tokens["refresh_token"], httponly=True,
                        secure=settings.env == "production", samesite="strict",
                        path="/api/v1/auth", max_age=settings.jwt_refresh_ttl_days * 86400)
    response.set_cookie(
        "krishilink_csrf",
        secrets.token_urlsafe(32),
        httponly=False,
        secure=settings.env == "production",
        samesite="strict",
        path="/",
        max_age=settings.jwt_refresh_ttl_days * 86400,
    )
    return {key: value for key, value in tokens.items() if key != "refresh_token"}



@router.post("/register", response_model=dict, status_code=201)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_reg", production_requires_redis=True)
def register(data: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, data, request)
    tokens = browser_tokens(request, response, create_session_tokens(db, user, request.headers.get("user-agent")))
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Registered successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/login", response_model=dict)
@rate_limit(max_requests=25, window_seconds=60, key_prefix="rl_login", production_requires_redis=True)
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password, request)
    tokens = browser_tokens(request, response, create_session_tokens(db, user, request.headers.get("user-agent")))
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Login successful",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/refresh", response_model=dict)
@rate_limit(max_requests=30, window_seconds=60, key_prefix="rl_ref", production_requires_redis=True)
def refresh(request: Request, response: Response, data: RefreshRequest | None = None, db: Session = Depends(get_db)):
    token = data.refresh_token if data else request.cookies.get("krishilink_refresh")
    if request.headers.get("x-krishilink-client") == "web":
        check_browser_origin(
            request,
            require_csrf=True,
            allow_legacy_cookie_bootstrap=bool(not data and request.cookies.get("krishilink_refresh")),
        )
    elif not data:
        check_browser_origin(request)
    if not token:
        raise HTTPException(401, "Missing refresh session")
    tokens = browser_tokens(request, response, refresh_tokens(db, token))
    return {"success": True, "data": tokens, "message": "Session refreshed"}


@router.get("/policy-versions", response_model=dict)
def policy_versions(request: Request):
    return {
        "success": True,
        "data": current_policy_versions(),
        "message": "Current policy versions",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/otp/request", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_otp_req", production_requires_redis=True)
def otp_request(data: OtpRequest, request: Request, db: Session = Depends(get_db)):
    result = request_otp(db, data.phone, request)
    return {
        "success": True,
        "data": result,
        "message": result["message"],
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/otp/verify", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_otp_verify", production_requires_redis=True)
def otp_verify(data: OtpVerify, request: Request, response: Response, db: Session = Depends(get_db)):
    result = verify_otp(db, data.phone, data.code, request)
    if not result["account_exists"]:
        return {
            "success": True,
            "data": {key: value for key, value in result.items() if key != "account_exists"},
            "message": "Mobile number verified. Continue creating your account.",
            "request_id": getattr(request.state, "request_id", None),
        }
    user = result["user"]
    tokens = browser_tokens(request, response, {key: result[key] for key in ("access_token", "refresh_token", "token_type", "expires_in")})
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Sign-in successful",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/forgot-password", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_fp", production_requires_redis=True)
def forgot_password(data: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    res = request_password_reset(db, data.email, request)
    return {
        "success": True,
        "data": res,
        "message": res["message"],
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/reset-password", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_rp", production_requires_redis=True)
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
    is_web = request.headers.get("x-krishilink-client") == "web"
    check_browser_origin(request, require_csrf=is_web)
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    payload = decode_token(token)
    sid = payload.get("sid")
    if sid:
        db.add(AuditLog(actor_id=str(user.id), action="session.revoked", entity="session", entity_id=sid))
        db.commit()
    logout_user(
        db,
        token,
        data.refresh_token if data else request.cookies.get("krishilink_refresh"),
        user,
        request,
        session_id=str(sid) if sid else None,
    )
    response.delete_cookie(
        "krishilink_refresh", path="/api/v1/auth", httponly=True,
        secure=settings.env == "production", samesite="strict",
    )
    response.delete_cookie(
        "krishilink_csrf", path="/", httponly=False,
        secure=settings.env == "production", samesite="strict",
    )
    return {"success": True, "data": None, "message": "Session ended"}
