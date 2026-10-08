import re
import uuid
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple
import yt_dlp
from config import DOWNLOAD_DIR

INSTAGRAM_REGEX = re.compile(
    r"(https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9_-]+/?(?:\?[^\s]*)?)",
    re.IGNORECASE
)

YOUTUBE_REGEX = re.compile(
    r"(https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)[A-Za-z0-9_-]+(?:\?[^\s]*)?)",
    re.IGNORECASE
)

@dataclass
class DownloadResult:
    success: bool
    file_paths: List[Path]
    title: Optional[str] = None
    original_url: Optional[str] = None
    error: Optional[str] = None

def extract_supported_url(text: str) -> Optional[Tuple[str, str]]:
    """
    Matn ichidan Instagram yoki YouTube havolasini ajratib oladi.
    Qaytaradi: (toza_url, platforma_nomi) yoki None
    """
    if not text:
        return None
    
    # Instagram tekshiruvi
    ig_match = INSTAGRAM_REGEX.search(text)
    if ig_match:
        url = ig_match.group(1).split("?")[0]
        return url, "Instagram"
        
    # YouTube tekshiruvi
    yt_match = YOUTUBE_REGEX.search(text)
    if yt_match:
        url = yt_match.group(1).split("&")[0]  # Ortiqcha parametrlarni qirqish
        return url, "YouTube"

    return None

def _download_video_sync(url: str) -> DownloadResult:
    """Sinxron tarzda video yuklab olish (Instagram yoki YouTube)."""
    file_prefix = uuid.uuid4().hex[:8]
    output_template = str(DOWNLOAD_DIR / f"{file_prefix}_%(id)s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best[filesize<50M][ext=mp4]/best[ext=mp4]/best[filesize<50M]/best',
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
            if 'requested_downloads' in info and info['requested_downloads']:
                for req in info['requested_downloads']:
                    fp = req.get('filepath')
                    if fp and Path(fp).exists():
                        downloaded_files.append(Path(fp))
            
            if not downloaded_files:
                expected_filename = Path(ydl.prepare_filename(info))
                if expected_filename.exists():
                    downloaded_files.append(expected_filename)
                else:
                    matching = list(DOWNLOAD_DIR.glob(f"{file_prefix}_*"))
                    if matching:
                        downloaded_files.extend(matching)

            if not downloaded_files:
                return DownloadResult(
                    success=False,
                    file_paths=[],
                    error="Faylni yuklab olishda xatolik yuz berdi."
                )

            title = info.get('title') or info.get('description') or ""
            if len(title) > 900:
                title = title[:900] + "..."

            return DownloadResult(
                success=True,
                file_paths=downloaded_files,
                title=title,
                original_url=url
            )

    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e)
        if "login" in err_msg.lower() or "private" in err_msg.lower():
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Ushbu akkaunt yopiq (private) yoki kirish talab qilinmoqda."
            )
        elif "max-filesize" in err_msg.lower() or "too large" in err_msg.lower():
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Video hajmi 50 MB dan katta bo'lgani sababli bot uni yubora olmaydi."
            )
        else:
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Videoni yuklab bo'lmadi. Havola to'g'riligini yoki cheklov yo'qligini tekshiring."
            )
    except Exception as e:
        return DownloadResult(
            success=False,
            file_paths=[],
            error=f"Kutilmagan xatolik: {str(e)}"
        )

def _download_audio_sync(url: str) -> DownloadResult:
    """Sinxron tarzda faqat audio/musiqani ajratib yuklab olish."""
    file_prefix = f"audio_{uuid.uuid4().hex[:8]}"
    output_template = str(DOWNLOAD_DIR / f"{file_prefix}_%(id)s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return DownloadResult(
                    success=False,
                    file_paths=[],
                    error="Audio ma'lumoti topilmadi."
                )

            downloaded_files = []
            if 'requested_downloads' in info and info['requested_downloads']:
                for req in info['requested_downloads']:
                    fp = req.get('filepath')
                    if fp and Path(fp).exists():
                        downloaded_files.append(Path(fp))

            if not downloaded_files:
                expected_filename = Path(ydl.prepare_filename(info))
                if expected_filename.exists():
                    downloaded_files.append(expected_filename)
                else:
                    matching = list(DOWNLOAD_DIR.glob(f"{file_prefix}_*"))
                    if matching:
                        downloaded_files.extend(matching)

            if not downloaded_files:
                return DownloadResult(
                    success=False,
                    file_paths=[],
                    error="Musiqani yuklab olish imkoni bo'lmadi."
                )

            title = info.get('title') or "Audio trek"
            if len(title) > 900:
                title = title[:900] + "..."

            return DownloadResult(
                success=True,
                file_paths=downloaded_files,
                title=title,
                original_url=url
            )

    except Exception as e:
        return DownloadResult(
            success=False,
            file_paths=[],
            error=f"Musiqani yuklashda xatolik: {str(e)}"
        )

async def download_media_video(url: str) -> DownloadResult:
    """Asinxron video yuklab olish."""
    return await asyncio.to_thread(_download_video_sync, url)

async def download_media_audio(url: str) -> DownloadResult:
    """Asinxron audio/musiqa yuklab olish."""
    return await asyncio.to_thread(_download_audio_sync, url)
