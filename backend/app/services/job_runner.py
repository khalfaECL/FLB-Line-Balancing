import asyncio
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from bson import ObjectId
import matplotlib.pyplot as plt

from app.core.config import get_settings
from app.services.emailer import is_email_enabled, send_report_email
from app.services.balance import run_all_methods, run_balance
from app.services.report import generate_report_pdf

import mte4

logger = logging.getLogger(__name__)


def _normalize_workstations(workstations: List[List[tuple]]) -> List[List[Dict[str, Any]]]:
    normalized = []
    for station in workstations:
        tasks = [
            {"task": task, "duration": float(duration)}
            for task, duration in station
        ]
        normalized.append(tasks)
    return normalized


def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    kpis = {}
    for key, value in (result.get("kpis") or {}).items():
        try:
            kpis[key] = float(value)
        except (TypeError, ValueError):
            kpis[key] = value

    return {
        "workstations": _normalize_workstations(result.get("ws", [])),
        "workstation_times": [float(val) for val in result.get("wst", [])],
        "kpis": kpis,
    }


def _plot_all_methods(file_path: str, methods: List[str], output_dir: Path) -> Any:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".txt",
        dir=str(output_dir),
        mode="w",
        encoding="utf-8",
    ) as tmp:
        tmp.write("\n".join(methods))
        methods_path = tmp.name

    try:
        fig = mte4.plot_all_methods_by_file(file_path, methods_txt_path=methods_path)
    finally:
        Path(methods_path).unlink(missing_ok=True)

    return fig


def _run_job_sync(method: str, file_path: str, output_dir: str, job_id: str) -> Dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = output_path / f"report_{job_id}.pdf"

    if method == "ALL":
        methods = ["MTE", "SPT", "RPW"]
        results = run_all_methods(file_path)
        fig = _plot_all_methods(file_path, methods, output_path)
        assignments = {
            name: (result["ws"], result["wst"])
            for name, result in results.items()
        }
    else:
        result = run_balance(file_path, method)
        results = {method: result}
        fig = result.get("fig")
        assignments = {method: (result["ws"], result["wst"])}

    if fig is None:
        raise RuntimeError("Failed to generate figure for report")

    generate_report_pdf(fig, assignments, str(report_path))
    plt.close(fig)

    payload = {
        "methods": {name: _normalize_result(result) for name, result in results.items()},
        "report_path": str(report_path),
        "report_name": report_path.name,
    }
    return payload


async def process_job(job_id: str, method: str, stored_path: str, db) -> None:
    settings = get_settings()
    obj_id = ObjectId(job_id)

    job_doc = await db.jobs.find_one({"_id": obj_id})
    if not job_doc:
        logger.error("Job not found: %s", job_id)
        return

    now = datetime.now(timezone.utc)
    await db.jobs.update_one(
        {"_id": obj_id},
        {"$set": {"status": "processing", "updated_at": now}},
    )

    try:
        payload = await asyncio.to_thread(
            _run_job_sync,
            method,
            stored_path,
            settings.output_dir,
            job_id,
        )
        now = datetime.now(timezone.utc)
        await db.jobs.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "status": "completed",
                    "result": payload["methods"],
                    "report_path": payload["report_path"],
                    "report_name": payload["report_name"],
                    "updated_at": now,
                    "completed_at": now,
                }
            },
        )

        email_status = "skipped"
        email_error = None
        email_sent_at = None

        if is_email_enabled() and job_doc.get("user_id"):
            user = await db.users.find_one({"_id": job_doc["user_id"]})
            if user and user.get("email"):
                try:
                    await asyncio.to_thread(
                        send_report_email,
                        user["email"],
                        payload["report_path"],
                        job_id,
                    )
                    email_status = "sent"
                    email_sent_at = datetime.now(timezone.utc)
                except Exception as exc:
                    email_status = "failed"
                    email_error = str(exc)

        await db.jobs.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "email_status": email_status,
                    "email_error": email_error,
                    "email_sent_at": email_sent_at,
                }
            },
        )
    except Exception as exc:
        now = datetime.now(timezone.utc)
        await db.jobs.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(exc),
                    "updated_at": now,
                }
            },
        )
        logger.exception("Job processing failed: %s", job_id)
