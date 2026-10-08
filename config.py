import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Yuklab olingan fayllar vaqtinchalik saqlanadigan papka
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
