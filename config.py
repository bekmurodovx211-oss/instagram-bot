import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Admin ID lari (.env yoki Render Environment Variables orqali olinadi)
admin_raw = os.getenv("ADMIN_ID", "").strip()
ADMIN_IDS: List[int] = []
if admin_raw:
    # Vergul, probel yoki nuqta-vergul bilan ajratilgan bo'lsa ham qo'llab-quvvatlaydi
    cleaned_items = admin_raw.replace(";", ",").replace(" ", ",").split(",")
    for item in cleaned_items:
        clean_id = item.strip().strip("'\"")
        if clean_id.isdigit():
            ADMIN_IDS.append(int(clean_id))

# Agar YOUTUBE_COOKIES muhit o'zgaruvchisi berilgan bo'lsa, cookies.txt yaratamiz
youtube_cookies_env = os.getenv("YOUTUBE_COOKIES", "").strip()
if youtube_cookies_env:
    cookies_file = BASE_DIR / "cookies.txt"
    try:
        cookies_file.write_text(youtube_cookies_env, encoding="utf-8")
    except Exception:
        pass

# Yuklab olingan fayllar vaqtinchalik saqlanadigan papka
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
