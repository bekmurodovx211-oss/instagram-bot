import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Admin ID lari (.env faylida: ADMIN_ID=12345678,87654321 ko'rinishida bo'lishi mumkin)
admin_raw = os.getenv("ADMIN_ID", "").strip()
ADMIN_IDS: List[int] = []
if admin_raw:
    for item in admin_raw.split(","):
        cleaned = item.strip()
        if cleaned.isdigit():
            ADMIN_IDS.append(int(cleaned))

# Yuklab olingan fayllar vaqtinchalik saqlanadigan papka
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
