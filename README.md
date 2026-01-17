
# ðŸ§µ Ã‰quilibrage de Ligne de Production Textile

Ce projet met en Å“uvre un **modÃ¨le mathÃ©matique personnalisÃ©** pour Ã©quilibrer des lignes de production dans l'industrie textile. Il repose sur lâ€™analyse automatique de gammes opÃ©ratoires et une allocation optimale des tÃ¢ches dans le respect des contraintes industrielles (Takt Time, nombre d'opÃ©rateurs, etc.).

---

## ðŸ“Œ Objectifs

- Extraire et structurer les opÃ©rations issues de gammes de fabrication.
- RÃ©partir les tÃ¢ches sur plusieurs postes en optimisant l'Ã©quilibrage.
- Ã‰valuer la performance Ã  lâ€™aide dâ€™indicateurs : efficience, fluiditÃ©, Ã©quilibre des charges.
- Visualiser les affectations sous forme de diagrammes Yamazumi.

---

## ðŸ§  ModÃ¨le mathÃ©matique

Le cÅ“ur du projet est un algorithme dâ€™optimisation sur-mesure, respectant :
- Les contraintes de prÃ©cÃ©dence dÃ©finies selon une logique mÃ©tier.
- Une borne supÃ©rieure (Takt Time) par poste.
- La minimisation du dÃ©sÃ©quilibre entre postes.

Aucune heuristique classique (type SPT, RPW) n'est utilisÃ©e ici.

---

## ðŸ“Š Indicateurs ClÃ©s

- **Efficience (%)** = Temps utile / Temps allouÃ© total
- **Indice de fluiditÃ©** = Ã‰cart-type des charges poste / Takt Time
- **Nombre de postes utilisÃ©s** = Allocation en fonction du Takt Time et de la durÃ©e totale

---

## ðŸ” Exemple d'utilisation

```bash
# Lancer le notebook
jupyter notebook MTE1.ipynb
```

- Lire automatiquement les opÃ©rations depuis le fichier Excel
- Lancer l'algorithme d'Ã©quilibrage
- Visualiser les tÃ¢ches affectÃ©es Ã  chaque poste + histogramme Yamazumi

---

## ðŸ“¦ Technologies

- Python 3.x
- Pandas, NumPy
- Matplotlib
- Jupyter Notebook

---

## âœï¸ Auteurs

Projet rÃ©alisÃ© dans le cadre dâ€™un cas rÃ©el dâ€™optimisation industrielle dans lâ€™industrie de la confection textile.  
EncadrÃ© par des experts mÃ©tier et basÃ© sur des donnÃ©es issues dâ€™ateliers marocains.

## Backend (FastAPI + Mongo Atlas)

- Copy `.env.example` to `.env` and set `MONGO_URI`.
- Install deps: `pip install -r backend/requirements.txt`
- Run API: `uvicorn app.main:app --reload --app-dir backend`

## Backend Notes

- Copy `.env.example` to `.env` and set `MONGO_URI` and `JWT_SECRET`.
- Optional: set `ADMIN_EMAIL` and `ADMIN_PASSWORD` to seed an admin user at startup.
- Run API: `uvicorn app.main:app --reload --app-dir backend`
- Health check: `http://localhost:8000/api/health`

## Frontend (React)

- Go to `frontend`.
- Install deps: `npm install`
- Copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL`.
- Run dev server: `npm run dev`

## Queue and Email

- Default queue mode uses Celery + Redis. Start Redis and a worker:
  - `cd backend && celery -A app.core.celery_app:celery_app worker --loglevel=info`
- To run without Celery, set `QUEUE_MODE=local` in `.env`.
- SMTP is optional. Enable with `SMTP_ENABLED=true` and fill the SMTP settings.

## Docker Compose (Dev)

- Build and run: `docker compose up --build`
- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Ensure `.env` contains `MONGO_URI` before running Docker.
