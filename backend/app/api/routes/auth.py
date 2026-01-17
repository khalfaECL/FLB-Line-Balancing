import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, generate_token, hash_password, verify_password
from app.db.mongo import get_db
from app.schemas.auth import EmailRequest, PasswordReset, Token
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.emailer import (
    is_email_enabled,
    send_password_reset_email,
    send_verification_email,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _verification_payload() -> dict:
    settings = get_settings()
    token = generate_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.email_verify_expires_hours)
    return {
        "email_verified": False,
        "verification_token": token,
        "verification_sent_at": now,
        "verification_expires_at": expires_at,
    }


async def _authenticate(payload: UserLogin, db):
    user = await db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return user


def _token_for_user(user: dict) -> Token:
    token = create_access_token(subject=user["email"])
    return Token(access_token=token, token_type="bearer")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db=Depends(get_db)):
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    settings = get_settings()
    now = datetime.now(timezone.utc)
    doc = {
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": "client",
    }

    if settings.email_verification_required:
        doc.update(_verification_payload())
    else:
        doc["email_verified"] = True
        doc["verified_at"] = now

    result = await db.users.insert_one(doc)

    if settings.email_verification_required and is_email_enabled():
        try:
            send_verification_email(payload.email, doc["verification_token"])
        except Exception:
            logger.exception("Failed to send verification email to %s", payload.email)

    return UserOut(
        id=str(result.inserted_id),
        email=payload.email,
        role=doc["role"],
        email_verified=doc.get("email_verified", False),
    )


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db=Depends(get_db)):
    user = await _authenticate(payload, db)
    settings = get_settings()
    if (
        settings.email_verification_required
        and user.get("role") == "client"
        and not user.get("email_verified")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return _token_for_user(user)


@router.post("/login-client", response_model=Token)
async def login_client(payload: UserLogin, db=Depends(get_db)):
    user = await _authenticate(payload, db)
    settings = get_settings()
    if user.get("role") != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client access required",
        )
    if settings.email_verification_required and not user.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return _token_for_user(user)


@router.post("/login-admin", response_model=Token)
async def login_admin(payload: UserLogin, db=Depends(get_db)):
    user = await _authenticate(payload, db)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return _token_for_user(user)


@router.get("/verify")
async def verify_email(token: str, db=Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing token")

    user = await db.users.find_one({"verification_token": token})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    if user.get("email_verified"):
        return {"status": "verified"}

    expires_at = user.get("verification_expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired",
        )

    now = datetime.now(timezone.utc)
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"email_verified": True, "verified_at": now},
            "$unset": {
                "verification_token": "",
                "verification_sent_at": "",
                "verification_expires_at": "",
            },
        },
    )
    return {"status": "verified"}


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(payload: EmailRequest, db=Depends(get_db)):
    settings = get_settings()
    if not settings.email_verification_required:
        return {"status": "skipped"}

    user = await db.users.find_one({"email": payload.email})
    if not user:
        return {"status": "ok"}

    if user.get("email_verified"):
        return {"status": "verified"}

    token = generate_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.email_verify_expires_hours)

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "verification_token": token,
                "verification_sent_at": now,
                "verification_expires_at": expires_at,
            }
        },
    )

    if is_email_enabled():
        try:
            send_verification_email(payload.email, token)
        except Exception:
            logger.exception("Failed to resend verification email to %s", payload.email)

    return {"status": "sent"}


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: EmailRequest, db=Depends(get_db)):
    settings = get_settings()
    user = await db.users.find_one({"email": payload.email})
    if not user:
        return {"status": "ok"}

    token = generate_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.password_reset_expires_minutes)

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token": token,
                "password_reset_sent_at": now,
                "password_reset_expires_at": expires_at,
            }
        },
    )

    if is_email_enabled():
        try:
            send_password_reset_email(payload.email, token)
        except Exception:
            logger.exception("Failed to send password reset email to %s", payload.email)

    return {"status": "ok"}


@router.post("/reset-password")
async def reset_password(payload: PasswordReset, db=Depends(get_db)):
    user = await db.users.find_one({"password_reset_token": payload.token})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    expires_at = user.get("password_reset_expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired",
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": hash_password(payload.password)},
            "$unset": {
                "password_reset_token": "",
                "password_reset_sent_at": "",
                "password_reset_expires_at": "",
            },
        },
    )

    return {"status": "reset"}


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(
        id=str(current_user["_id"]),
        email=current_user["email"],
        role=current_user.get("role", "client"),
        email_verified=current_user.get("email_verified", False),
    )