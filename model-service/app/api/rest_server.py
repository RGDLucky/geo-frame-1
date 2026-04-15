from fastapi import FastAPI
from pydantic import BaseModel
from app.config import settings
from app.scheduler.sync_task import sync_scheduler
from app.storage.database import database


app = FastAPI(title=settings.app_name)


class SyncResponse(BaseModel):
    sync_id: str
    status: str
    attempts: int = 1
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    last_sync_status: str | None
    last_sync_time: str | None


@app.get("/health", response_model=HealthResponse)
async def health():
    status = "healthy"
    sync_status = sync_scheduler.get_status()
    return HealthResponse(
        status=status,
        last_sync_status=sync_status.get("last_sync_status"),
        last_sync_time=sync_status.get("last_sync_time"),
    )


@app.post("/sync", response_model=SyncResponse)
async def trigger_sync():
    result = await sync_scheduler.trigger_manual_sync()
    return SyncResponse(**result)


@app.get("/sync/status")
async def get_sync_status():
    return sync_scheduler.get_status()


@app.get("/sync/errors")
async def get_sync_errors():
    errors = await database.get_errors()
    return {"errors": errors}


@app.get("/sync/record/{sync_id}")
async def get_sync_record(sync_id: str):
    record = await database.get_record(sync_id)
    if not record:
        return {"error": "record not found"}, 404
    return record


def serve():
    import uvicorn
    uvicorn.run(app, host=settings.rest_host, port=settings.rest_port)