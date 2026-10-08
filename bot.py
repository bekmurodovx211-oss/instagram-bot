import os
import sys
import logging
import asyncio
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile

from config import BOT_TOKEN
from downloader import extract_instagram_url, download_instagram_video

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# --- UptimeRobot va Render uchun Web Server (Port 8080/10000) ---
async def handle_ping(request: web.Request) -> web.Response:
    """UptimeRobot ping yuborganda 200 OK qaytaradi."""
    return web.Response(text="Bot is running! Status: OK 🚀", status=200)

async def start_web_server() -> None:
    """Render va UptimeRobot boti uxlab qolmasligi uchun HTTP server."""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()

    # Render PORT muhit o'zgaruvchisini beradi (odatda 10000)
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"UptimeRobot & Render HTTP serveri {port}-portda ishga tushirildi.")

# --- Telegram Bot Handlerlari ---
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """/start komandasi uchun handler."""
    user_name = message.from_user.full_name if message.from_user else "Foydalanuvchi"
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user_name}!</b>\n\n"
        "Men Instagramdan video va Reels yuklab beruvchi botman.\n\n"
        "📲 Menga Instagramdagi video yoki Reels havolasini (linkini) yuboring, "
        "men uni sizga yuklab beraman!\n\n"
        "<i>Misol uchun:</i>\n"
        "<code>https://www.instagram.com/reel/...</code>"
    )
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """/help komandasi uchun handler."""
    help_text = (
        "📖 <b>Botdan qanday foydalanish mumkin?</b>\n\n"
        "1. Instagram ilovasida videoni oching va <b>Ulashish (Share) -> Havolani nusxalash (Copy link)</b> tugmasini bosing.\n"
        "2. Nusxalangan havolani ushbu botga yuboring.\n"
        "3. Bot videoni bir necha soniya ichida yuklab beradi!\n\n"
        "⚠️ <b>Eslatma:</b>\n"
        "• Faqat ochiq (public) profillardagi videolarni yuklash mumkin.\n"
        "• Hajmi 50 MB gacha bo'lgan videolar qo'llab-quvvatlanadi."
    )
    await message.answer(help_text)

@dp.message(F.text)
async def handle_instagram_message(message: Message, bot: Bot) -> None:
    """Foydalanuvchi xabarlarini tahlil qilish va videoni yuklash."""
    text = message.text or ""
    instagram_url = extract_instagram_url(text)

    # Agar xabarda Instagram havolasi bo'lmasa
    if not instagram_url:
        await message.answer(
            "⚠️ <b>Iltimos, to'g'ri Instagram havolasini yuboring.</b>\n\n"
            "Masalan: <code>https://www.instagram.com/reel/...</code>"
        )
        return

    # Jarayon boshlanganini bildirish
    status_msg = await message.answer("⏳ <i>Video yuklanmoqda, iltimos kuting...</i>")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)

    result = await download_instagram_video(instagram_url)

    if not result.success:
        error_text = result.error or "Videoni yuklab olishda noma'lum xatolik yuz berdi."
        await status_msg.edit_text(f"❌ {error_text}")
        return

    # Yuklab olingan fayllarni foydalanuvchiga yuborish
    try:
        for file_path in result.file_paths:
            if not file_path.exists():
                continue

            caption = (
                f"🎬 {result.title}\n\n"
                f"📥 @{(await bot.get_me()).username or 'InstagramDownloaderBot'}"
            ) if result.title else f"📥 @{(await bot.get_me()).username or 'InstagramDownloaderBot'}"

            # Agar fayl video bo'lsa
            if file_path.suffix.lower() in [".mp4", ".mov", ".m4v", ".webm"]:
                video_file = FSInputFile(str(file_path))
                await message.answer_video(video=video_file, caption=caption)
            elif file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                photo_file = FSInputFile(str(file_path))
                await message.answer_photo(photo=photo_file, caption=caption)
            else:
                doc_file = FSInputFile(str(file_path))
                await message.answer_document(document=doc_file, caption=caption)

        # Holat xabarini o'chirish
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Fayl yuborishda xatolik: {e}")
        await status_msg.edit_text(f"❌ Videoni yuborishda xatolik yuz berdi: {e}")
    finally:
        # Disk to'lib qolmasligi uchun yuklangan fayllarni o'chirish
        for file_path in result.file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Faylni o'chirishda xatolik {file_path}: {e}")

async def main() -> None:
    """Asosiy ishga tushirish funksiyasi."""
    if not BOT_TOKEN:
        logger.error(
            "\n" + "="*60 +
            "\n❌ DIQQAT: BOT_TOKEN aniqlanmadi!\n"
            "Iltimos, .env faylini oching va @BotFather orqali olingan tokenni kiriting:\n"
            "BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ\n" +
            "="*60 + "\n"
        )
        sys.exit(1)

    # 1. Render va UptimeRobot uchun veb serverni ishga tushiramiz
    await start_web_server()

    # 2. Telegram botni ishga tushiramiz
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    logger.info("Bot muvaffaqiyatli ishga tushirildi! Yangi xabarlar kutilmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
