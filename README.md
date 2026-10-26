# Personalised Travel Itinerary Planner

A beginner-friendly starter with three parts:

- **Frontend** (`frontend/`): a React website built with Vite
- **Backend** (`backend/`): a FastAPI (Python) server
- **Database** (`database/schema.sql`): table layout for Supabase later. We have **not** connected Supabase yet.
- **`supabase/`**: leftover placeholder folder from the first starter. Kept so nothing was deleted.

## What you need installed

Install these once on your computer:

1. **Node.js LTS** (includes `npm`) from [https://nodejs.org](https://nodejs.org)
2. **Python 3.11 or newer** from [https://www.python.org/downloads](https://www.python.org/downloads)

During the Python installer, tick **Add python.exe to PATH**.

Open a **new** terminal after installing so the commands below work.

## Folder guide

| Folder | What it is |
| --- | --- |
| `frontend/` | The pages the user sees |
| `backend/` | The API that will later plan trips |
| `database/schema.sql` | Starter tables for trips and itinerary items |
| `supabase/` | Older placeholder folder. Kept in place |

## Run the backend (FastAPI)

Open a terminal in the project folder, then:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks the virtual environment, run this once, then try `Activate.ps1` again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

When it works, open:

- API home: [http://localhost:8000](http://localhost:8000)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Leave this terminal open.

## Run the frontend (React)

Open a **second** terminal in the project folder, then:

```powershell
cd frontend
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

Click **Check backend connection**. If the backend is running, you should see a success message.

## Next step (not done yet)

Connecting **Supabase** (database + login) will be a separate step.
