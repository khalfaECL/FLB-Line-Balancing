# MTE Line Balancing Studio

Professional line balancing app for textile production lines. Run MTE, SPT, and RPW methods, generate KPIs, and deliver PDF reports to clients.

## Features

- Client space: register/login, upload Excel, run balancing, download PDF, delete runs.
- Admin space: list users/jobs, retry jobs, resend reports, delete clients.
- Email verification and password reset by email.
- SMTP delivery of PDF reports.
- Max 10 runs per client (configurable).

## Tech stack

- Backend: FastAPI, Motor (MongoDB), Celery, Redis
- Frontend: React, Vite, Recharts
- Storage: MongoDB Atlas (or local MongoDB)

## Quick start (Docker)

1) Copy `.env.example` to `.env`.
2) Set at minimum:
   - `MONGO_URI`
   - `JWT_SECRET`
   - `ADMIN_EMAIL` and `ADMIN_PASSWORD`
   - `FRONTEND_BASE_URL=http://localhost:5173`
3) Optional: SMTP settings (see below).
4) Run:

```
docker compose up --build
```

URLs:
- Frontend: `http://localhost:5173`
- API health: `http://localhost:8000/api/health`

## Package (GitHub Packages / GHCR)

This repo publishes Docker images to GitHub Container Registry via GitHub Actions.

Images:
- `ghcr.io/<owner>/<repo>-api`
- `ghcr.io/<owner>/<repo>-frontend`

Triggers:
- Push to `main`
- Tag `v*`
- Manual run (Actions tab)

Notes:
- In GitHub: Settings → Actions → Workflow permissions → set **Read and write**.
- The frontend image runs Vite dev server. Provide `VITE_API_URL` at runtime.

Example (local run):
```
docker pull ghcr.io/<owner>/<repo>-api:latest

docker run --rm -p 8000:8000 --env-file .env ghcr.io/<owner>/<repo>-api:latest

# frontend (set API URL)
docker pull ghcr.io/<owner>/<repo>-frontend:latest

docker run --rm -p 5173:5173 -e VITE_API_URL=http://localhost:8000 ghcr.io/<owner>/<repo>-frontend:latest
```

## Environment variables (backend)

Required:
- `MONGO_URI`
- `JWT_SECRET`

Optional but recommended:
- `ADMIN_EMAIL`, `ADMIN_PASSWORD` (seed admin at startup)
- `FRONTEND_BASE_URL` (used in email links)
- `EMAIL_VERIFICATION_REQUIRED=true|false`
- `EMAIL_VERIFY_EXPIRES_HOURS=24`
- `PASSWORD_RESET_EXPIRES_MINUTES=60`
- `MAX_CLIENT_JOBS=10`

SMTP (optional):
- `SMTP_ENABLED=true`
- `SMTP_HOST`, `SMTP_PORT`
- `SMTP_USER`, `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_USE_TLS=true` (default) or `SMTP_USE_SSL=true`

## Frontend API URL

The frontend reads `VITE_API_URL`.

- Docker: set in `docker-compose.yml` under `frontend.environment`
- Local dev: create `frontend/.env` with:

```
VITE_API_URL=http://localhost:8000
```

Note: `VITE_API_BASE_URL` is not used.

## Email verification flow

- Register a client account.
- A verification email is sent if SMTP is enabled.
- The client must verify before logging in or running jobs.
- You can resend verification from the client login screen.

Links use:
```
FRONTEND_BASE_URL + "?verify=TOKEN"
```

If you open the link on another device, do not use `localhost`. Use your PC IP or a public domain.

## Forgot password flow

- Use "Forgot password" in the client space.
- A reset email is sent if SMTP is enabled.
- Opening the link shows the reset form.

Links use:
```
FRONTEND_BASE_URL + "?reset=TOKEN"
```

## Password policy

- At least 8 characters
- At least 1 uppercase, 1 lowercase, 1 symbol
- Max 72 bytes (bcrypt limit)

## Client storage limit

- Each client can store up to `MAX_CLIENT_JOBS` runs (default 10).
- Delete old runs to free space (client UI provides Delete).

## Development without Docker

Backend:
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

Worker (Celery):
```
cd backend
celery -A app.core.celery_app:celery_app worker --loglevel=info
```

Frontend:
```
cd frontend
npm install
npm run dev
```

## Troubleshooting

Failed to fetch (verify/reset):
- Check API: `http://localhost:8000/api/health`
- Confirm `VITE_API_URL` points to the API
- Avoid mixed http/https
- If using another device, replace `localhost` with PC IP or domain

Gmail SMTP 535:
- Enable 2FA and create an app password
- Use the app password in `SMTP_PASSWORD`

## Legacy notebooks

Research notebooks and previous scripts are kept in the repo (MTE*.ipynb, `app_replit.py`, etc.). The current app is the FastAPI + React stack described above.