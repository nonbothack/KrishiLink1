from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.models import User
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

@router.post("/register", response_model=dict, status_code=201)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_reg")
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    user = register_user(db, data, request)
    tokens = issue_tokens(user)
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Registered successfully",
        "request_id": getattr(request.state, "request_id", None),
    }

@router.post("/login", response_model=dict)
@rate_limit(max_requests=25, window_seconds=60, key_prefix="rl_login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password, request)
    tokens = issue_tokens(user)
    return {
        "success": True,
        "data": {"user": UserResponse.model_validate(user).model_dump(), **tokens},
        "message": "Login successful",
        "request_id": getattr(request.state, "request_id", None),
    }

@router.post("/refresh", response_model=dict)
@rate_limit(max_requests=30, window_seconds=60, key_prefix="rl_ref")
def refresh(data: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    tokens = refresh_tokens(db, data.refresh_token)
    return {
        "success": True,
        "data": tokens,
        "message": "Tokens refreshed",
        "request_id": getattr(request.state, "request_id", None),
    }

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
    data: LogoutRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    access_token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        access_token = auth_header.split(" ", 1)[1].strip()
    refresh_token = data.refresh_token if data else None

    res = logout_user(db, access_token, refresh_token, user, request)
    return {
        "success": True,
        "data": None,
        "message": res["message"],
        "request_id": getattr(request.state, "request_id", None),
    }
