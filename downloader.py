import re
import uuid
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple
import yt_dlp
from config import DOWNLOAD_DIR, BASE_DIR

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
    """Matn ichidan Instagram yoki YouTube havolasini ajratib oladi."""
    if not text:
        return None
    
    ig_match = INSTAGRAM_REGEX.search(text)
    if ig_match:
        url = ig_match.group(1).split("?")[0]
        return url, "Instagram"
        
    yt_match = YOUTUBE_REGEX.search(text)
    if yt_match:
        url = yt_match.group(1).split("&")[0]
        return url, "YouTube"

    return None

def _get_base_ydl_opts(output_template: str, is_audio: bool = False) -> dict:
    """yt-dlp sozlamalari (YouTube bot himoyasini aylanib o'tish bilan)."""
    opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024,
        # YouTube bot va cloud IP blokirovkasini aylanib o'tish (Android & iOS mijozlari orqali)
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }

    if is_audio:
        opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best'
    else:
        opts['format'] = 'best[filesize<50M][ext=mp4]/best[ext=mp4]/best[filesize<50M]/best'

    # Agar cookies.txt mavjud bo'lsa, undan foydalanamiz
    cookies_path = BASE_DIR / "cookies.txt"
    if cookies_path.exists():
        opts['cookiefile'] = str(cookies_path)

    return opts

def _download_video_sync(url: str) -> DownloadResult:
    """Sinxron tarzda video yuklab olish."""
    file_prefix = uuid.uuid4().hex[:8]
    output_template = str(DOWNLOAD_DIR / f"{file_prefix}_%(id)s.%(ext)s")
    ydl_opts = _get_base_ydl_opts(output_template, is_audio=False)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return DownloadResult(
                    success=False,
                    file_paths=[],
                    error="Ma'lumot topilmadi yoki video mavjud emas."
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
                    error="Faylni saqlashda xatolik yuz berdi."
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
        err_msg = str(e).lower()
        if "sign in" in err_msg or "confirm you're not a bot" in err_msg:
            return DownloadResult(
                success=False,
                file_paths=[],
                error="YouTube ushbu videoga kirish uchun tasdiqlashni talab qildi (yosh chegarasi yoki avtorizatsiya talabi)."
            )
        elif "login" in err_msg or "private" in err_msg:
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Ushbu akkaunt yopiq (private) yoki video maxfiy."
            )
        elif "max-filesize" in err_msg or "too large" in err_msg:
            return DownloadResult(
                success=False,
                file_paths=[],
                error="Video hajmi 50 MB dan katta bo'lgani sababli Telegram orqali yuborib bo'lmaydi."
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
            error=f"Kutilmagan xatolik: {str(e)}"
        )

def _download_audio_sync(url: str) -> DownloadResult:
    """Sinxron tarzda audio/musiqa yuklab olish."""
    file_prefix = f"audio_{uuid.uuid4().hex[:8]}"
    output_template = str(DOWNLOAD_DIR / f"{file_prefix}_%(id)s.%(ext)s")
    ydl_opts = _get_base_ydl_opts(output_template, is_audio=True)

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
    """Asinxron audio yuklab olish."""
    return await asyncio.to_thread(_download_audio_sync, url)
