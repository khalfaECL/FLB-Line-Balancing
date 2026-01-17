import asyncio

from app.core.config import get_settings
from app.services.job_runner import process_job


def enqueue_job(job_id: str, method: str, stored_path: str, db) -> None:
    settings = get_settings()
    mode = settings.queue_mode.lower()
    if mode == "celery":
        from app.services.tasks import run_job_task

        run_job_task.delay(job_id, method, stored_path)
        return

    asyncio.create_task(process_job(job_id, method, stored_path, db))
