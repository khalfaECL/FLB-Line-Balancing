from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, health, jobs
from app.core.config import get_settings
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.services.seed import ensure_admin_user

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    await connect_to_mongo()
    settings.ensure_directories()
    await ensure_admin_user()


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_mongo_connection()


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
