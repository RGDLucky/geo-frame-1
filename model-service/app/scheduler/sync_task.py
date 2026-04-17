import asyncio
import uuid
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.clients import get_s3_client
from app.processors.ai_processor import get_ai_processor
from app.storage.database import database


class SyncScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.s3_client = get_s3_client()
        self.ai_processor = get_ai_processor()
        self._last_sync_status = "never_run"
        self._last_sync_time = None

    async def sync_once(self) -> dict:
        sync_id = str(uuid.uuid4())
        max_retries = settings.sync_max_retries
        backoff = settings.sync_retry_backoff_seconds

        for attempt in range(max_retries + 1):
            try:
                raw_data = await self.s3_client.fetch()
                await database.store_raw(sync_id, raw_data)

                processed_data = await self.ai_processor.process(raw_data)
                await database.update_processed(sync_id, processed_data)

                await database.set_metadata(
                    "last_sync_id", sync_id
                )
                await database.set_metadata(
                    "last_sync_time", datetime.utcnow().isoformat()
                )

                self._last_sync_status = "success"
                self._last_sync_time = datetime.utcnow()
                return {"sync_id": sync_id, "status": "success", "attempts": attempt + 1}

            except Exception as e:
                retry_count = await database.increment_retry(sync_id)
                if retry_count > max_retries:
                    await database.mark_failed(sync_id, str(e))
                    self._last_sync_status = "failed"
                    self._last_sync_time = datetime.utcnow()
                    return {
                        "sync_id": sync_id,
                        "status": "failed",
                        "error": str(e),
                        "attempts": retry_count,
                    }
                await asyncio.sleep(backoff)

        return {"sync_id": sync_id, "status": "failed", "error": "max_retries_exceeded"}

    async def run_sync_job(self):
        result = await self.sync_once()
        print(f"Sync completed: {result}")

    def start(self):
        self.scheduler.add_job(
            self.run_sync_job,
            "interval",
            hours=settings.sync_interval_hours,
            id="periodic_sync",
            replace_existing=True,
        )
        self.scheduler.start()
        print(f"Scheduler started (interval: {settings.sync_interval_hours}h)")

    def stop(self):
        self.scheduler.shutdown()

    def get_status(self) -> dict:
        return {
            "last_sync_status": self._last_sync_status,
            "last_sync_time": self._last_sync_time.isoformat()
            if self._last_sync_time
            else None,
            "next_sync_time": (
                self.scheduler.get_job("periodic_sync").next_run_time.isoformat()
                if self.scheduler.get_job("periodic_sync")
                else None
            ),
        }

    async def trigger_manual_sync(self) -> dict:
        return await self.sync_once()


sync_scheduler = SyncScheduler()