import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_PATH = Path(__file__).resolve().parent / "bot.db"

# Agar PostgreSQL (Neon.tech) bo'lsa
is_postgres = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")
pg_pool = None

async def init_db() -> None:
    """Ma'lumotlar bazasini initsializatsiya qilish (Neon PostgreSQL yoki SQLite)."""
    global pg_pool, is_postgres

    if is_postgres:
        import asyncpg
        dsn = DATABASE_URL
        if dsn.startswith("postgres://"):
            dsn = "postgresql://" + dsn[len("postgres://"):]

        try:
            pg_pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
            logger.info("Neon PostgreSQL bulutli bazasiga muvaffaqiyatli ulandi!")
            
            async with pg_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        full_name TEXT,
                        joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        downloads_count INTEGER DEFAULT 0,
                        is_banned INTEGER DEFAULT 0
                    );
                    CREATE TABLE IF NOT EXISTS media_cache (
                        short_id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        title TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            return
        except Exception as e:
            logger.error(f"Neon PostgreSQL ga ulanishda xatolik: {e}. SQLite ga o'tilmoqda...")
            is_postgres = False

    # Agar DATABASE_URL bo'lmasa yoki xato bersa -> Mahalliy SQLite
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                downloads_count INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS media_cache (
                short_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("Mahalliy SQLite bazasi (bot.db) faollashtirildi.")

async def add_or_update_user(user_id: int, username: Optional[str], full_name: str) -> None:
    """Foydalanuvchini bazaga qo'shish yoki ma'lumotlarini yangilash."""
    global pg_pool, is_postgres
    if is_postgres and pg_pool:
        async with pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, full_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name
            """, user_id, username, full_name)
    else:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
            """, (user_id, username, full_name))
            await db.commit()

async def increment_downloads(user_id: int) -> None:
    """Foydalanuvchining yuklab olishlar sonini bittaga oshirish."""
    global pg_pool, is_postgres
    if is_postgres and pg_pool:
        async with pg_pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET downloads_count = downloads_count + 1
                WHERE user_id = $1
            """, user_id)
    else:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE users SET downloads_count = downloads_count + 1
                WHERE user_id = ?
            """, (user_id,))
            await db.commit()

async def get_stats() -> dict:
    """Admin uchun umumiy statistika."""
    global pg_pool, is_postgres
    if is_postgres and pg_pool:
        async with pg_pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            total_downloads = await conn.fetchval("SELECT COALESCE(SUM(downloads_count), 0) FROM users")
            new_users_today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = CURRENT_DATE")
            return {
                "total_users": total_users,
                "total_downloads": total_downloads,
                "new_users_today": new_users_today,
                "db_type": "Neon PostgreSQL ☁️"
            }
    else:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_users = (await cursor.fetchone())[0]

            async with db.execute("SELECT COALESCE(SUM(downloads_count), 0) FROM users") as cursor:
                total_downloads = (await cursor.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM users WHERE date(joined_at) = date('now')") as cursor:
                new_users_today = (await cursor.fetchone())[0]

            return {
                "total_users": total_users,
                "total_downloads": total_downloads,
                "new_users_today": new_users_today,
                "db_type": "SQLite (Fayl) 📁"
            }

async def get_all_user_ids() -> List[int]:
    """Xabar tarqatish uchun foydalanuvchilar IDlari."""
    global pg_pool, is_postgres
    if is_postgres and pg_pool:
        async with pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users WHERE is_banned = 0")
            return [row["user_id"] for row in rows]
    else:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

async def save_media_cache(url: str, title: Optional[str] = None) -> str:
    """Inline tugma uchun qisqa ID saqlash."""
    short_id = uuid.uuid4().hex[:12]
    global pg_pool, is_postgres
    if is_postgres and pg_pool:
        async with pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO media_cache (short_id, url, title)
                VALUES ($1, $2, $3)
            """, short_id, url, title)
    else:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO media_cache (short_id, url, title)
                VALUES (?, ?, ?)
            """, (short_id, url, title))
            await db.commit()
    return short_id

async def get_media_cache(short_id: str) -> Optional[Tuple[str, Optional[str]]]:
    """Qisqa ID bo'yicha media havolasini olish."""
    global pg_pool, is_postgres
    if is_postgres and pg_pool:
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT url, title FROM media_cache WHERE short_id = $1
            """, short_id)
            if row:
                return row["url"], row["title"]
    else:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("""
                SELECT url, title FROM media_cache WHERE short_id = ?
            """, (short_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0], row[1]
    return None
