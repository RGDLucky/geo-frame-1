# geo-frame-1

React/Tailwind + Python AI application (2-service architecture)

## Architecture

```
┌─────────────┐     gRPC      ┌──────────────┐     PostgreSQL
│ api-service │ ──────────────│ model-service│ ─────────────▶
│  (Node/TS)  │               │   (Python)   │
└─────────────┘               └──────────────┘
       │
       │ static files (served combined)
       ▼
┌─────────────┐
│  frontend   │
│ (React/TS)  │
└─────────────┘
```

- **api-service** (Node/TS): Serves frontend + handles HTTP requests
- **model-service** (Python): AI model inference + database operations
- **postgres**: External database

## Running the App

### Quick Start (run.sh)

```bash
./run.sh
```

This starts all 3 services in one command.

### Option 1: Docker (recommended for production-like)

```bash
# Start all services
docker-compose up --build

# Stop all services
docker-compose down
```

### Option 2: Manual (recommended for development)

**Terminal 1 - Model service (gRPC)**
```bash
cd model-service
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m app.main
```

**Terminal 2 - API service**
```bash
cd api-service
npm install
npm run dev
```

**Terminal 3 - Frontend dev server (optional, for hot reload)**
```bash
cd frontend
npm install
npm run dev
```

### Option 3: API serves built frontend

```bash
# Build frontend
cd frontend && npm run build

# Start services (frontend served statically by api-service)
cd model-service && python -m app.main &
cd api-service && npm run dev
```

## Access

| Service | URL |
|---------|-----|
| Frontend + API | http://localhost:8000 |
| API endpoints | http://localhost:8000/api/* |
| Health check | http://localhost:8000/health |
| Model service (gRPC) | localhost:50051 |
| PostgreSQL | localhost:5432 |

## Stopping the App

### Docker
```bash
docker-compose down
```

### Manual
Press `Ctrl+C` in each terminal, or:
```bash
lsof -i :3000,8000,50051 -t | xargs kill
```

## Project Structure

```
geo-frame-1/
├── frontend/              # React + Tailwind
├── api-service/         # Node/TS - HTTP server
│   └── src/
│       ├── main.ts      # Entry point
│       ├── config.ts   # Configuration
│       └── routes/     # API routes
├── model-service/        # Python - AI model + gRPC
│   └── app/
│       ├── api/         # gRPC server
│       ├── processors/   # Data processing
│       ├── model/       # Model inference
│       ├── clients/     # External APIs
│       └── storage/     # Database operations
├── proto/               # Shared gRPC contracts
├── docker-compose.yml   # Service orchestration
└── .env               # Environment variables
```