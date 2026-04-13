# geo-frame-1

React/Tailwind + Python (FastAPI) AI application

## Running the App

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:3000`

## Verify

- Backend health: `http://localhost:8000/health`
- Backend API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`