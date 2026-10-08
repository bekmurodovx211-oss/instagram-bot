import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import get_stats, get_all_user_ids

logger = logging.getLogger(__name__)
admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    confirm_broadcast = State()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin bosh panel tugmalari."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
            InlineKeyboardButton(text="📢 Xabar tarqatish", callback_data="admin:broadcast")
        ],
        [
            InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:menu")
        ]
    ])

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish."""
    return user_id in ADMIN_IDS

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Admin panelini ochish."""
    if not is_admin(message.from_user.id):
        # Admin bo'lmasa javob bermaymiz
        return

    await state.clear()
    await message.answer(
        "🛠 <b>Boshqaruv Paneli (Admin Panel)</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_keyboard()
    )

@admin_router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Bosh menyuga qaytish."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Boshqaruv Paneli (Admin Panel)</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    """Statistikani ko'rsatish."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    stats = await get_stats()
    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"📥 <b>Jami yuklab olishlar:</b> {stats['total_downloads']} marta\n"
        f"🆕 <b>Bugun qo'shilganlar:</b> {stats['new_users_today']} ta"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin:menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@admin_router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Xabar tarqatishni boshlash."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_broadcast)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:menu")]
    ])
    await callback.message.edit_text(
        "📢 <b>Foydalanuvchilarga xabar yuborish</b>\n\n"
        "Barcha a'zolarga jo'natmoqchi bo'lgan xabaringizni yuboring.\n"
        "<i>(Matn, rasm, video, audio yoki havola yuborishingiz mumkin)</i>",
        reply_markup=keyboard
    )
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    """Xabarni qabul qilish va tasdiqlashni so'rash."""
    if not is_admin(message.from_user.id):
        return

    # Xabar ID sini saqlaymiz
    await state.update_data(broadcast_message_id=message.message_id)
    await state.set_state(AdminStates.confirm_broadcast)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, hammaga yuborilsin", callback_data="admin:confirm_send"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:menu")
        ]
    ])
    await message.reply(
        "❓ Ushbu xabar barcha foydalanuvchilarga tarqatilsinmi?",
        reply_markup=keyboard
    )

@admin_router.callback_query(F.data == "admin:confirm_send", AdminStates.confirm_broadcast)
async def cb_confirm_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Barcha foydalanuvchilarga xabarni nusxalab jo'natish."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    data = await state.get_data()
    msg_id = data.get("broadcast_message_id")
    await state.clear()

    if not msg_id:
        await callback.message.edit_text("❌ Xabar topilmadi.", reply_markup=get_admin_keyboard())
        return

    user_ids = await get_all_user_ids()
    total = len(user_ids)

    status_msg = await callback.message.edit_text(
        f"⏳ Xabar tarqatilmoqda...\nJami: {total} ta foydalanuvchi."
    )

    success_count = 0
    fail_count = 0

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=callback.message.chat.id,
                message_id=msg_id
            )
            success_count += 1
            # Telegram chekloviga tushmaslik uchun kichik tanaffus
            await asyncio.sleep(0.04)
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        "✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"👥 <b>Jami a'zolar:</b> {total} ta\n"
        f"📥 <b>Yetkazildi:</b> {success_count} ta\n"
        f"🚫 <b>Yetib bormadi (bloklagan):</b> {fail_count} ta",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()
