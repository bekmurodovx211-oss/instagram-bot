import re
import uuid
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import yt_dlp
from config import DOWNLOAD_DIR

INSTAGRAM_REGEX = re.compile(
    r"(https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9_-]+/?(?:\?[^\s]*)?)",
    re.IGNORECASE
)

@dataclass
class DownloadResult:
    success: bool
    file_paths: List[Path]
    title: Optional[str] = None
    error: Optional[str] = None

def extract_instagram_url(text: str) -> Optional[str]:
    """Matn ichidan Instagram havolasini ajratib oladi."""
    if not text:
        return None
    match = INSTAGRAM_REGEX.search(text)
    if match:
        return match.group(1).split("?")[0] # Toza havola
    return None

def _download_sync(url: str) -> DownloadResult:
    """Sinxron tarzda yt-dlp orqali videoni yuklab olish."""
    file_prefix = uuid.uuid4().hex[:8]
    output_template = str(DOWNLOAD_DIR / f"{file_prefix}_%(id)s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024,  # Telegram bot limiti 50 MB
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return DownloadResult(
                    success=False,
                    file_paths=[],
                    error="Ma'lumot topilmadi yoki post mavjud emas."
                )

            downloaded_files = []
            
            # Agar bir nechta fayl yuklangan bo'lsa (masalan karusel)
            if 'requested_downloads' in info and info['requested_downloads']:
                for req in info['requested_downloads']:
                    fp = req.get('filepath')
                    if fp and Path(fp).exists():
                        downloaded_files.append(Path(fp))
            
            # Agar yuqoridagi ro'yxat bo'sh bo'lsa, standart filename tekshiramiz
            if not downloaded_files:
                expected_filename = Path(ydl.prepare_filename(info))
                if expected_filename.exists():
                    downloaded_files.append(expected_filename)
                else:
                    # downloads papkasida shu prefiksli faylni qidiramiz
                    matching = list(DOWNLOAD_DIR.glob(f"{file_prefix}_*"))
                    if matching:
                        downloaded_files.extend(matching)

            if not downloaded_files:
                return DownloadResult(
                    success=False,
                    file_paths=[],
                    error="Faylni saqlashda xatolik yuz berdi."
                )

            title = info.get('title') or info.get('description') or ""
            # Telegram sarlavha (caption) limiti - 1024 belgi
            if len(title) > 900:
                title = title[:900] + "..."

            return DownloadResult(
                success=True,
                file_paths=downloaded_files,
                title=title
            )

    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e)
        if "login" in err_msg.lower() or "private" in err_msg.lower():
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Ushbu akkaunt yopiq (private) yoki Instagram kirishni talab qilmoqda."
            )
        elif "max-filesize" in err_msg.lower():
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Video hajmi 50 MB dan katta bo'lgani sababli bot uni yubora olmaydi."
            )
        else:
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Videoni yuklab bo'lmadi. Havola to'g'riligini tekshiring."
            )
    except Exception as e:
        return DownloadResult(
            success=False,
            file_paths=[],
            error=f"Kutilmagan xatolik yuz berdi: {str(e)}"
        )

async def download_instagram_video(url: str) -> DownloadResult:
    """Asinxron oqimda videoni yuklash."""
    return await asyncio.to_thread(_download_sync, url)
