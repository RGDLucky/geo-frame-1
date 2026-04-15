import aiosqlite
from datetime import datetime
from typing import Any
from app.config import settings


class Database:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.database_url
        self.db_path = self.db_url.replace("sqlite:///", "")

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sync_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_id TEXT NOT NULL UNIQUE,
                    raw_data TEXT NOT NULL,
                    processed_data TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sync_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_id TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.commit()

    async def store_raw(self, sync_id: str, data: dict[str, Any]) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.utcnow().isoformat()
            await db.execute(
                """
                INSERT OR REPLACE INTO sync_records 
                (sync_id, raw_data, status, created_at, updated_at)
                VALUES (?, ?, 'pending', ?, ?)
                """,
                (sync_id, str(data), now, now),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT id FROM sync_records WHERE sync_id = ?", (sync_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def update_processed(
        self, sync_id: str, processed_data: dict[str, Any]
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.utcnow().isoformat()
            await db.execute(
                """
                UPDATE sync_records 
                SET processed_data = ?, status = 'completed', updated_at = ?
                WHERE sync_id = ?
                """,
                (str(processed_data), now, sync_id),
            )
            await db.commit()

    async def increment_retry(self, sync_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT retry_count FROM sync_records WHERE sync_id = ?", (sync_id,)
            )
            row = await cursor.fetchone()
            current_count = row[0] if row else 0
            new_count = current_count + 1
            now = datetime.utcnow().isoformat()
            await db.execute(
                """
                UPDATE sync_records 
                SET retry_count = ?, updated_at = ?
                WHERE sync_id = ?
                """,
                (new_count, now, sync_id),
            )
            await db.commit()
            return new_count

    async def mark_failed(self, sync_id: str, error_message: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "UPDATE sync_records SET status = 'failed', updated_at = ? WHERE sync_id = ?",
                (now, sync_id),
            )
            await db.execute(
                """
                INSERT INTO sync_errors (sync_id, error_message, retry_count, created_at)
                SELECT sync_id, ?, retry_count, ? FROM sync_records WHERE sync_id = ?
                """,
                (error_message, now, sync_id),
            )
            await db.commit()

    async def get_pending_records(self) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT sync_id, raw_data FROM sync_records WHERE status = 'pending'"
            )
            rows = await cursor.fetchall()
            return [{"sync_id": r[0], "raw_data": eval(r[1])} for r in rows]

    async def get_record(self, sync_id: str) -> dict[str, Any] | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM sync_records WHERE sync_id = ?", (sync_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "sync_id": row[1],
                "raw_data": eval(row[2]),
                "processed_data": eval(row[3]) if row[3] else None,
                "status": row[4],
                "retry_count": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }

    async def get_errors(self) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM sync_errors ORDER BY created_at DESC LIMIT 100"
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "sync_id": r[1],
                    "error_message": r[2],
                    "retry_count": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]

    async def set_metadata(self, key: str, value: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "INSERT OR REPLACE INTO sync_metadata (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, now),
            )
            await db.commit()

    async def get_metadata(self, key: str) -> str | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT value FROM sync_metadata WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None


database = Database()