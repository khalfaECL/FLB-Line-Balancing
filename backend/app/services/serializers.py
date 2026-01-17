from typing import Any, Dict


def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(user.get("_id")),
        "email": user.get("email"),
        "role": user.get("role", "client"),
        "email_verified": user.get("email_verified", False),
    }


def serialize_job(
    job: Dict[str, Any],
    include_user_id: bool = False,
    include_paths: bool = False,
) -> Dict[str, Any]:
    data = {
        "job_id": str(job.get("_id")),
        "filename": job.get("filename"),
        "method": job.get("method"),
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "completed_at": job.get("completed_at"),
        "result": job.get("result"),
        "error": job.get("error"),
        "report_name": job.get("report_name"),
        "email_status": job.get("email_status"),
        "email_error": job.get("email_error"),
        "email_sent_at": job.get("email_sent_at"),
    }

    if include_user_id:
        data["user_id"] = str(job.get("user_id"))
    if include_paths:
        data["stored_path"] = job.get("stored_path")
        data["report_path"] = job.get("report_path")

    return data