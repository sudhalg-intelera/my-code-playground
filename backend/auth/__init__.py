"""Auth as one stack: JWT issuance/verification and register/login live in
service.py. Re-exported here so `from auth import ...` keeps working
unchanged for main.py."""

from auth.service import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    get_current_user,
    login_user,
    register_user,
)

__all__ = [
    "AuthResponse",
    "LoginRequest",
    "RegisterRequest",
    "get_current_user",
    "login_user",
    "register_user",
]
