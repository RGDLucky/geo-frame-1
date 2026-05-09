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

# S3 Settings
S3_BUCKET_NAME=
S3_REGION=us-east-1
S3_FILE_PREFIX=

# AI Model
AI_MODEL_TYPE=dock

# Model Settings
MODEL_PATH=../ml/checkpoints/best_model.pth
MODEL_INPUT_SIZE=260
MODEL_DEVICE=cpu

# Logging
LOG_LEVEL=INFO
```

## Architecture

```
app/
├── api/
│   ├── grpc_server.py      # gRPC service
│   ├── rest_server.py      # REST endpoints
│   └── service_pb2*.py     # Generated gRPC stubs
├── clients/
│   └── s3_client.py        # S3 client (aiobotocore)
├── model/
│   ├── dock_classifier.py  # Model definition
│   ├── model_loader.py     # Lazy-loading model singleton
│   └── preprocessing.py    # Image conversion (TIFF→PNG)
├── processors/
│   └── ai_processor.py     # AI processing logic
├── storage/
│   └── database.py         # SQLite database
├── scheduler/
│   └── sync_task.py        # Periodic sync
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
| `/sync/record/{id}` | GET | Get sync record |
| `/predictions` | GET | List recent predictions |
| `/predictions/{sync_id}` | GET | Get predictions for sync |

## gRPC

```proto
service ModelService {
  rpc ProcessRequest(Request) returns (Response);
  rpc HealthCheck(Empty) returns (HealthResponse);
  rpc ProcessImage(ImageProcessRequest) returns (ImageProcessResponse);
  rpc ClassifyDock(DockClassifyRequest) returns (DockClassifyResponse);
}
```

## Database

SQLite with tables:
- `sync_records` - Sync data
- `sync_errors` - Failed syncs
- `sync_metadata` - Key-value store
- `ai_predictions` - AI model predictions

## Logging

Set via environment variable:
```bash
LOG_LEVEL=DEBUG python -m app.main
```

Levels: DEBUG, INFO, WARNING, ERROR

## Dependencies

- **FastAPI** - REST API framework
- **uvicorn** - ASGI server
- **grpcio** - gRPC server
- **APScheduler** - Periodic task scheduling
- **boto3** - AWS SDK
- **aiobotocore** - Async S3 operations
- **aiosqlite** - Async SQLite
- **torch** - PyTorch (inference)
- **torchvision** - Model weights, transforms
- **Pillow** - Image processing
