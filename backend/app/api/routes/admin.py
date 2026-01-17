import asyncio
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin
from app.db.mongo import get_db
from app.services.emailer import is_email_enabled, send_report_email
from app.services.queue import enqueue_job
from app.services.serializers import serialize_job, serialize_user

router = APIRouter()


@router.get("/users")
async def list_users(db=Depends(get_db), current_user=Depends(require_admin)):
    cursor = db.users.find({}).sort("email", 1).limit(200)
    users = [serialize_user(user) async for user in cursor]
    return users


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db=Depends(get_db), current_user=Depends(require_admin)):
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin accounts",
        )

    cursor = db.jobs.find({"user_id": obj_id})
    async for job in cursor:
        for path in [job.get("stored_path"), job.get("report_path")]:
            if path:
                Path(path).unlink(missing_ok=True)

    await db.jobs.delete_many({"user_id": obj_id})
    await db.users.delete_one({"_id": obj_id})

    return {"user_id": user_id, "deleted": True}


@router.get("/jobs")
async def list_jobs(db=Depends(get_db), current_user=Depends(require_admin)):
    cursor = db.jobs.find({}).sort("created_at", -1).limit(200)
    jobs = [serialize_job(job, include_user_id=True) async for job in cursor]
    return jobs


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, db=Depends(get_db), current_user=Depends(require_admin)):
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")

    job = await db.jobs.find_one({"_id": obj_id})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.get("status") == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is already processing",
        )

    stored_path = job.get("stored_path")
    if not stored_path or not Path(stored_path).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored file missing",
        )

    now = datetime.now(timezone.utc)
    await db.jobs.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "status": "queued",
                "error": None,
                "result": None,
                "report_path": None,
                "report_name": None,
                "completed_at": None,
                "email_status": None,
                "email_error": None,
                "email_sent_at": None,
                "updated_at": now,
            }
        },
    )

    enqueue_job(job_id, job.get("method", "ALL"), stored_path, db)
    return {"job_id": job_id, "status": "queued"}


@router.post("/jobs/{job_id}/resend")
async def resend_report(job_id: str, db=Depends(get_db), current_user=Depends(require_admin)):
    if not is_email_enabled():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP is not enabled",
        )

    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")

    job = await db.jobs.find_one({"_id": obj_id})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    report_path = job.get("report_path")
    if not report_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not ready")

    user = await db.users.find_one({"_id": job.get("user_id")})
    if not user or not user.get("email"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User email not found")

    path = Path(report_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file missing")

    try:
        await asyncio.to_thread(send_report_email, user["email"], report_path, job_id)
        await db.jobs.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "email_status": "sent",
                    "email_error": None,
                    "email_sent_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"job_id": job_id, "status": "sent"}
    except Exception as exc:
        await db.jobs.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "email_status": "failed",
                    "email_error": str(exc),
                }
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db=Depends(get_db), current_user=Depends(require_admin)):
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")

    job = await db.jobs.find_one({"_id": obj_id})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    stored_path = job.get("stored_path")
    report_path = job.get("report_path")

    await db.jobs.delete_one({"_id": obj_id})

    for path in [stored_path, report_path]:
        if path:
            Path(path).unlink(missing_ok=True)

    return {"job_id": job_id, "deleted": True}