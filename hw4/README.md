# Campus Customs — Homework 4 (AI for Managers)

A Fortnite-style "Item Shop" storefront for Campus Customs (Yale Bulldog Blue). It has a React + Vite + TypeScript frontend, a FastAPI backend, and a PydanticAI shop agent (`gpt-5.6-luna` via Portkey) that reads live price and stock from `data/campus_customs.db`.

## Where things are

- `AI_prompt.md` — log of every prompt typed into the vibe coder, by problem
- `backend/` — `main.py` (API), `agent.py`, `tools.py`, `models.py`, `prompts/AI_prompt.md`, plus `auth.py`, `db.py`, `safety.py` and `audit.py`
- `frontend/` — React site
- `output/harness.md` — how the system works: database, auth, tools, models, safety, specs, how to run
- `output/usability.md` — the four Problem 9 improvements
- `output/design.md` — the Problem 10 design
- `output/app_check.html` — live-app screenshots (open it in a browser)
- `output/audit_trail.json` — append-only log of agent runs

## Run

The database, product photos and real `.env` aren't in this repo. Put `campus_customs.db` and `products/` into `data/` (see `data/README.md`), then:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # add your PORTKEY_API_KEY
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000
# in a second terminal
cd frontend && npm install && npm run dev
```

Then open http://localhost:5173. The seed test login is `test@campuscustoms.yale.edu` with the password `password`.
