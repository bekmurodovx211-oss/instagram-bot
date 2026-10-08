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
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from config import BOT_TOKEN
from database import (
    init_db, add_or_update_user, increment_downloads,
    save_media_cache, get_media_cache
)
from downloader import (
    extract_supported_url, download_media_video, download_media_audio
)
from admin import admin_router

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

dp = Dispatcher()
# Admin routerni ulash
dp.include_router(admin_router)

# --- UptimeRobot va Render uchun Web Server ---
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

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"UptimeRobot & Render HTTP serveri {port}-portda ishga tushirildi.")

# --- Asosiy Komandalar ---
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """/start komandasi uchun handler."""
    if message.from_user:
        await add_or_update_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )

    user_name = message.from_user.full_name if message.from_user else "Foydalanuvchi"
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user_name}!</b>\n\n"
        "Men <b>Instagram</b> va <b>YouTube</b>dan video va audio yuklab beruvchi qulay botman.\n\n"
        "📥 <b>Menga quyidagilarning havolasini (linkini) yuboring:</b>\n"
        "• Instagram Reels va Post videolari\n"
        "• YouTube Shorts va Videolari\n\n"
        "🎵 <i>Har bir video ostida musiqasini alohida yuklab olish tugmasi ham mavjud!</i>"
    )
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """/help komandasi uchun handler."""
    help_text = (
        "📖 <b>Botdan qanday foydalanish mumkin?</b>\n\n"
        "1. Instagram yoki YouTubedan istalgan video havolasini nusxalang (Copy link).\n"
        "2. Havolani ushbu botga yuboring.\n"
        "3. Bot videoni yuklab beradi.\n"
        "4. Agar faqat musiqasi kerak bo'lsa, video ostidagi <b>«🎵 Musiqasini yuklash»</b> tugmasini bosing!\n\n"
        "⚠️ <i>Telegram orqali 50 MB gacha bo'lgan fayllar qo'llab-quvvatlanadi.</i>"
    )
    await message.answer(help_text)

# --- Video Yuklash Handleri ---
@dp.message(F.text)
async def handle_media_message(message: Message, bot: Bot) -> None:
    """Instagram yoki YouTube havolalarini tahlil qilish va videoni yuborish."""
    if message.from_user:
        await add_or_update_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )

    text = message.text or ""
    detected = extract_supported_url(text)

    # Agar qo'llab-quvvatlanadigan havola topilmasa
    if not detected:
        await message.answer(
            "⚠️ <b>Iltimos, to'g'ri Instagram yoki YouTube havolasini yuboring.</b>\n\n"
            "<i>Masalan:</i>\n"
            "• <code>https://www.instagram.com/reel/...</code>\n"
            "• <code>https://youtube.com/shorts/...</code>\n"
            "• <code>https://youtu.be/...</code>"
        )
        return

    url, platform = detected
    status_msg = await message.answer(f"⏳ <i>{platform} videosi yuklanmoqda, iltimos kuting...</i>")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)

    result = await download_media_video(url)

    if not result.success:
        error_text = result.error or "Videoni yuklab olishda xatolik yuz berdi."
        await status_msg.edit_text(f"❌ {error_text}")
        return

    try:
        # Musiqa yuklash tugmasi uchun havola keshga saqlanadi
        short_id = await save_media_cache(url, result.title)
        audio_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎵 Musiqasini yuklash (MP3)", callback_data=f"audio:{short_id}")]
        ])

        bot_info = await bot.get_me()
        bot_tag = f"@{bot_info.username or 'saver'}"

        for file_path in result.file_paths:
            if not file_path.exists():
                continue

            caption = (
                f"🎬 {result.title}\n\n"
                f"📥 {bot_tag}"
            ) if result.title else f"📥 {bot_tag}"

            if file_path.suffix.lower() in [".mp4", ".mov", ".m4v", ".webm"]:
                video_file = FSInputFile(str(file_path))
                await message.answer_video(
                    video=video_file,
                    caption=caption,
                    reply_markup=audio_markup
                )
            elif file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                photo_file = FSInputFile(str(file_path))
                await message.answer_photo(
                    photo=photo_file,
                    caption=caption,
                    reply_markup=audio_markup
                )
            else:
                doc_file = FSInputFile(str(file_path))
                await message.answer_document(
                    document=doc_file,
                    caption=caption,
                    reply_markup=audio_markup
                )

        if message.from_user:
            await increment_downloads(message.from_user.id)

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Fayl yuborishda xatolik: {e}")
        await status_msg.edit_text(f"❌ Videoni yuborishda xatolik: {e}")
    finally:
        for file_path in result.file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Faylni o'chirishda xatolik: {e}")

# --- Musiqani Yuklash Callback Handleri ---
@dp.callback_query(F.data.startswith("audio:"))
async def handle_audio_download(callback: CallbackQuery, bot: Bot) -> None:
    """Video ostidagi 'Musiqasini yuklash' tugmasi bosilganda ishlaydi."""
    short_id = callback.data.split(":", 1)[1]
    cached = await get_media_cache(short_id)

    if not cached:
        await callback.answer("❌ Havola eskirgan yoki topilmadi.", show_alert=True)
        return

    url, title = cached
    await callback.answer("🎵 Musiqa yuklanmoqda...")
    status_msg = await callback.message.reply("⏳ <i>Musiqa ajratib olinmoqda, iltimos kuting...</i>")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.RECORD_VOICE)

    result = await download_media_audio(url)

    if not result.success:
        error_text = result.error or "Musiqani yuklab bo'lmadi."
        await status_msg.edit_text(f"❌ {error_text}")
        return

    try:
        bot_info = await bot.get_me()
        bot_tag = f"@{bot_info.username or 'saver'}"

        for file_path in result.file_paths:
            if not file_path.exists():
                continue

            audio_file = FSInputFile(str(file_path))
            audio_caption = f"🎵 {result.title or title or 'Audio'}\n\n📥 {bot_tag}"

            await callback.message.answer_audio(
                audio=audio_file,
                caption=audio_caption,
                title=result.title or title or "Audio Trek"
            )

        if callback.from_user:
            await increment_downloads(callback.from_user.id)

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Audio yuborishda xatolik: {e}")
        await status_msg.edit_text(f"❌ Audio yuborishda xatolik: {e}")
    finally:
        for file_path in result.file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Audio faylni o'chirishda xatolik: {e}")

# --- Asosiy Funksiya ---
async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN aniqlanmadi! .env faylini tekshiring.")
        sys.exit(1)

    # 1. Ma'lumotlar bazasini initsializatsiya qilish
    await init_db()
    logger.info("Ma'lumotlar bazasi (SQLite) muvaffaqiyatli ulandi.")

    # 2. Render & UptimeRobot HTTP serverini ishga tushirish
    await start_web_server()

    # 3. Telegram botni ishga tushirish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    logger.info("Bot muvaffaqiyatli ishga tushdi! Yangi xabarlar kutilmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
