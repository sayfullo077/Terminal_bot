import re

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from aiogram.filters import Command
from filters.admin_bot import IsBotOrAssistantAdmin

from loader import dp, bot
from data.config import ADMINS
from database.orm_query import select_all_users, get_admin_users, delete_all_transactions, orm_delete_by_id
from keyboards.inline.buttons import back_button


def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


class UserMessageState(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()


user_message_map = {}


@dp.message(Command("deletetransactions"))
async def delete_all_transfers(message: Message, session: AsyncSession):
    await delete_all_transactions(session)
    await message.answer("Barcha transferlar o'chirildi !")


@dp.message(Command("feedback"))
async def ask_for_feedback(message: Message, state: FSMContext):
    back_btn = await back_button()
    await message.answer("📭 Fikringizni qoldiring. Sizning fikringiz biz uchun muhim.", reply_markup=back_btn)
    await state.set_state(UserMessageState.waiting_for_message)


@dp.message(Command("exit"))
async def exit_bot(message: Message, session: AsyncSession):
    telegram_id = message.from_user.id
    await orm_delete_by_id(session, telegram_id)
    await message.answer("Tizimdan chiqdingiz")


@dp.message(UserMessageState.waiting_for_message)
async def forward_to_admins(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    full_name = html_escape(message.from_user.full_name)
    username = message.from_user.username
    telegram_id = message.from_user.id
    registration_date = datetime.now().strftime("%Y-%m-%d")
    is_premium = message.from_user.is_premium if message.from_user.is_premium else 'Unknown'
    user_text = html_escape(message.text)
    db_admins = await select_all_users(session)

    assistant_admins = await get_admin_users(session)
    admin_ids = [admin.id for admin in assistant_admins] + ADMINS
    try:
        if admin_ids:
            for admin_id in admin_ids:
                callback_data = f"reply_{user_id}"
                user_message_map[callback_data] = user_id
                await bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"👤 User : {full_name}\n"
                        f"🔑 Username : {f'@{username}' if username else 'None'}\n"
                        f"🆔 Telegram : {telegram_id}\n"
                        f"📆 Data : {registration_date}\n"
                        f"💎 Premium : {is_premium}\n"
                        f"📨 Message : {user_text}"
                    ),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🔰 Profil", url=f"tg://user?id={telegram_id}"),
                            InlineKeyboardButton(text="📤 Javob berish", callback_data=callback_data)
                        ]
                    ])
                )
        else:
            print("DB Adminlar ro'yxati bo'sh !")

    except Exception as e:
        print(f"❗️ Xatolik adminlar olishda :\nError : {e}")
    await message.delete()
    await message.answer("📬 Xabaringiz adminga yetkazildi, tez orada javob keladi kuting !")
    await state.clear()


@dp.callback_query(F.data.startswith("reply_"))
async def ask_reply_message(callback: CallbackQuery, state: FSMContext):
    user_id = user_message_map.get(callback.data)
    if user_id:
        await callback.message.answer("✉️ Javob xabarini kiriting:")
        await state.update_data(user_id=user_id)
        await state.set_state(UserMessageState.waiting_for_admin_reply)
    else:
        await callback.answer("❗️ Xato: User ID noto'g'ri formatda!")


@dp.message(UserMessageState.waiting_for_admin_reply)
async def send_reply_to_user(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_id = state_data.get("user_id")
    try:
        if user_id:
            await message.delete()
            await bot.send_message(user_id, f"<b>📥 Admin javobi</b>:\n{message.text}")
            await message.answer("✅ Foydalanuvchiga javob yuborildi!")
    except Exception as e:
        print(f"❗️ User 🆔 not found. Error : {e}")
    await state.clear()
