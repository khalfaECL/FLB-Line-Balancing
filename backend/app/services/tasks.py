import asyncio

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.db.mongo import create_mongo_client
from app.services.job_runner import process_job


@celery_app.task(name="mte.process_job")
def run_job_task(job_id: str, method: str, stored_path: str) -> None:
    settings = get_settings()
    client = create_mongo_client()
    db = client[settings.mongo_db_name]

    try:
        asyncio.run(process_job(job_id, method, stored_path, db))
    finally:
        client.close()
