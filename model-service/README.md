# Model Service

Python microservice for periodic data sync and AI processing.

## Quick Start

```bash
pip install -r requirements.txt
python -m app.main
```

## Configuration

Edit `.env`:

```env
# Server
API_HOST=0.0.0.0
API_PORT=50051
REST_HOST=0.0.0.0
REST_PORT=8000
DATABASE_URL=sqlite:///./geo_int.db

# Sync Settings
SYNC_INTERVAL_HOURS=1.0
SYNC_MAX_RETRIES=3
SYNC_RETRY_BACKOFF_SECONDS=30

# External API (configure when ready)
EXTERNAL_API_URL=
EXTERNAL_API_KEY=

# AI Model (configure when ready)
AI_MODEL_TYPE=
```

## Architecture

```
app/
├── api/
│   ├── grpc_server.py     # gRPC service
│   └── rest_server.py   # REST endpoints
├── clients/
│   └── external_api.py  # External API client
├── processors/
│   └── ai_processor.py # AI processing
├── storage/
│   └── database.py    # SQLite database
├── scheduler/
│   └── sync_task.py  # Periodic sync
├── config.py
└── main.py
```

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/sync` | POST | Trigger manual sync |
| `/sync/status` | GET | Scheduler status |
| `/sync/errors` | GET | List errors |
| `/sync/record/{id}` | GET | Get record |

## gRPC

```proto
service ModelService {
  rpc ProcessRequest(Request) returns (Response);
  rpc HealthCheck(Empty) returns (HealthResponse);
}
```

## Database

SQLite with tables:
- `sync_records` - Sync data
- `sync_errors` - Failed syncs
- `sync_metadata` - Key-value store