import uuid
from pathlib import Path
from typing import Optional, Tuple, List
import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "bot.db"

async def init_db() -> None:
    """Ma'lumotlar bazasini initsializatsiya qilish va jadvallarni yaratish."""
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

async def add_or_update_user(user_id: int, username: Optional[str], full_name: str) -> None:
    """Foydalanuvchini bazaga qo'shish yoki ma'lumotlarini yangilash."""
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
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET downloads_count = downloads_count + 1
            WHERE user_id = ?
        """, (user_id,))
        await db.commit()

async def get_stats() -> dict:
    """Admin uchun umumiy statistika."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute("SELECT COALESCE(SUM(downloads_count), 0) FROM users") as cursor:
            total_downloads = (await cursor.fetchone())[0]

        async with db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE date(joined_at) = date('now')
        """) as cursor:
            new_users_today = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "total_downloads": total_downloads,
            "new_users_today": new_users_today
        }

async def get_all_user_ids() -> List[int]:
    """Xabar tarqatish (broadcast) uchun bloklanmagan barcha foydalanuvchilar IDlari."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def save_media_cache(url: str, title: Optional[str] = None) -> str:
    """Inline tugma (callback_data 64 bayt limiti) uchun qisqa ID saqlash."""
    short_id = uuid.uuid4().hex[:12]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO media_cache (short_id, url, title)
            VALUES (?, ?, ?)
        """, (short_id, url, title))
        await db.commit()
    return short_id

async def get_media_cache(short_id: str) -> Optional[Tuple[str, Optional[str]]]:
    """Qisqa ID bo'yicha media havolasi va sarlavhasini olish."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT url, title FROM media_cache WHERE short_id = ?
        """, (short_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0], row[1]
    return None
