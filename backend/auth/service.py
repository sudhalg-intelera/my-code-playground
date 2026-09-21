import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import psycopg
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from pydantic import BaseModel

from observability.audit import write_audit_log
from database import get_db_connection
from logging_config import get_logger

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
logger = get_logger("auth")

JWT_SECRET = os.environ["JWT_SECRET"]  # fail at startup, not with a public fallback secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 12


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str
    role: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def issue_token(user_uuid: str, role: str) -> str:
    """The JWT's `sub` is the user's stable UUID, not their username - the
    username can be shown/changed freely without touching what every table
    actually keys off of."""
    payload = {
        "sub": user_uuid,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def register_user(req: RegisterRequest) -> AuthResponse:
    if req.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="role must be 'user' or 'admin'")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s) "
                "RETURNING user_uuid",
                (req.username, req.email, hash_password(req.password), req.role),
            )
            user_uuid = cursor.fetchone()["user_uuid"]
        conn.commit()
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        logger.warning("Registration failed - username or email already taken: %s", req.username)
        write_audit_log(req.username, "register_failed", "username or email already registered")
        raise HTTPException(status_code=409, detail="username or email already registered")
    finally:
        conn.close()

    logger.info("User registered: %s (role=%s)", req.username, req.role)
    write_audit_log(req.username, "register_success", {"role": req.role})

    return AuthResponse(token=issue_token(str(user_uuid), req.role), username=req.username, role=req.role)


def login_user(req: LoginRequest) -> AuthResponse:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT username, password_hash, role, user_uuid FROM users WHERE username = %s",
                (req.username,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row or not row["password_hash"] or not verify_password(req.password, row["password_hash"]):
        logger.warning("Login failed for username: %s", req.username)
        write_audit_log(req.username, "login_failed", "invalid username or password")
        raise HTTPException(status_code=401, detail="invalid username or password")

    logger.info("User logged in: %s", row["username"])
    write_audit_log(row["username"], "login_success", {"role": row["role"]})

    return AuthResponse(
        token=issue_token(str(row["user_uuid"]), row["role"]), username=row["username"], role=row["role"]
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token")


def get_current_user(authorization: str = Header(default="")) -> dict:
    """FastAPI dependency: requires a valid bearer token, any role."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return decode_token(authorization.removeprefix("Bearer ").strip())


def require_role(*allowed_roles: str):
    """FastAPI dependency factory: protects a route behind one of the given roles."""

    def _dependency(authorization: str = Header(default="")) -> dict:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")

        claims = decode_token(authorization.removeprefix("Bearer ").strip())

        if claims.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="insufficient role")

        return claims

    return _dependency
