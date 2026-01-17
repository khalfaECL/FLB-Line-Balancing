import logging

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.mongo import get_db

logger = logging.getLogger(__name__)


async def ensure_admin_user() -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return

    password_bytes = settings.admin_password.encode("utf-8")
    if len(password_bytes) > 72:
        logger.error(
            "ADMIN_PASSWORD too long for bcrypt (max 72 bytes). Admin seed skipped."
        )
        return

    db = get_db()
    existing = await db.users.find_one({"email": settings.admin_email})
    if existing:
        updates = {}
        if existing.get("role") != "admin":
            updates["role"] = "admin"
        if not existing.get("email_verified", False):
            updates["email_verified"] = True
        if updates:
            await db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": updates},
            )
            logger.info("Updated existing admin user: %s", settings.admin_email)
        return

    try:
        password_hash = hash_password(settings.admin_password)
    except Exception:
        logger.exception("Failed to hash ADMIN_PASSWORD. Admin seed skipped.")
        return

    doc = {
        "email": settings.admin_email,
        "password_hash": password_hash,
        "role": "admin",
        "email_verified": True,
    }
    await db.users.insert_one(doc)
    logger.info("Seeded admin user: %s", settings.admin_email)