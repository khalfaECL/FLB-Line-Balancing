from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user, require_client
from app.core.config import get_settings
from app.db.mongo import get_db
from app.services.queue import enqueue_job
from app.services.serializers import serialize_job
from app.services.storage import save_upload_file, safe_filename

router = APIRouter()

ALLOWED_METHODS = {"MTE", "SPT", "RPW", "ALL"}


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(
    method: str = Form("ALL"),
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(require_client),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    method = method.upper()
    if method not in ALLOWED_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported method: {method}",
        )

    settings = get_settings()
    existing_count = await db.jobs.count_documents({"user_id": current_user["_id"]})
    if existing_count >= settings.max_client_jobs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job limit reached ({settings.max_client_jobs}). Delete older runs.",
        )

    job_id = ObjectId()
    original_name = safe_filename(file.filename)
    stored_name = f"{job_id}_{original_name}"
    upload_path = Path(settings.upload_dir) / stored_name

    try:
        save_upload_file(file, upload_path)
    finally:
        await file.close()

    now = datetime.now(timezone.utc)
    doc = {
        "_id": job_id,
        "user_id": current_user["_id"],
        "filename": original_name,
        "stored_path": str(upload_path),
        "method": method,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
    }
    await db.jobs.insert_one(doc)
    enqueue_job(str(job_id), method, str(upload_path), db)
    return {"job_id": str(job_id), "status": doc["status"]}


@router.get("/jobs")
async def list_jobs(db=Depends(get_db), current_user=Depends(require_client)):
    cursor = (
        db.jobs.find({"user_id": current_user["_id"]})
        .sort("created_at", -1)
        .limit(50)
    )
    jobs = [serialize_job(job) async for job in cursor]
    return jobs


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db=Depends(get_db), current_user=Depends(require_client)):
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")

    job = await db.jobs.find_one({"_id": obj_id, "user_id": current_user["_id"]})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return serialize_job(job)


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db=Depends(get_db), current_user=Depends(require_client)):
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")

    job = await db.jobs.find_one({"_id": obj_id, "user_id": current_user["_id"]})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    stored_path = job.get("stored_path")
    report_path = job.get("report_path")

    await db.jobs.delete_one({"_id": obj_id, "user_id": current_user["_id"]})

    for path in [stored_path, report_path]:
        if path:
            Path(path).unlink(missing_ok=True)

    return {"job_id": job_id, "deleted": True}


@router.get("/jobs/{job_id}/report")
async def download_report(
    job_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")

    job = await db.jobs.find_one({"_id": obj_id})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    is_admin = current_user.get("role") == "admin"
    if not is_admin and job.get("user_id") != current_user.get("_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    report_path = job.get("report_path")
    if not report_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not ready")

    path = Path(report_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file missing")

    filename = job.get("report_name") or path.name
    return FileResponse(path, filename=filename, media_type="application/pdf")