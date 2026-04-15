import asyncio
from app.config import settings
from app.api.grpc_server import serve as serve_grpc
from app.api.rest_server import serve as serve_rest
from app.scheduler.sync_task import sync_scheduler
from app.storage.database import database


async def main():
    await database.init_db()
    print(f"Database initialized at {settings.database_url}")

    sync_scheduler.start()

    await asyncio.gather(
        asyncio.to_thread(serve_grpc),
        asyncio.to_thread(serve_rest),
    )


if __name__ == "__main__":
    asyncio.run(main())